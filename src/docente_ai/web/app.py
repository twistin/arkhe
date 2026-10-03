"""Servidor ASGI local: recursos propios, token por proceso y tareas secuenciales."""

from contextlib import asynccontextmanager
import json
import hashlib
from pathlib import Path
import secrets
import sqlite3

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from docente_ai.generation.render import render, render_sources, render_student
from docente_ai.generation.service import get_run
from docente_ai.library.service import show_document, authorize_document, update_document, original_file
from docente_ai.web.workspace import Workspace, SUFFIXES, MAX_BYTES

STATIC = Path(__file__).parent / 'static'


import ipaddress


class LocalOnly(BaseHTTPMiddleware):
    def __init__(self, app, *, token, port, allowed_hosts=None):
        super().__init__(app)
        self.token, self.port = token, port
        self.allowed_hosts = set(allowed_hosts or [])

    async def dispatch(self, request, call_next):
        host = request.headers.get('host', '')
        host_name = host.split(':')[0]
        allowed = {f'127.0.0.1:{self.port}', f'localhost:{self.port}', '127.0.0.1', 'localhost'}
        allowed.update(self.allowed_hosts)

        is_allowed_host = host in allowed or host_name in allowed
        if not is_allowed_host and self.allowed_hosts:
            if host_name.endswith('.ts.net') or host_name.endswith('.tailscale.net'):
                is_allowed_host = True
            else:
                try:
                    ip = ipaddress.ip_address(host_name)
                    if ip in ipaddress.ip_network('100.64.0.0/10') or ip.is_private or ip.is_loopback:
                        is_allowed_host = True
                except ValueError:
                    pass

        if not is_allowed_host and '0.0.0.0' not in self.allowed_hosts:
            return JSONResponse({'error': 'Acceso local no válido.'}, status_code=403)

        origin = request.headers.get('origin')
        if origin:
            if origin not in {f'http://{host}', f'https://{host}', f'http://{host_name}', f'https://{host_name}'}:
                return JSONResponse({'error': 'Origen no permitido.'}, status_code=403)

        if request.url.path.startswith('/api/') and not secrets.compare_digest(request.headers.get('x-docente-token', ''), self.token):
            return JSONResponse({'error': 'La sesión ha caducado. Recarga la página.'}, status_code=403)
        response = await call_next(request)
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        return response


async def body(request):
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 200_000:
            raise ValueError('Solicitud demasiado grande.')
        chunks.append(chunk)
    try:
        data = json.loads(b''.join(chunks))
    except (ValueError, UnicodeError):
        raise ValueError('Solicitud JSON inválida.') from None
    if not isinstance(data, dict):
        raise ValueError('Solicitud inválida.')
    return data


def create_app(root, *, port=8765, workspace=None, allowed_hosts=None):
    token = secrets.token_urlsafe(32)
    ws = workspace or Workspace(root)

    @asynccontextmanager
    async def lifespan(app):
        yield
        await run_in_threadpool(ws.close)

    async def index(request):
        try:
            mtime = int(max((STATIC / 'style.css').stat().st_mtime, (STATIC / 'app.js').stat().st_mtime))
        except Exception:
            mtime = 1
        html = (STATIC / 'index.html').read_text().replace('__TOKEN__', token).replace('__VERSION__', str(mtime))
        return HTMLResponse(html, headers={'X-Enjambre-Workspace': hashlib.sha256(str(ws.root).encode()).hexdigest()})

    async def state(request):
        return JSONResponse(await run_in_threadpool(ws.state))

    async def status(request):
        return JSONResponse(await run_in_threadpool(ws.model_status))

    async def inbox(request):
        return JSONResponse(await run_in_threadpool(ws.scan))

    async def jobs(request):
        return JSONResponse(ws.job_list())

    async def upload(request):
        name = request.query_params.get('name', '')
        if not name or Path(name).name != name or '\\' in name or any(ord(c) < 32 for c in name) or Path(name).suffix.lower() not in SUFFIXES:
            raise ValueError('Elige un PDF, DOCX, TXT o Markdown con un nombre válido.')
        # Leave room for duplicate suffixes and respect the filesystem byte limit.
        if len(name.encode('utf-8')) > 230:
            suffix = Path(name).suffix
            stem = Path(name).stem.encode('utf-8')[:210].decode('utf-8', errors='ignore')
            name = stem + '-' + hashlib.sha256(name.encode('utf-8')).hexdigest()[:8] + suffix
        target = ws.knowledge / '00 Entrada' / name
        count = 1
        while target.exists():
            target = target.with_name(f'{Path(name).stem} ({count}){Path(name).suffix}')
            count += 1
        temporary = target.with_name('.upload-' + secrets.token_hex(12))
        size = 0
        try:
            with temporary.open('xb') as stream:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ValueError('El archivo supera los 100 MiB.')
                    stream.write(chunk)
            if not size:
                raise ValueError('El archivo está vacío.')
            # Hard-link gives no-overwrite semantics even for concurrent uploads.
            target.hardlink_to(temporary)
        finally:
            temporary.unlink(missing_ok=True)
        return JSONResponse({'path': str(target.relative_to(ws.knowledge)), 'name': target.name})

    async def importing(request):
        data = await body(request)
        ws.source_path(data.get('path'))
        return JSONResponse(ws.submit('Incorporando documento', lambda: ws.add_source(data)), status_code=202)

    async def document(request):
        data = await run_in_threadpool(show_document, ws.db, request.path_params['id'], text=True)
        if request.query_params.get('download') == '1':
            version = next(v for v in data['versions'] if v['id'] == data['selected_version_id'])
            is_ocr = request.query_params.get('derived') == '1'
            if version['derived_from_version_id'] and not is_ocr:
                version = next(v for v in data['versions'] if v['id'] == version['derived_from_version_id'])
            path = original_file(ws.db, version['original_path'])
            with path.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != version['sha256']:
                    raise ValueError('El original ha cambiado; no se puede entregar como una copia íntegra.')
            filename = Path(version['source_path']).name
            if is_ocr and version['derived_from_version_id']:
                filename = Path(filename).stem + '-texto-ocr.pdf'
            return FileResponse(path, filename=filename)
        data['preview_truncated'] = len(data['segments']) > 30
        data['segments'] = data['segments'][:30]
        for segment in data['segments']:
            if len(segment['text']) > 16000:
                segment['text'] = segment['text'][:16000] + '\n[Vista previa abreviada]'
                data['preview_truncated'] = True
        return JSONResponse(data)

    async def authorize(request):
        data = await body(request)
        identifier = request.path_params['id']
        accepted = data.get('accept_warnings', False)
        if type(accepted) is not bool:
            raise ValueError('Confirmación de avisos inválida.')
        await run_in_threadpool(authorize_document, ws.db, identifier, enabled=True, accept_warnings=accepted)
        return JSONResponse(ws.submit('Preparando fuente para el asistente', lambda: ws.prepare_source(identifier), key='prepare:'+identifier), status_code=202)

    async def exclude(request):
        return JSONResponse(await run_in_threadpool(authorize_document, ws.db, request.path_params['id'], enabled=False))

    async def delete_doc(request):
        return JSONResponse(await run_in_threadpool(ws.delete_source, request.path_params['id']))

    async def metadata(request):
        data = await body(request)
        subject = data.get('subject')
        if not isinstance(subject, str) or not subject:
            raise ValueError('Elige una materia.')
        values = {'title': data.get('title'), 'authors': data.get('authors', [])}
        values['year'] = data.get('year')
        return JSONResponse(await run_in_threadpool(update_document, ws.db, request.path_params['id'], values=values, subjects=[subject]))

    async def generation(request):
        data = await body(request)
        await run_in_threadpool(ws.require_provider_consent, data.get('mode'))
        return JSONResponse(ws.submit('Preparando propuesta' if data.get('mode') == 'pedagogy' else 'Consultando tus fuentes', lambda: ws.generate(data)), status_code=202)

    async def run(request):
        result = await run_in_threadpool(get_run, ws.db, request.path_params['id'])
        if request.query_params.get('student') == '1':
            return Response(render_student(result), media_type='text/markdown')
        if request.query_params.get('sources') == '1':
            return Response(render_sources(result), media_type='text/markdown', headers={
                'Content-Disposition': f'attachment; filename="anexo-fuentes-{result["id"]}.md"'})
        if request.query_params.get('download') == '1':
            return Response(render(result), media_type='text/markdown', headers={'Content-Disposition': f'attachment; filename="{result["id"]}.md"'})
        return JSONResponse({k: result[k] for k in ('id', 'status', 'created_at', 'request', 'result', 'evidence', 'warnings', 'error', 'review')})

    async def delete_run_route(request):
        return JSONResponse(await run_in_threadpool(ws.delete_run, request.path_params['id']))

    async def review(request):
        data = await body(request)
        action = data.get('action')
        if action not in ('approved', 'rejected'):
            raise ValueError("La acción debe ser 'approved' o 'rejected'.")
        return JSONResponse(await run_in_threadpool(ws.review_run, request.path_params['id'], data))

    async def edit(request):
        data = await body(request)
        return JSONResponse(await run_in_threadpool(ws.edit_run, request.path_params['id'], data))

    async def record_create(request):
        data = await body(request)
        return JSONResponse(await run_in_threadpool(ws.add_record, data))

    async def record_get(request):
        return JSONResponse(await run_in_threadpool(ws.get_record, request.path_params['id']))

    async def record_progress(request):
        data = await body(request)
        return JSONResponse(await run_in_threadpool(ws.add_progress, request.path_params['id'], data))

    async def record_feedback(request):
        data = await body(request)
        return JSONResponse(await run_in_threadpool(ws.add_feedback, request.path_params['id'], data))

    async def record_reveal(request):
        return JSONResponse(await run_in_threadpool(ws.reveal_record, request.path_params['id']))

    async def group_records(request):
        group_id = request.path_params['id']
        limit = int(request.query_params.get('limit', 10))
        return JSONResponse(await run_in_threadpool(ws.list_records, group_id, limit))

    async def subject(request):
        return JSONResponse(await run_in_threadpool(ws.save_subject, await body(request)))

    async def group(request):
        return JSONResponse(await run_in_threadpool(ws.save_group, await body(request)))

    async def models(request):
        return JSONResponse(await run_in_threadpool(ws.save_models, await body(request)))

    async def stats(request):
        from docente_ai.generation.service import run_stats
        return JSONResponse(await run_in_threadpool(run_stats, ws.db, int(request.query_params.get('limit', '100'))))

    async def delete_api_key(request):
        return JSONResponse(await run_in_threadpool(ws.delete_api_key))

    async def confirm_provider(request):
        return JSONResponse(await run_in_threadpool(ws.confirm_provider, await body(request)))

    async def reveal(request):
        return JSONResponse(await run_in_threadpool(ws.reveal))

    async def reveal_diary(request):
        return JSONResponse(await run_in_threadpool(ws.reveal_diary))

    async def export_calendar(request):
        group_id = request.query_params.get('group_id')
        reminder = int(request.query_params.get('reminder', 15))
        content = await run_in_threadpool(ws.calendar_ics, group_id=group_id, reminder_minutes=reminder)
        return Response(content, media_type='text/calendar', headers={'Content-Disposition': 'attachment; filename="horario-docente.ics"'})

    async def shutdown(request):
        if any(j['status'] in ('queued', 'running') for j in ws.job_list()):
            raise ValueError('Espera a que terminen las tareas antes de cerrar Enjambre.')
        callback = getattr(request.app.state, 'shutdown', None)
        if callback is None:
            raise ValueError('Este servidor se cierra desde su lanzador.')
        callback()
        return JSONResponse({'ok': True})

    async def error(request, exc):
        return JSONResponse({'error': str(exc)}, status_code=400)

    routes = [Route('/', index), Route('/api/state', state), Route('/api/status', status), Route('/api/inbox', inbox),
              Route('/api/jobs', jobs), Route('/api/upload', upload, methods=['POST']),
              Route('/api/import', importing, methods=['POST']), Route('/api/documents/{id}', document),
              Route('/api/documents/{id}/authorize', authorize, methods=['POST']),
              Route('/api/documents/{id}/exclude', exclude, methods=['POST']),
              Route('/api/documents/{id}/delete', delete_doc, methods=['POST']),
              Route('/api/documents/{id}/metadata', metadata, methods=['POST']),
              Route('/api/generate', generation, methods=['POST']), Route('/api/runs/{id}', run),
              Route('/api/runs/{id}/delete', delete_run_route, methods=['POST']),
              Route('/api/runs/{id}/review', review, methods=['POST']),
              Route('/api/runs/{id}/edit', edit, methods=['POST']),
              Route('/api/records', record_create, methods=['POST']),
              Route('/api/records/{id}', record_get),
              Route('/api/records/{id}/progress', record_progress, methods=['POST']),
              Route('/api/records/{id}/feedback', record_feedback, methods=['POST']),
              Route('/api/records/{id}/reveal', record_reveal, methods=['POST']),
              Route('/api/groups/{id}/records', group_records),
              Route('/api/calendar.ics', export_calendar),
              Route('/api/subjects', subject, methods=['POST']), Route('/api/groups', group, methods=['POST']),
              Route('/api/shutdown', shutdown, methods=['POST']), Route('/api/models', models, methods=['POST']), Route('/api/reveal', reveal, methods=['POST']), Route('/api/reveal-diary', reveal_diary, methods=['POST']), Mount('/assets', StaticFiles(directory=STATIC), name='assets')]

    routes.insert(0, Route('/api/secrets/deepseek', delete_api_key, methods=['DELETE']))
    routes.insert(0, Route('/api/secrets/provider', delete_api_key, methods=['DELETE']))
    routes.insert(0, Route('/api/provider/confirm', confirm_provider, methods=['POST']))
    routes.insert(0, Route('/api/runs/stats', stats))
    app = Starlette(routes=routes, lifespan=lifespan, exception_handlers={ValueError: error, OSError: error, sqlite3.Error: error})
    app.add_middleware(LocalOnly, token=token, port=port, allowed_hosts=allowed_hosts)
    app.state.workspace = ws
    return app
