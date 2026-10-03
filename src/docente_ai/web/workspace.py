"""Carpeta de conocimiento y servicios de la interfaz local."""

from collections import deque
from docente_ai.generation.live import LiveExecution, current_execution, GenerationCancelled
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import os
import subprocess
import sys
from threading import RLock
import unicodedata
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
import yaml

from docente_ai.agents.pedagogy import context_for
from docente_ai.config import SCHEMAS, load
from docente_ai.llm.generation import OllamaGenerator
from docente_ai.generation.service import ask, edit_run as _edit_run, get_run as _get_run, list_runs, run_stats, review_run as _review_run
from docente_ai.generation.render import render, render_sources, render_student
from docente_ai.generation.settings import load_settings as generation_settings
from docente_ai.secrets import set_secret, delete_secret, secret_configured
from docente_ai.llm.presets import PRESETS
from docente_ai.library.service import import_document, list_documents, show_document, authorize_document, update_document, read_connection
from docente_ai.rag.ollama import OllamaEmbedder
from docente_ai.rag.service import index_library, representation
from docente_ai.rag.settings import load_settings as rag_settings
from docente_ai.record.service import (
    add_feedback as _add_feedback, add_progress as _add_progress,
    add_record as _add_record, get_record as _get_record, list_records as _list_records,
)
from docente_ai.storage import import_config, read_config, connect, migrate
from docente_ai.teaching.calendar import sessions as calendar_sessions

CATEGORIES = {'documental': '01 Fuentes', 'profesor': '02 Material docente'}
SUFFIXES = {'.pdf', '.docx', '.txt', '.md'}
MAX_BYTES = 300 * 1024 * 1024


def daily_agenda(config, day=None):
    """Return the scheduled sessions for one local teaching day."""
    timezone = config.get('timezone', 'Europe/Madrid')
    selected_day = day or datetime.now(ZoneInfo(timezone)).date()
    if not isinstance(selected_day, date):
        raise ValueError('La fecha de la agenda no es válida.')
    return {
        'date': selected_day.isoformat(),
        'timezone': timezone,
        'sessions': calendar_sessions(config, selected_day, selected_day),
    }


def label(value, name, maximum=200):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        raise ValueError(f'{name}: escribe entre 1 y {maximum} caracteres.')
    return value.strip()


def slug(name):
    result = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return re.sub('[^a-z0-9]+', '-', result).strip('-')[:65] or 'materia'


class Workspace:
    def __init__(self, root, *, embedder_factory=OllamaEmbedder, ask_function=ask):
        self.root = Path(root).resolve()
        self.db = self.root / 'data/docente.sqlite3'
        self.knowledge = self.root / 'Conocimiento'
        self.embedder_factory = embedder_factory
        self.ask_function = ask_function
        self.lock = RLock()
        self.jobs = {}
        self.live_jobs = {}
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='docente-local')
        if not self.db.exists():
            config = self.root / 'config/teaching.yaml'
            data = load(config) if config.exists() else {'schema_version': 1, 'timezone': 'Europe/Madrid', **{key: [] for key in SCHEMAS}}
            import_config(self.db, data)
        with closing(connect(self.db)) as connection, connection:
            migrate(connection)
        self.ensure_folders()

    def close(self):
        self.pool.shutdown(wait=True)

    def ensure_folders(self):
        self.knowledge.mkdir(parents=True, exist_ok=True)
        (self.knowledge / '00 Entrada').mkdir(exist_ok=True)
        (self.knowledge / '03 Diario docente').mkdir(exist_ok=True)
        for category in CATEGORIES.values():
            folder = self.knowledge / category
            folder.mkdir(exist_ok=True)
            for subject in read_config(self.db)['subjects']:
                sub_folder = folder / subject['id']
                sub_folder.mkdir(exist_ok=True)
                for period in subject.get('periods', []):
                    (sub_folder / period['id']).mkdir(exist_ok=True)
        guide = self.knowledge / '_LEEME.md'
        if not guide.exists():
            guide.write_text('''# Tu biblioteca de conocimiento

00 Entrada: archivos pendientes de organizar.
01 Fuentes: libros, artículos y documentación.
02 Material docente: tus apuntes, ejercicios y explicaciones.
03 Diario docente: materiales y feedback de cada sesión, ordenados por fecha.

Las subcarpetas corresponden al identificador de cada materia.
Puedes copiar PDF, DOCX, TXT o Markdown. Los PDF escaneados requieren OCRmyPDF opcional en PATH y revisión del texto OCR. Máximo 100 MiB por archivo.
En la aplicación, pulsa «Revisar carpeta» para incorporar esos archivos.
Revisa la extracción y pulsa «Permitir al asistente» para autorizarlos e indexarlos.
Copiar un archivo aquí no lo autoriza automáticamente.

El catálogo conserva una copia de cada original en data/library. Cambiar un
archivo de esta carpeta requiere importar y autorizar su nueva versión.
Retirarlo de esta carpeta no lo excluye: usa «Excluir del asistente» en la app.

Los materiales generados se guardan aparte, en el historial de la aplicación.
No coloques generaciones de IA en esta carpeta como si fueran fuentes.
''', encoding='utf-8')

    def source_path(self, relative):
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError('Selecciona un archivo de la carpeta Conocimiento.')
        path = (self.knowledge / relative).resolve()
        if not path.is_relative_to(self.knowledge.resolve()) or path.suffix.lower() not in SUFFIXES or not path.is_file():
            raise ValueError('Archivo no admitido o fuera de Conocimiento.')
        if path.stat().st_size > MAX_BYTES:
            raise ValueError('El archivo supera los 100 MiB.')
        return path

    def scan(self):
        with closing(read_connection(self.db)) as connection:
            versions = list(connection.execute('SELECT document_id,source_path,sha256 FROM document_versions ORDER BY rowid'))
        known = {v['source_path']: v for v in versions}
        subjects = {s['id'] for s in read_config(self.db)['subjects']}
        files = []
        for path in sorted(self.knowledge.rglob('*')):
            if not path.is_file() or path.name.startswith(('.', '_')) or path.suffix.lower() not in SUFFIXES:
                continue
            if len(files) >= 1000:
                return {'files': files, 'truncated': True}
            if not path.resolve().is_relative_to(self.knowledge.resolve()):
                continue
            relative = path.relative_to(self.knowledge)
            size = path.stat().st_size
            previous = known.get(str(path.resolve()))
            imported = False
            if size <= MAX_BYTES:
                with path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                imported = digest == previous['sha256'] if previous else any(v['sha256'] == digest for v in versions)
            parts = relative.parts
            category = next((k for k, v in CATEGORIES.items() if parts[0] == v), 'documental')
            files.append({'path': str(relative), 'name': path.name, 'size': size, 'imported': imported,
                          'document_id': previous['document_id'] if previous else None,
                          'category': category, 'subject': parts[1] if len(parts) > 2 and parts[1] in subjects else '',
                          'too_large': size > MAX_BYTES})
        return {'files': files, 'truncated': False}

    def add_source(self, data):
        path = self.source_path(data.get('path'))
        document_id = data.get('document_id')
        if document_id:
            existing = show_document(self.db, document_id)
            # New versions keep their existing categorization and metadata.
            return import_document(self.db, path, category=existing['category'], document_id=document_id)
        subject = data.get('subject')
        category = data.get('category')
        if not subject or not any(item['id'] == subject for item in read_config(self.db)['subjects']):
            raise ValueError('Elige una materia existente para esta fuente.')
        if category not in CATEGORIES:
            raise ValueError('Elige fuente documental o material propio.')
        target = path
        moved = False
        if path.parent == (self.knowledge / '00 Entrada').resolve():
            folder = self.knowledge / CATEGORIES[category] / subject
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / path.name
            count = 1
            while target.exists():
                target = folder / f'{path.stem} ({count}){path.suffix}'
                count += 1
            target.hardlink_to(path)
            moved = True
        try:
            result = import_document(self.db, target, category=category, subjects=[subject])
        except BaseException:
            if moved:
                target.unlink(missing_ok=True)
            raise
        if moved:
            path.unlink()
        return result

    def prepare_source(self, document_id):
        settings = rag_settings(self.root / 'config/rag.yaml')
        with self.embedder_factory(settings) as embedder:
            def progress(done, total):
                with self.lock:
                    for job in self.jobs.values():
                        if job['status'] == 'running':
                            job['progress'] = {'done': done, 'total': total}
            return index_library(self.db, settings, embedder, document_ids=[document_id], progress=progress)

    def documents(self):
        documents = list_documents(self.db)
        try:
            settings = rag_settings(self.root / 'config/rag.yaml')
            identity = representation(settings)
            model = settings.model
        except ValueError:
            identity, model = '', ''
        with closing(read_connection(self.db)) as connection:
            indexes = {r[0] for r in connection.execute('SELECT i.version_id FROM rag_indexes i JOIN embedding_profiles p ON p.id=i.profile_id WHERE p.settings=? AND p.model IN (?,?)',
                       (identity, model, model + ':latest'))}
            versions = {r['id']: r for r in connection.execute('SELECT id,format,source_path FROM document_versions')}
        for doc in documents:
            doc['indexed'] = doc['current_version_id'] in indexes
            v = versions.get(doc['current_version_id'])
            doc['format'] = v['format'] if v else 'archivo'
            source_path = v['source_path'] if v else ''
            period = ''
            if source_path:
                try:
                    rel = Path(source_path).resolve().relative_to(self.knowledge.resolve())
                    parts = rel.parts
                    if len(parts) >= 3:
                        period = parts[2]
                except Exception:
                    pass
            doc['period'] = period
        return documents

    def state(self):
        runs = list_runs(self.db, limit=100)
        # Titles and scope for the real history, without sending prompts or raw responses.
        with closing(read_connection(self.db)) as connection:
            for item in runs:
                row = connection.execute('SELECT request_json,prompt_version FROM generation_runs WHERE id=?', (item['id'],)).fetchone()
                request = json.loads(row[0])
                item.update(title=request['question'], subject=request['subject'], kind='proposal' if 'pedagogy' in request else 'answer')
        try:
            gen_cfg = generation_settings(self.root / 'config/generation.yaml')
            gen_provider = gen_cfg.provider
            gen_model = gen_cfg.model
            provider_info = self.provider_info(gen_cfg)
        except Exception:
            gen_provider, gen_model = 'ollama', ''
            provider_info = {'indicator': 'Proveedor sin configurar', 'is_remote': False, 'remote_confirmed': False}
        config = read_config(self.db)
        try:
            pedagogy_info = self.provider_info(generation_settings(self.root / 'config/pedagogy.yaml'))
        except (ValueError, OSError):
            pedagogy_info = provider_info
        records = []
        for group in config['groups']:
            records.extend(self._record_with_archive(_get_record(self.db, item['id']))
                           for item in _list_records(self.db, group['id'], limit=20))
        records.sort(key=lambda item: (item['session_date'], item['created_at']), reverse=True)
        return {'config': config, 'documents': self.documents(), 'runs': runs,
                'subject_periods': {s['id']: [p['id'] for p in s.get('periods', [])] for s in config['subjects']},
                'agenda': daily_agenda(config),
                'records': records,
                'knowledge_path': str(self.knowledge), 'jobs': self.job_list(),
                'generation_provider': gen_provider, 'generation_model': gen_model,
                'api_key_configured': secret_configured(gen_cfg.secret_name) if gen_provider in PRESETS and provider_info['is_remote'] else False,
                'provider_info': provider_info, 'pedagogy_provider_info': pedagogy_info, 'provider_presets': PRESETS,
                'run_stats': run_stats(self.db, 100)}

    def model_status(self):
        status = {'connected': False, 'models': [], 'ollama_models': [], 'embedding_models': [],
                  'generation': None, 'embeddings': None, 'provider': 'ollama', 'message': '',
                  'api_key_configured': False}
        try:
            generation = generation_settings(self.root / 'config/generation.yaml')
            rag = rag_settings(self.root / 'config/rag.yaml')
            status.update(generation=generation.model, embeddings=rag.model, provider=generation.provider,
                          api_key_configured=secret_configured(generation.secret_name) if generation.is_remote else False)

            # Consultar modelos de Ollama para embeddings y generación local
            local_models = []
            try:
                with httpx.Client(timeout=3, trust_env=False, follow_redirects=False) as client:
                    response = client.get(rag.host + '/api/tags')
                    if response.is_success:
                        local_models = [m['name'] for m in response.json().get('models', [])]
            except Exception:
                pass

            status['ollama_models'] = local_models
            embed_list = list(local_models)
            if rag.model and rag.model not in embed_list:
                embed_list.insert(0, rag.model)
            if not embed_list:
                embed_list = ['bge-m3']
            status['embedding_models'] = embed_list

            if generation.is_remote:
                status['models'] = list(PRESETS[generation.provider]['models']) or [generation.model]
                status['connected'] = status['api_key_configured']
                if not status['api_key_configured']:
                    status['message'] = 'Introduce la clave del proveedor para activar el generador.'
            else:
                gen_list = list(local_models)
                if generation.model and generation.model not in gen_list:
                    gen_list.insert(0, generation.model)
                status['models'] = gen_list
                status['connected'] = bool(local_models)
        except (ValueError, KeyError, TypeError, OSError):
            status['message'] = 'No se pudo conectar con el motor generativo o falta su configuración.'
            status['embedding_models'] = ['bge-m3']
        return status

    def save_subject(self, data):
        name = label(data.get('name'), 'Nombre')
        with self.lock:
            config = read_config(self.db)
            subject_id = data.get('id')
            if subject_id:
                subject = next((s for s in config['subjects'] if s['id'] == subject_id), None)
                if subject is None:
                    raise ValueError('Materia inexistente.')
                subject['name'] = name
            else:
                subject_id = slug(name)
                if any(s['id'] == subject_id for s in config['subjects']):
                    raise ValueError('Ya existe una materia con ese nombre.')
                subject = {'id': subject_id, 'name': name}
                config['subjects'].append(subject)
            if 'color' in data:
                subject.pop('color', None)
                if data['color']:
                    subject['color'] = data['color']
            if 'periods' in data:
                subject['periods'] = data['periods']
            import_config(self.db, config, replace=True)
            self.ensure_folders()
        return {'id': subject_id}

    def save_group(self, data):
        name, level = label(data.get('name'), 'Grupo'), label(data.get('level'), 'Nivel')
        center_name = label(data.get('center'), 'Centro')
        teacher_name = label(data.get('teacher'), 'Profesor')
        year = data.get('year')
        if type(year) is not int or not 2000 <= year <= 2100:
            raise ValueError('Curso académico inválido.')
        language = data.get('language', 'es')
        if language not in ('es', 'gl', 'ca', 'eu', 'en', 'pt'):
            raise ValueError('Idioma no admitido.')
        with self.lock:
            config = read_config(self.db)
            def entity(table, name):
                row = next((x for x in config[table] if x['name'] == name), None)
                if row:
                    return row['id']
                identifier = f'{table}-{uuid4().hex[:10]}'
                config[table].append({'id': identifier, 'name': name})
                return identifier
            center_id, teacher_id = entity('centers', center_name), entity('teachers', teacher_name)
            current_group = next((g for g in config['groups'] if g['id'] == data.get('id')), None)
            preferred_year = current_group['academic_year_id'] if current_group else None
            available_years = [y for y in config['academic_years'] if y['start_date'].startswith(str(year) + '-')]
            academic = next((y for y in available_years if y['id'] == preferred_year), available_years[0] if available_years else None)
            if not academic:
                academic = {'id': f'curso-{uuid4().hex[:10]}', 'name': f'{year}–{year+1}', 'start_date': f'{year}-09-01', 'end_date': f'{year+1}-08-31'}
                config['academic_years'].append(academic)
            identifier = data.get('id') or f'grupo-{uuid4().hex[:10]}'
            if data.get('id') and not any(g['id'] == identifier for g in config['groups']):
                raise ValueError('Grupo inexistente.')
            group = {'id': identifier, 'name': name, 'level': level, 'subject_id': data.get('subject'),
                     'center_id': center_id, 'teacher_id': teacher_id, 'academic_year_id': academic['id'], 'language': language}
            config['groups'] = [g for g in config['groups'] if g['id'] != identifier] + [group]
            import_config(self.db, config, replace=True)
        return group

    def require_provider_consent(self, mode):
        generation_settings(self.root / 'config' / ('pedagogy.yaml' if mode == 'pedagogy' else 'generation.yaml')).require_consent()

    def generate(self, data):
        question = label(data.get('question'), 'Tema o pregunta', 4000)
        category = data.get('category', 'all')
        def progress(message):
            execution = current_execution()
            if execution:
                execution.check()
                execution.emit('stage', message=message)
        kwargs = {'subject': data.get('subject'), 'category': category, 'progress': progress}
        mode = data.get('mode')
        if mode not in ('ask', 'pedagogy'):
            raise ValueError('Tipo de consulta inválido.')
        config_name = 'generation.yaml'
        selected_settings = generation_settings(self.root / 'config' / ('pedagogy.yaml' if mode == 'pedagogy' else config_name))
        selected_settings.require_consent()
        if mode == 'pedagogy':
            session_date = None
            if data.get('session_date'):
                try:
                    session_date = date.fromisoformat(data['session_date'])
                except (TypeError, ValueError):
                    raise ValueError('La fecha de la clase debe tener formato YYYY-MM-DD.') from None
            context = context_for(
                self.db, data.get('group'), data.get('duration'),
                unit_id=data.get('unit') or None,
                criteria=data.get('criteria', ''), session_date=session_date,
            )
            kwargs.update(subject=context['group']['subject_id'], pedagogy_context=context)
            config_name = 'pedagogy.yaml'
        result = self.ask_function(self.db, rag_settings(self.root / 'config/rag.yaml'),
                                   generation_settings(self.root / 'config' / config_name), question, **kwargs)
        return {'run_id': result['id'], 'status': result['status']}

    def review_run(self, run_id: str, data: dict) -> dict:
        action = data.get('action')
        notes = data.get('notes', '')
        result = _review_run(self.db, run_id, action=action, notes=notes)
        return {k: result[k] for k in ('id', 'status', 'created_at', 'request', 'result', 'evidence', 'warnings', 'error', 'review')}

    def edit_run(self, run_id: str, data: dict) -> dict:
        allowed_patch_keys = {'objectives', 'difficulty', 'activities', 'resources', 'observations'}
        patch = {k: v for k, v in data.items() if k in allowed_patch_keys}
        result = _edit_run(self.db, run_id, plan_patch=patch)
        return {k: result[k] for k in ('id', 'status', 'created_at', 'request', 'result', 'evidence', 'warnings', 'error', 'review')}

    def delete_run(self, run_id: str) -> dict:
        from docente_ai.generation.service import delete_run as _delete_run
        return _delete_run(self.db, run_id)

    def delete_source(self, document_id: str) -> dict:
        from docente_ai.library.service import delete_document as _delete_document
        return _delete_document(self.db, document_id)

    # ── Registro de impartición ──────────────────────────────────────────────

    def _record_folder(self, record: dict) -> Path:
        day = date.fromisoformat(record['session_date'])
        group = next((item for item in read_config(self.db)['groups']
                      if item['id'] == record['group_id']), None)
        group_name = group['name'] if group else record['group_id']
        return (self.knowledge / '03 Diario docente' / str(day.year) /
                f'{day.month:02d}' / day.isoformat() /
                f'{slug(group_name)}--{record["id"][3:11]}')

    def _record_with_archive(self, record: dict) -> dict:
        return {**record, 'archive_path': str(self._record_folder(record))}

    def _write_record_archive(self, record: dict) -> dict:
        folder = self._record_folder(record)
        folder.mkdir(parents=True, exist_ok=True)
        group = next((item for item in read_config(self.db)['groups']
                      if item['id'] == record['group_id']), {})
        feedback = record.get('feedback') or {}
        lines = [
            '# Registro docente', '',
            f"**Fecha:** {record['session_date']}",
            f"**Grupo:** {group.get('name', record['group_id'])}",
            f"**Duración real:** {record['duration_minutes']} minutos", '',
            '## Contenido impartido', '', record['topic'], '',
            '## Notas de la sesión', '', record.get('notes') or 'Sin notas adicionales.', '',
            '## Feedback del profesor', '',
            '### Qué funcionó', '', feedback.get('what_worked') or 'Pendiente de completar.', '',
            '### Qué conviene ajustar', '', feedback.get('what_failed') or 'Pendiente de completar.', '',
            '### Para la próxima sesión', '', feedback.get('next_session_note') or 'Pendiente de completar.', '',
        ]
        target = folder / 'registro-docente.md'
        temporary = target.with_suffix('.tmp')
        temporary.write_text('\n'.join(lines), encoding='utf-8')
        temporary.replace(target)
        if record.get('run_id'):
            run = _get_run(self.db, record['run_id'])
            (folder / 'guia-profesor.md').write_text(render(run), encoding='utf-8')
            try:
                (folder / 'material-alumnado.md').write_text(render_student(run), encoding='utf-8')
            except ValueError:
                pass
            (folder / 'anexo-fuentes.md').write_text(render_sources(run), encoding='utf-8')
        return self._record_with_archive(record)

    def add_record(self, data: dict) -> dict:
        from datetime import date
        group_id = data.get('group_id') or data.get('group')
        raw_date = data.get('session_date') or data.get('date')
        if not raw_date:
            raise ValueError('Indica la fecha de la sesión (session_date: YYYY-MM-DD).')
        session_date = date.fromisoformat(raw_date)
        duration = data.get('duration_minutes') or data.get('duration')
        if duration is None:
            raise ValueError('Indica la duración de la sesión en minutos.')
        topic = data.get('topic', '')
        record = _add_record(self.db, group_id, session_date, int(duration), topic,
                             run_id=data.get('run_id'), notes=data.get('notes', ''),
                             objectives_met=data.get('objectives_met'),
                             activities=data.get('activities'))
        if any(data.get(key, '').strip() for key in
               ('what_worked', 'what_failed', 'next_session_note')):
            record = _add_feedback(self.db, record['id'],
                                   what_worked=data.get('what_worked', ''),
                                   what_failed=data.get('what_failed', ''),
                                   next_session_note=data.get('next_session_note', ''))
        return self._write_record_archive(record)

    def get_record(self, record_id: str) -> dict:
        return self._record_with_archive(_get_record(self.db, record_id))

    def add_progress(self, record_id: str, data: dict) -> dict:
        unit_id = data.get('unit_id') or data.get('unit')
        if not unit_id:
            raise ValueError('Indica el ID de la unidad (unit_id).')
        return self._write_record_archive(
            _add_progress(self.db, record_id, unit_id, note=data.get('note', '')))

    def add_feedback(self, record_id: str, data: dict) -> dict:
        return self._write_record_archive(_add_feedback(
            self.db, record_id,
            what_worked=data.get('what_worked', ''),
            what_failed=data.get('what_failed', ''),
            next_session_note=data.get('next_session_note', '')))

    def list_records(self, group_id: str, limit: int = 10) -> list:
        return [self._record_with_archive(_get_record(self.db, item['id']))
                for item in _list_records(self.db, group_id, limit=limit)]

    def provider_info(self, settings):
        return {'name': PRESETS[settings.provider]['name'], 'provider': settings.provider,
                'indicator': settings.indicator, 'is_remote': settings.is_remote,
                'data_residency': settings.data_residency, 'base_url': settings.base_url,
                'response_format': settings.response_format, 'model': settings.model,
                'remote_confirmed': settings.remote_confirmed, 'consent_scope': settings.consent_scope}

    def confirm_provider(self, data):
        with self.lock:
            configs = {name: generation_settings(self.root / 'config' / name) for name in ('generation.yaml', 'pedagogy.yaml')}
            current = configs['pedagogy.yaml' if data.get('mode') == 'pedagogy' else 'generation.yaml']
            if data.get('consent_scope') != current.consent_scope or data.get('confirmed') is not True:
                raise ValueError('La confirmación debe ser explícita y corresponder al proveedor actual.')
            if not current.is_remote:
                raise ValueError('La generación local no requiere confirmación de envío remoto.')
            for name, settings in configs.items():
                if settings.consent_scope == current.consent_scope:
                    path = self.root / 'config' / name
                    temporary = path.with_name('.' + name + '.' + uuid4().hex)
                    try:
                        temporary.write_text(yaml.safe_dump({'schema_version': 1, 'generation': asdict(replace(settings, remote_consent=current.consent_scope))}, allow_unicode=True, sort_keys=False))
                        os.replace(temporary, path)
                    finally:
                        temporary.unlink(missing_ok=True)
        return {'ok': True}

    def delete_api_key(self):
        with self.lock:
            settings = generation_settings(self.root / 'config/generation.yaml')
            if not settings.is_remote:
                raise ValueError('Selecciona el proveedor remoto cuya clave deseas borrar.')
            delete_secret(settings.secret_name)
        return {'ok': True, 'api_key_configured': secret_configured(settings.secret_name)}

    def save_models(self, data):
        with self.lock:
            if any(j['status'] in ('queued', 'running') for j in self.jobs.values()):
                raise ValueError('Espera a que terminen las tareas antes de cambiar los modelos.')
            folder = self.root / 'config'
            gen_current = generation_settings(folder / 'generation.yaml')
            ped_current = generation_settings(folder / 'pedagogy.yaml')
            rag_current = rag_settings(folder / 'rag.yaml')

            provider = data.get('provider', gen_current.provider)
            gen_model = data.get('generation') or gen_current.model
            api_key = data.get('api_key', '')
            if not isinstance(api_key, str):
                raise ValueError('La clave debe ser texto.')
            rag_model = data.get('embeddings') or rag_current.model

            changes = {'provider': provider, 'model': gen_model, 'base_url': data.get('base_url', '') if provider == 'custom' else '',
                       'data_residency': '', 'response_format': data.get('response_format', ''),
                       'num_ctx': 65536 if PRESETS.get(provider, {}).get('transport') == 'openai' else 6144}
            generation = replace(gen_current, **changes)
            pedagogy = replace(ped_current, **changes)
            if not generation.is_remote:
                with OllamaGenerator(generation):
                    pass

            rag = replace(rag_current, model=rag_model)
            with self.embedder_factory(rag):
                pass
            if data.get('delete_api_key'):
                delete_secret(generation.secret_name)
            elif api_key.strip():
                if not generation.is_remote:
                    raise ValueError('Las claves solo se guardan para proveedores remotos.')
                set_secret(generation.secret_name, api_key)
            files = {'generation.yaml': {'schema_version': 1, 'generation': asdict(generation)},
                     'pedagogy.yaml': {'schema_version': 1, 'generation': asdict(pedagogy)},
                     'rag.yaml': {'schema_version': 1, 'embeddings': asdict(rag)}}
            originals = {name: (folder/name).read_bytes() for name in files}
            changed = []
            try:
                for name, content in files.items():
                    path = folder/name
                    temporary = folder/('.' + name + '.' + uuid4().hex)
                    try:
                        temporary.write_text(yaml.safe_dump(content, allow_unicode=True, sort_keys=False))
                        os.replace(temporary, path)
                        changed.append(name)
                    finally:
                        temporary.unlink(missing_ok=True)
            except OSError:
                for name in changed:
                    (folder/name).write_bytes(originals[name])
                raise
        return {'ok': True}

    def submit(self, title, operation, *, key=None, cancellable=False):
        with self.lock:
            if key:
                for job in self.jobs.values():
                    if job.get('key') == key and job['status'] in ('queued', 'running'):
                        return {'job_id': job['id']}
            if sum(j['status'] in ('queued', 'running') for j in self.jobs.values()) >= 8:
                raise ValueError('Ya hay varias tareas pendientes. Espera a que termine una.')
            # Keep a bounded, refresh-safe set of job notifications; the result lives in SQLite.
            completed = [k for k, j in self.jobs.items() if j['status'] in ('done', 'failed', 'cancelled')]
            for old_id in completed[:-40]:
                del self.jobs[old_id]
                self.live_jobs.pop(old_id, None)
            identifier = uuid4().hex
            self.jobs[identifier] = {'id': identifier, 'key': key, 'title': title, 'status': 'queued',
                                     'result': None, 'error': None, 'cancellable': cancellable}
            live = {'events': deque(maxlen=1024), 'sequence': 0, 'text': '', 'attempt': 0}
            live['control'] = LiveExecution(lambda event, **data: self.publish_job(identifier, event, data))
            self.live_jobs[identifier] = live
        self.publish_job(identifier, 'stage', {'message': title})
        def work():
            execution = live['control']
            try:
                with execution.activate():
                    with self.lock:
                        self.jobs[identifier]['status'] = 'running'
                    result = operation()
                    execution.check()
                    with self.lock:
                        self.jobs[identifier].update(status='done', result=result)
            except GenerationCancelled:
                with self.lock:
                    self.jobs[identifier].update(status='cancelled', error='Consulta cancelada.',
                        result={'run_id': execution.run_id, 'status': 'cancelled'})
            except Exception as exc:
                with self.lock:
                    self.jobs[identifier].update(status='failed', error=str(exc))
            finally:
                with execution.lock:
                    execution.finished = True
                    execution.aborters.clear()
                with self.lock:
                    terminal = deepcopy(self.jobs[identifier])
                self.publish_job(identifier, 'terminal', terminal)
        future = self.pool.submit(work)
        with self.lock:
            live['future'] = future
        return {'job_id': identifier}

    def publish_job(self, identifier, event, data):
        with self.lock:
            live = self.live_jobs[identifier]
            if event != 'terminal' and self.jobs[identifier]['status'] in ('done', 'failed', 'cancelled'):
                return
            if event == 'stage':
                self.jobs[identifier]['title'] = data['message']
            if event == 'attempt':
                live['text'], live['attempt'] = '', data['attempt']
            if event == 'token':
                # Solo RAM: jamás se presenta como resultado validado ni se escribe en SQLite.
                live['text'] = (live['text'] + data['text'])[:100_000]
            if event == 'terminal': live['text'] = ''
            live['sequence'] += 1
            live['events'].append({'id': live['sequence'], 'event': event, 'data': deepcopy(data)})

    def job_events(self, identifier, after=0):
        with self.lock:
            if identifier not in self.jobs:
                return None
            live, job = self.live_jobs[identifier], self.jobs[identifier]
            if after > live['sequence'] or (live['events'] and after < live['events'][0]['id'] - 1):
                return [{'id': live['sequence'], 'event': 'snapshot', 'data': {
                    **deepcopy(job), 'text': live['text'], 'attempt': live['attempt']}}]
            events = [deepcopy(item) for item in live['events'] if item['id'] > after]
            if not events and job['status'] in ('done', 'failed', 'cancelled'):
                return [{'id': live['sequence'], 'event': 'terminal', 'data': deepcopy(job)}]
            return events

    def cancel_job(self, identifier):
        with self.lock:
            job = self.jobs.get(identifier)
            if job is None: return None
            if not job['cancellable']:
                raise ValueError('Esta tarea no admite cancelación.')
            control = self.live_jobs[identifier]['control']
        accepted = control.cancel()
        if accepted:
            future = self.live_jobs[identifier].get('future')
            if future and future.cancel():
                with control.lock:
                    control.finished = True
                with self.lock:
                    job.update(status='cancelled', error='Consulta cancelada.',
                               result={'run_id': None, 'status': 'cancelled'})
                    terminal = deepcopy(job)
                self.publish_job(identifier, 'terminal', terminal)
            else:
                self.publish_job(identifier, 'stage', {'message': 'Cancelando consulta…'})
        return {'accepted': accepted, 'status': 'cancelling' if accepted else job['status']}

    def job_list(self):
        with self.lock:
            return deepcopy(list(self.jobs.values()))

    def reveal(self):
        if sys.platform != 'darwin':
            raise ValueError(f'Abre esta carpeta en tu explorador: {self.knowledge}')
        subprocess.run(['open', str(self.knowledge)], check=True)
        return {'ok': True}

    def reveal_diary(self):
        folder = self.knowledge / '03 Diario docente'
        folder.mkdir(exist_ok=True)
        if sys.platform != 'darwin':
            raise ValueError(f'Abre esta carpeta en tu explorador: {folder}')
        subprocess.run(['open', str(folder)], check=True)
        return {'ok': True}

    def reveal_record(self, record_id: str):
        record = _get_record(self.db, record_id)
        folder = self._record_folder(record)
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform != 'darwin':
            raise ValueError(f'Abre esta carpeta en tu explorador: {folder}')
        subprocess.run(['open', str(folder)], check=True)
        return {'ok': True}

    def calendar_ics(self, *, group_id=None, reminder_minutes=15):
        from docente_ai.teaching.calendar import to_ical
        config = read_config(self.db)
        return to_ical(config, group_id=group_id, reminder_minutes=reminder_minutes)
