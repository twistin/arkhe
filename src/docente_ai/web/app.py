"""Servidor ASGI local: recursos propios, token por proceso y tareas secuenciales."""

from contextlib import asynccontextmanager
import asyncio
import json
import hashlib
from pathlib import Path
import secrets
import sqlite3

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
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
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
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


def create_app(root, *, port=8765, workspace=None, allowed_hosts=None, server=None):
    token = secrets.token_urlsafe(32)
    ws = workspace or Workspace(root)

    @asynccontextmanager
    async def lifespan(app):
        await run_in_threadpool(ws.cleanup_stale_runs)
        yield
        await run_in_threadpool(ws.close)

    async def index(request):
        try:
            mtime = int(max((STATIC / 'style.css').stat().st_mtime, (STATIC / 'js' / 'main.js').stat().st_mtime))
        except Exception:
            mtime = 1
        html = (STATIC / 'index.html').read_text().replace('__TOKEN__', token).replace('__VERSION__', str(mtime))
        workspace_id = hashlib.sha256(str(ws.root).encode()).hexdigest()
        if server:
            html = html.replace('</header>', '<button data-action="logout" class="button">Cerrar sesión</button></header>')
        return HTMLResponse(html, headers={
            'X-Arkhe-Workspace': workspace_id,
            'X-Enjambre-Workspace': workspace_id,  # Compatibilidad con lanzadores anteriores.
        })

    def visible(data):
        if server:
            from docente_ai.web.server import public_data
            return public_data(data)
        return data

    async def state(request):
        data = await run_in_threadpool(ws.state)
        if server: data['server_mode'] = True
        return JSONResponse(visible(data))

    async def status(request):
        return JSONResponse(await run_in_threadpool(ws.model_status))

    async def inbox(request):
        return JSONResponse(await run_in_threadpool(ws.scan))

    async def jobs(request):
        return JSONResponse(ws.job_list())

    async def job_events(request):
        identifier = request.path_params['id']
        try:
            cursor = int(request.headers.get('last-event-id', request.query_params.get('after', '0')))
            if cursor < 0: raise ValueError
        except ValueError:
            return JSONResponse({'error': 'Cursor de eventos inválido.'}, status_code=400)
        if ws.job_events(identifier, cursor) is None:
            return JSONResponse({'error': 'Tarea inexistente.'}, status_code=404)
        async def stream():
            nonlocal cursor
            ticks = 0
            while not await request.is_disconnected():
                events = ws.job_events(identifier, cursor)
                if events is None: return
                for item in events:
                    cursor = item['id']
                    data = json.dumps(item['data'], ensure_ascii=False)
                    yield f"id: {cursor}\nevent: {item['event']}\ndata: {data}\n\n"
                    if item['event'] == 'terminal' or (item['event'] == 'snapshot' and
                            item['data']['status'] in ('done', 'failed', 'cancelled')):
                        return
                ticks += 1
                if ticks % 40 == 0: yield ': latido\n\n'
                await asyncio.sleep(0.25)
        return StreamingResponse(stream(), media_type='text/event-stream', headers={
            'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no',
        })

    async def cancel_job(request):
        await body(request)
        result = await run_in_threadpool(ws.cancel_job, request.path_params['id'])
        return JSONResponse(result or {'error': 'Tarea inexistente.'}, status_code=202 if result else 404)

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
        return JSONResponse(visible(data))

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
        subjects = [subject] if (isinstance(subject, str) and subject) else None
        values = {}
        if 'title' in data and data['title']:
            values['title'] = data['title']
        if 'authors' in data:
            values['authors'] = data['authors']
        if 'year' in data:
            values['year'] = data['year']
        if 'origin' in data and data['origin']:
            values['origin'] = data['origin']
        return JSONResponse(await run_in_threadpool(update_document, ws.db, request.path_params['id'], values=values, subjects=subjects))

    async def generation(request):
        data = await body(request)
        await run_in_threadpool(ws.require_provider_consent, data.get('mode'))
        return JSONResponse(ws.submit('Preparando propuesta' if data.get('mode') == 'pedagogy' else 'Consultando tus fuentes', lambda: ws.generate(data), cancellable=True), status_code=202)

    async def run(request):
        result = await run_in_threadpool(get_run, ws.db, request.path_params['id'])
        display_title = result.get('display_title') or (result.get('request') or {}).get('display_title') or (result.get('request') or {}).get('question', 'propuesta')
        from docente_ai.web.workspace import slug
        title_slug = slug(display_title)
        if request.query_params.get('student') == '1':
            filename = f"material-alumnado-{title_slug}.md" if title_slug else f"material-alumnado-{result['id']}.md"
            return Response(render_student(result), media_type='text/markdown', headers={
                'Content-Disposition': f'attachment; filename="{filename}"'})
        if request.query_params.get('sources') == '1':
            filename = f"anexo-fuentes-{title_slug}.md" if title_slug else f"anexo-fuentes-{result['id']}.md"
            return Response(render_sources(result), media_type='text/markdown', headers={
                'Content-Disposition': f'attachment; filename="{filename}"'})
        if request.query_params.get('download') == '1':
            filename = f"propuesta-{title_slug}.md" if title_slug else f"{result['id']}.md"
            return Response(render(result), media_type='text/markdown', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
        ficha_data = result.get('ficha')
        if not ficha_data:
            from docente_ai.teaching.fichas import get_ficha_for_run
            ficha_data = get_ficha_for_run(result)
        out = {k: result.get(k) for k in ('id', 'status', 'created_at', 'request', 'result', 'evidence', 'warnings', 'error', 'review', 'display_title', 'original_topic')}
        out['ficha'] = ficha_data
        out['ficha_ejemplos'] = result.get('ficha_ejemplos') or []
        return JSONResponse(out)

    async def descargar_ejemplos_ficha_route(request):
        run_id = request.path_params.get('id')
        res = await run_in_threadpool(ws.descargar_ejemplos_ficha, run_id)
        return JSONResponse(res)

    async def ficha_get(request):
        from docente_ai.teaching.fichas import get_ficha
        f_id = request.path_params['id']
        f = await run_in_threadpool(get_ficha, f_id)
        if not f:
            return JSONResponse({'error': f'Ficha no encontrada: {f_id}'}, status_code=404)
        return JSONResponse(f)

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

    async def set_title(request):
        data = await body(request)
        return JSONResponse(await run_in_threadpool(ws.update_run_title, request.path_params['id'], data.get('title')))

    async def set_subject(request):
        data = await body(request)
        return JSONResponse(await run_in_threadpool(ws.update_run_subject, request.path_params['id'], data.get('subject')))


    async def adopt_score(request):
        data = await body(request)
        run_id = request.path_params['id']
        req_id = request.path_params['req_id']
        return JSONResponse(await run_in_threadpool(ws.adopt_score_candidate, run_id, req_id, data))

    async def discard_score(request):
        data = await body(request)
        run_id = request.path_params['id']
        req_id = request.path_params['req_id']
        return JSONResponse(await run_in_threadpool(ws.discard_score_candidate, run_id, req_id, data))

    async def search_repos(request):
        data = await body(request) if request.headers.get('content-length') else {}
        run_id = request.path_params['id']
        req_id = request.path_params['req_id']
        return JSONResponse(await run_in_threadpool(ws.search_open_score_repos, run_id, req_id, data))

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

    async def record_download(request):
        import io
        import zipfile
        record = await run_in_threadpool(ws.get_record, request.path_params['id'])
        folder = ws._record_folder(record)
        if not folder.resolve().is_relative_to(ws.knowledge.resolve()):
            raise ValueError('Carpeta de sesión inválida.')
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(folder.rglob('*')):
                if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(folder.resolve()):
                    archive.write(path, str(path.relative_to(folder)))
        return Response(output.getvalue(), media_type='application/zip', headers={
            'Content-Disposition': 'attachment; filename="sesion.zip"'})

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
        data = await body(request)
        if server:
            if data.get('api_key') or data.get('delete_api_key') or data.get('provider', 'mistral') != 'mistral':
                raise ValueError('Piloto: solo Mistral UE; la clave se administra por entorno en el servidor.')
            if data.get('embeddings', 'bge-m3') not in ('', 'bge-m3'):
                raise ValueError('El piloto utiliza únicamente embeddings bge-m3.')
        return JSONResponse(await run_in_threadpool(ws.save_models, data))

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

    async def exportar_eventos(request):
        from docente_ai.teaching.eventos_centro import cargar_eventos, calendario_eventos
        eventos = await run_in_threadpool(cargar_eventos, ws.root)
        contenido = calendario_eventos(eventos, solo_prioritarios=request.query_params.get('prioritarios') == '1')
        return Response(contenido, media_type='text/calendar', headers={
            'Content-Disposition': 'attachment; filename="audiciones-centro.ics"',
        })

    async def listar_ejemplos(request):
        from docente_ai.teaching.ejemplos import load_all_ejemplos
        return JSONResponse(await run_in_threadpool(load_all_ejemplos))

    async def obtener_ejemplo(request):
        from docente_ai.teaching.ejemplos import get_ejemplo, get_ejemplo_musicxml
        id_ej = request.path_params['id']
        ej = await run_in_threadpool(get_ejemplo, id_ej, directory=ws.root / 'data/ejemplos')
        if not ej:
            ej = await run_in_threadpool(get_ejemplo, id_ej, directory=ws.root / 'config/ejemplos')
        if not ej:
            ej = await run_in_threadpool(get_ejemplo, id_ej)
        if not ej:
            raise ValueError(f'Ejemplo musical {id_ej} no encontrado.')
        if request.query_params.get('musicxml') == '1':
            if ej.get("exportable") is False or ej.get("licencia") == "licencia no especificada: uso docente con atribución":
                raise ValueError("Esta partitura tiene licencia no especificada y no puede exportarse fuera del material de clase.")
            xml_content = await run_in_threadpool(get_ejemplo_musicxml, id_ej, directory=ws.root / 'data/ejemplos')
            if not xml_content:
                xml_content = await run_in_threadpool(get_ejemplo_musicxml, id_ej, directory=ws.root / 'config/ejemplos')
            if not xml_content:
                xml_content = await run_in_threadpool(get_ejemplo_musicxml, id_ej)
            if not xml_content:
                raise ValueError(f'Contenido MusicXML no disponible para {id_ej}.')
            return Response(xml_content, media_type='application/vnd.recordare.musicxml+xml', headers={
                'Content-Disposition': f'attachment; filename="{ej.get("archivo", id_ej + ".musicxml")}"'
            })
        return JSONResponse(ej)

    async def exportar_ejemplo_wav(request):
        id_ej = request.path_params['id']
        wav_bytes = await run_in_threadpool(ws.export_score_wav, id_ej)
        return Response(wav_bytes, media_type='audio/wav', headers={
            'Content-Disposition': f'attachment; filename="{id_ej}.wav"'
        })

    async def music_capabilities_route(request):
        return JSONResponse(await run_in_threadpool(ws.music_capabilities))

    async def render_score_pianoroll(request):
        data = await body(request)
        if 'path' in data:
            raise ValueError('No se admiten rutas del cliente. Proporciona el identificador del candidato o ejemplo.')
        score_id = data.get('id') or data.get('candidate_id') or data.get('ejemplo_id')
        if not score_id:
            raise ValueError('Se requiere el identificador del candidato o ejemplo del catálogo.')
        run_id = data.get('run_id')
        start = int(data.get('start', 1))
        end = int(data.get('end', 8))
        voice = data.get('voice') or data.get('highlight_voice')
        try:
            resolved_file = await run_in_threadpool(ws.resolve_score_path, score_id, run_id)
        except FileNotFoundError as exc:
            return JSONResponse({'error': str(exc)}, status_code=404)
        except PermissionError as exc:
            return JSONResponse({'error': str(exc)}, status_code=400)
        svg = await run_in_threadpool(ws.render_score_pianoroll, str(resolved_file), start, end, voice)
        if request.headers.get('accept') == 'image/svg+xml':
            return Response(svg, media_type='image/svg+xml')
        return JSONResponse({'svg': svg})

    async def render_verovio_svg(request):
        data = await body(request)
        if 'path' in data:
            raise ValueError('No se admiten rutas del cliente. Proporciona el identificador del candidato o ejemplo.')
        score_id = data.get('id') or data.get('candidate_id') or data.get('ejemplo_id')
        if not score_id:
            raise ValueError('Se requiere el identificador del candidato o ejemplo del catálogo.')
        run_id = data.get('run_id')
        start = int(data.get('start', 1))
        end = int(data.get('end', 8))
        try:
            resolved_file = await run_in_threadpool(ws.resolve_score_path, score_id, run_id)
        except FileNotFoundError as exc:
            return JSONResponse({'error': str(exc)}, status_code=404)
        except PermissionError as exc:
            return JSONResponse({'error': str(exc)}, status_code=400)
        voice = data.get('voice') or data.get('highlight_voice')
        svg = await run_in_threadpool(ws.render_score_svg, str(resolved_file), start, end, voice)
        if request.headers.get('accept') == 'image/svg+xml':
            return Response(svg, media_type='image/svg+xml')
        return JSONResponse({'svg': svg})

    async def render_verovio_midi(request):
        data = await body(request)
        if 'path' in data:
            raise ValueError('No se admiten rutas del cliente. Proporciona el identificador del candidato o ejemplo.')
        score_id = data.get('id') or data.get('candidate_id') or data.get('ejemplo_id')
        if not score_id:
            raise ValueError('Se requiere el identificador del candidato o ejemplo del catálogo.')
        run_id = data.get('run_id')
        start = int(data.get('start', 1))
        end = int(data.get('end', 8))
        try:
            resolved_file = await run_in_threadpool(ws.resolve_score_path, score_id, run_id)
        except FileNotFoundError as exc:
            return JSONResponse({'error': str(exc)}, status_code=404)
        except PermissionError as exc:
            return JSONResponse({'error': str(exc)}, status_code=400)
        midi_base64 = await run_in_threadpool(ws.render_score_midi, str(resolved_file), start, end)
        return JSONResponse({'midi': midi_base64})

    async def shutdown(request):
        if any(j['status'] in ('queued', 'running') for j in ws.job_list()):
            raise ValueError('Espera a que terminen las tareas antes de cerrar Arkhé.')
        callback = getattr(request.app.state, 'shutdown', None)
        if callback is None:
            raise ValueError('Este servidor se cierra desde su lanzador.')
        callback()
        return JSONResponse({'ok': True})

    async def error(request, exc):
        return JSONResponse({'error': str(exc)}, status_code=400)

    routes = [Route('/', index), Route('/api/state', state), Route('/api/status', status), Route('/api/inbox', inbox),
              Route('/api/jobs', jobs),
              Route('/api/jobs/{id}/events', job_events),
              Route('/api/jobs/{id}/cancel', cancel_job, methods=['POST']), Route('/api/upload', upload, methods=['POST']),
              Route('/api/import', importing, methods=['POST']), Route('/api/documents/{id}', document),
              Route('/api/documents/{id}/authorize', authorize, methods=['POST']),
              Route('/api/documents/{id}/exclude', exclude, methods=['POST']),
              Route('/api/documents/{id}/delete', delete_doc, methods=['POST']),
              Route('/api/documents/{id}/metadata', metadata, methods=['POST']),
              Route('/api/generate', generation, methods=['POST']), Route('/api/runs/{id}', run),
              Route('/api/runs/{id}/delete', delete_run_route, methods=['POST']),
              Route('/api/runs/{id}/review', review, methods=['POST']),
              Route('/api/runs/{id}/edit', edit, methods=['POST']),
              Route('/api/runs/{id}/title', set_title, methods=['POST']),
              Route('/api/runs/{id}/subject', set_subject, methods=['POST']),

              Route('/api/runs/{id}/descargar-ejemplos-ficha', descargar_ejemplos_ficha_route, methods=['POST']),
              Route('/api/fichas/{id}/descargar-ejemplos', descargar_ejemplos_ficha_route, methods=['POST']),
              Route('/api/fichas/{id}', ficha_get),
              Route('/api/runs/{id}/music_requests/{req_id}/adopt', adopt_score, methods=['POST']),
              Route('/api/runs/{id}/music_requests/{req_id}/discard', discard_score, methods=['POST']),
              Route('/api/runs/{id}/music_requests/{req_id}/search_open_repos', search_repos, methods=['POST']),
              Route('/api/records', record_create, methods=['POST']),
              Route('/api/records/{id}', record_get),
              Route('/api/records/{id}/progress', record_progress, methods=['POST']),
              Route('/api/records/{id}/feedback', record_feedback, methods=['POST']),
              Route('/api/records/{id}/download', record_download), Route('/api/records/{id}/reveal', record_reveal, methods=['POST']),
              Route('/api/groups/{id}/records', group_records),
              Route('/api/calendar.ics', export_calendar),
              Route('/api/eventos-centro.ics', exportar_eventos),
              Route('/api/ejemplos', listar_ejemplos),
              Route('/api/ejemplos/{id}', obtener_ejemplo),
              Route('/api/ejemplos/{id}/wav', exportar_ejemplo_wav),
              Route('/api/scores/render-svg', render_verovio_svg, methods=['POST']),
              Route('/api/scores/render-pianoroll', render_score_pianoroll, methods=['POST']),
              Route('/api/scores/render-midi', render_verovio_midi, methods=['POST']),
              Route('/api/music/capabilities', music_capabilities_route),
              Route('/api/subjects', subject, methods=['POST']), Route('/api/groups', group, methods=['POST']),
              Route('/api/shutdown', shutdown, methods=['POST']), Route('/api/models', models, methods=['POST']), Route('/api/reveal', reveal, methods=['POST']), Route('/api/reveal-diary', reveal_diary, methods=['POST']), Mount('/assets', StaticFiles(directory=STATIC), name='assets')]

    routes.insert(0, Route('/api/secrets/deepseek', delete_api_key, methods=['DELETE']))
    routes.insert(0, Route('/api/secrets/provider', delete_api_key, methods=['DELETE']))
    routes.insert(0, Route('/api/provider/confirm', confirm_provider, methods=['POST']))
    routes.insert(0, Route('/api/runs/stats', stats))
    auth = None
    if server:
        from docente_ai.web.auth import AuthStore, routes as access_routes
        auth = AuthStore(server.auth_file)
        login, logout = access_routes(auth, server.public_host)
        from docente_ai.web.privacy import privacy
        routes.append(Route('/privacy', privacy))
        routes.extend([Route('/login', login, methods=['GET', 'POST']), Route('/api/logout', logout, methods=['POST'])])
    app = Starlette(routes=routes, lifespan=lifespan, exception_handlers={ValueError: error, OSError: error, sqlite3.Error: error})
    if server:
        from docente_ai.web.server import ServerOnly
        app.add_middleware(ServerOnly, settings=server, token=token, auth=auth)
    else:
        app.add_middleware(LocalOnly, token=token, port=port, allowed_hosts=allowed_hosts)
    app.state.workspace = ws
    return app
