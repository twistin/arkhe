"""Ejecuciones documentadas y auditadas, sin aprobación automática."""

from contextlib import closing
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
from typing import Any, Optional
from uuid import uuid4

from docente_ai.generation.live import current_execution, emit_live, GenerationCancelled
from docente_ai import __version__
from docente_ai.generation.prompt import PROMPT_VERSION, build_prompt
from docente_ai.generation.validation import validate_response
from docente_ai.generation.errors import SourceChangedError
from docente_ai.generation.repair import generate_validated, repair_with_review
from docente_ai.agents.reviewer import perform_review
from docente_ai.library.service import now, read_connection
from docente_ai.llm.generation import OllamaGenerator
from docente_ai.rag.ollama import OllamaEmbedder
from docente_ai.rag.service import eligible, search, verify_original
from docente_ai.storage import connect, migrate


class GenerationFailure(ValueError):
    pass


def dump(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def check_evidence(connection, db, evidence, request):
    current = {item['version_id']: item for item in eligible(
        connection, subject=request['subject'], category=request['category'], document_ids=request['document_ids'])}
    checked = set()
    for source in evidence:
        version = current.get(source['version_id'])
        if version is None or version['document_id'] != source['document_id'] or version['category'] != source['category']:
            raise SourceChangedError('Una fuente ha sido excluida, reasignada o sustituida. Repite la consulta con el corpus actual.')
        if json.loads(version['metadata']) != source['metadata']:
            raise SourceChangedError('Los metadatos de una fuente han cambiado durante la consulta.')
        chunk = connection.execute('SELECT text,locator,version_id,profile_id FROM rag_chunks WHERE id=?', (source['chunk_id'],)).fetchone()
        if not chunk or chunk['version_id'] != source['version_id'] or chunk['text'] != source['text'] or json.loads(chunk['locator']) != source['locator']:
            raise SourceChangedError('La evidencia recuperada ya no coincide con el índice.')
        if source['version_id'] not in checked:
            try:
                verify_original(db, version)
            except (ValueError, OSError) as exc:
                raise SourceChangedError('El original de una fuente ha cambiado o ya no está disponible.') from exc
            checked.add(source['version_id'])


def record_prompt(db, run_id, bundle, model, digest):
    with closing(connect(db)) as connection, connection:
        connection.execute('UPDATE generation_runs SET model=?,digest=?,messages_json=?,evidence_json=?,omitted_json=? WHERE id=?',
                           (model, digest, dump(bundle['messages']), dump(bundle['evidence']), dump(bundle['omitted']), run_id))


def finish(db, run_id, *, status, result=None, raw=None, metrics=None, error=None, evidence=None, request=None):
    with closing(connect(db)) as connection, connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN IMMEDIATE')
        if evidence:
            check_evidence(connection, db, evidence, request)
        connection.execute('''UPDATE generation_runs SET status=?,finished_at=?,result_json=?,raw_response=?,metrics_json=?,error=? WHERE id=?''',
                           (status, now(), dump(result) if result is not None else None, raw, dump(metrics or {}), error, run_id))


def ask(db: Path, rag_settings, settings, question: str, *, subject: str,
        category='documental', document_ids=None, top_k=12, max_distance=None,
        embedder_factory=OllamaEmbedder, generator_factory=OllamaGenerator, pedagogy_context=None, progress=None):
    execution = current_execution()
    if execution:
        execution.check()
    settings.require_consent()
    if not isinstance(question, str) or not question.strip() or len(question) > 4000:
        raise ValueError('Escribe una pregunta de entre 1 y 4000 caracteres.')
    if not subject:
        raise ValueError('La consulta necesita una asignatura explícita.')
    if type(top_k) is not int or not 1 <= top_k <= 100:
        raise ValueError('top_k debe estar entre 1 y 100.')
    if max_distance is not None and (type(max_distance) not in (int, float) or not math.isfinite(max_distance) or not 0 <= max_distance <= 2):
        raise ValueError('La distancia máxima debe estar entre 0 y 2.')
    # Validar selección y existencia antes de crear una ejecución o llamar modelos.
    with closing(read_connection(db)) as connection:
        sources = eligible(connection, subject=subject, category=category, document_ids=document_ids)
    programming_sources = [source for source in sources
                           if json.loads(source['metadata']).get('document_type') == 'programacion_didactica']
    generation_request = asdict(settings)
    from docente_ai.secrets import secret_configured
    generation_request['api_key_configured'] = settings.is_remote and secret_configured(settings.secret_name)
    from docente_ai.teaching.terms import normalize_topic
    norm_topic = normalize_topic(question)
    display_title = (norm_topic[:1].upper() + norm_topic[1:]) if norm_topic else question
    original_topic = question
    request = {'app_version': __version__, 'question': question, 'display_title': display_title,
               'original_topic': original_topic, 'subject': subject, 'category': category,
               'document_ids': document_ids, 'top_k': top_k, 'max_distance': max_distance,
               'generation': generation_request, 'rag': asdict(rag_settings)}
    prompt_version = PROMPT_VERSION
    default_generator = generator_factory is OllamaGenerator
    if pedagogy_context is not None:
        from docente_ai.agents import pedagogy
        if pedagogy_context['group']['subject_id'] != subject:
            raise ValueError('El grupo y la asignatura no coinciden.')
        if programming_sources:
            pedagogy_context['programming_documents'] = [
                {'id': source['document_id'], 'title': json.loads(source['metadata'])['title']}
                for source in programming_sources
            ]
        request['pedagogy'] = pedagogy_context
        prompt_version = pedagogy.PROMPT_VERSION
    run_id = 'run-' + uuid4().hex
    # Seleccionar generador según el proveedor configurado.
    is_local = not settings.is_remote
    if default_generator:
        if not is_local:
            from docente_ai.llm.openai_compatible import OpenAICompatibleGenerator
            generator_factory = OpenAICompatibleGenerator
        elif pedagogy_context is not None:
            generator_factory = pedagogy.PedagogicalGenerator
    enhanced_retrieval = default_generator
    if pedagogy_context is not None:
        top_k = max(top_k, 16)
    with closing(connect(db)) as connection, connection:
        migrate(connection)
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('INSERT INTO generation_runs(id,created_at,status,request_json,prompt_version,display_title,original_topic) VALUES (?,?,?,?,?,?,?)',
                           (run_id, now(), 'running', dump(request), prompt_version, display_title, original_topic))
    if execution:
        execution.run_id = run_id
    emit_live('run', run_id=run_id)
    raw, metrics = None, {}
    def complete(**kwargs):
        operation = lambda: finish(db, run_id, **kwargs)
        if execution:
            execution.complete(operation)
        else:
            operation()

    try:
        retrieval_started = time.monotonic()
        report = progress or (lambda message: None)
        retrieval_question = question
        requirements = []
        if pedagogy_context is not None:
            pedagogy_context['topic'] = question
            teacher_crit = pedagogy_context.get('teacher_criteria', '').strip()
            if teacher_crit:
                retrieval_question += '\nEnfoque indicado por el profesor: ' + teacher_crit
            if 'requirements' in pedagogy_context and pedagogy_context['requirements']:
                requirements = pedagogy_context['requirements']
            else:
                from docente_ai.rag.planning import extract_requirements
                report('Extrayendo requisitos pedagógicos')
                # Solo pasar generator_factory si estamos en recuperación avanzada con modelo real,
                # para no consumir diálogos de fakes en tests.
                extractor_factory = generator_factory if enhanced_retrieval else None
                requirements = extract_requirements(question, teacher_crit, settings, generator_factory=extractor_factory)
                pedagogy_context['requirements'] = requirements
            request['requirements'] = requirements
            with closing(connect(db)) as connection, connection:
                connection.execute('UPDATE generation_runs SET request_json=? WHERE id=?', (dump(request), run_id))

        variants = []
        if sources and enhanced_retrieval:
            from docente_ai.rag.planning import plan_queries
            report('Preparando búsqueda multilingüe')
            # Generar consultas orientadas al tema y a los requisitos pedagógicos
            variants = plan_queries(retrieval_question, settings, generator_factory=generator_factory)
            if requirements:
                for req in requirements:
                    req_desc = req['description'].strip()
                    if req_desc and req_desc not in variants and req_desc != question:
                        variants.append(req_desc)
                variants = list(dict.fromkeys(variants))[:11]

        programming_results = []
        if sources:
            report('Buscando pasajes en tus fuentes')
            # Cerrar el adaptador de embeddings antes de cargar el generativo.
            with embedder_factory(rag_settings) as embedder:
                retrieved = search(db, rag_settings, embedder, retrieval_question, subject=subject,
                                   category=category, document_ids=document_ids, top_k=max(top_k, 24) if variants else top_k, max_distance=max_distance, query_variants=variants)
                
                # Búsqueda específica por requisito para garantizar que cada uno tenga candidatos etiquetados
                if requirements:
                    existing_chunks = {r['chunk_id']: r for r in retrieved['results']}
                    for req in requirements:
                        req_query = f"{question} {req['description']}"
                        req_res = search(db, rag_settings, embedder, req_query, subject=subject,
                                         category=category, document_ids=document_ids, top_k=4, max_distance=max_distance)
                        for r_item in req_res['results']:
                            cid = r_item['chunk_id']
                            if cid not in existing_chunks:
                                r_item['requirement_id'] = req['id']
                                retrieved['results'].append(r_item)
                                existing_chunks[cid] = r_item
                            elif 'requirement_id' not in existing_chunks[cid]:
                                existing_chunks[cid]['requirement_id'] = req['id']

                # La programación fija el marco de la propuesta. Se recupera por
                # separado para que un corpus grande no la expulse por similitud.
                programming_ids = [source['document_id'] for source in programming_sources]
                if pedagogy_context is not None and programming_ids:
                    report('Consultando la programación de la materia')
                    session = pedagogy_context.get('session') or {}
                    scheduled = (
                        f" Sesión {session['sequence_number']} del curso, fecha {session['date']}."
                        if session.get('sequence_number') else ''
                    )
                    programming = search(
                        db, rag_settings, embedder,
                        retrieval_question + '\nProgramación didáctica:' + scheduled
                        + ' objetivos, contenidos, secuencia, temporalización y evaluación.',
                        subject=subject, category=category,
                        document_ids=programming_ids, top_k=min(4, top_k),
                        max_distance=max_distance,
                    )
                    programming_results = programming['results']
                    programming_chunk_ids = {item['chunk_id'] for item in programming_results}
                    retrieved['results'] = [
                        *programming_results,
                        *(item for item in retrieved['results'] if item['chunk_id'] not in programming_chunk_ids),
                    ]
        else:
            retrieved = {'results': []}
        candidate_count = len(retrieved['results'])
        ranking_audit = None
        if variants and retrieved['results']:
            from docente_ai.rag.planning import rerank
            retrieved['results'], ranking_audit = rerank(retrieval_question, retrieved['results'], settings, limit=top_k,
                                                         progress=report, generator_factory=generator_factory)
            if programming_results:
                programming_chunk_ids = {item['chunk_id'] for item in programming_results}
                retrieved['results'] = [
                    *programming_results,
                    *(item for item in retrieved['results'] if item['chunk_id'] not in programming_chunk_ids),
                ]
        metrics = {'retrieval_ranking': ranking_audit, 'retrieval_queries': [retrieval_question, *variants], 'retrieval_method': 'hybrid-rrf:1' if variants else 'semantic:1', 'retrieval_profile_id': retrieved.get('profile_id'), 'retrieval_candidate_count': candidate_count, 'retrieval_selected_count': len(retrieved['results']), 'retrieval_seconds': round(time.monotonic() - retrieval_started, 2)}
        if not retrieved['results']:
            result = {'status': 'insufficient_sources', 'claims': [], 'visualizations': []}
            if pedagogy_context is not None:
                result['plan'] = None
            complete(status='abstained', result=result, metrics=metrics)
            return get_run(db, run_id)
        bundle = (build_prompt(question, retrieved['results'], settings) if pedagogy_context is None else
                  pedagogy.build_prompt(question, retrieved['results'], settings, pedagogy_context))
        report('Redactando con los pasajes seleccionados')
        record_prompt(db, run_id, bundle, settings.model, None)
        with generator_factory(settings) as generator:
            model_id = getattr(generator, 'model', settings.model)
            digest = getattr(generator, 'digest', None)
            record_prompt(db, run_id, bundle, model_id, digest)
            def check():
                if execution:
                    execution.check()
                with closing(read_connection(db)) as connection:
                    check_evidence(connection, db, bundle['evidence'], request)
            validator = (lambda content, **kwargs: validate_response(content, bundle['evidence'])) if pedagogy_context is None else (
                lambda content, **kwargs: pedagogy.validate(content, bundle['evidence'], pedagogy_context, **kwargs))
            result, raw = generate_validated(generator, bundle['messages'], validator, metrics,
                                            check=check, report=report, sanitize_response=not is_local,
                                            on_dialogue=lambda dialogue: record_prompt(db, run_id, {**bundle, 'messages': dialogue}, model_id, digest))

            # Paso de revisión opcional si está activado en settings y la propuesta fue respondida
            if getattr(settings, 'enable_review', False) and result.get('status') == 'answered' and pedagogy_context is not None:
                report('Ejecutando revisión pedagógica con la rúbrica')
                requirements = pedagogy_context.get('requirements') or []
                rev_start_t = time.monotonic()
                review_data = perform_review(
                    generator, result, requirements, bundle['evidence'], pedagogy_context, question, report=report
                )
                rev_duration = round(time.monotonic() - rev_start_t, 3)
                initial_review_tokens = review_data.get('_metrics', {})
                initial_scores = dict(review_data.get('scores', {}))
                review_scores = review_data.get('scores', {})
                min_score = min(review_scores.values()) if review_scores else 3
                total_score = sum(review_scores.values()) if review_scores else 18
                min_thresh = getattr(settings, 'review_repair_min_score', 2)
                total_thresh = getattr(settings, 'review_repair_total_score', 15)
                needs_repair = (
                    min_score <= min_thresh
                    or total_score < total_thresh
                )
                had_repair = False
                repair_duration = 0.0
                post_review_duration = 0.0
                if needs_repair and review_data.get('issues'):
                    try:
                        rep_start_t = time.monotonic()
                        repaired_result, repaired_raw = repair_with_review(
                            generator, bundle['messages'], raw, review_data['issues'], validator, metrics,
                            check=check, report=report, sanitize_response=not is_local
                        )
                        repair_duration = round(time.monotonic() - rep_start_t, 3)
                        result, raw = repaired_result, repaired_raw
                        had_repair = True
                        post_rev_start_t = time.monotonic()
                        review_data = perform_review(
                            generator, result, requirements, bundle['evidence'], pedagogy_context, question, report=report
                        )
                        post_review_duration = round(time.monotonic() - post_rev_start_t, 3)
                    except Exception as rep_exc:
                        report('La ronda de reparación no prosperó; conservando propuesta original')
                final_review_tokens = review_data.get('_metrics', {})
                metrics['auto_review'] = {
                    'initial_scores': initial_scores,
                    'scores': review_data.get('scores'),
                    'issues': review_data.get('issues'),
                    'summary': review_data.get('summary'),
                    'repaired': had_repair,
                    'seconds': {
                        'initial_review': rev_duration,
                        'repair': repair_duration,
                        'post_review': post_review_duration,
                        'total': round(rev_duration + repair_duration + post_review_duration, 3)
                    },
                    'tokens': {
                        'initial_review': {
                            'input': initial_review_tokens.get('prompt_eval_count'),
                            'output': initial_review_tokens.get('eval_count'),
                        } if initial_review_tokens else None,
                        'final_review': {
                            'input': final_review_tokens.get('prompt_eval_count'),
                            'output': final_review_tokens.get('eval_count'),
                        } if final_review_tokens else None,
                    }
                }

        if result and isinstance(result.get('music_requests'), list):
            try:
                from docente_ai.teaching.score_resolver import resolver_todas_las_peticiones
                report('Resolviendo peticiones de partituras y ejemplos musicales')
                result['resolved_music_requests'] = resolver_todas_las_peticiones(
                    result['music_requests'],
                    con_repositorios_abiertos=False
                )
            except Exception as res_err:
                report(f'Aviso en resolución de partituras: {res_err}')

        metrics.update(estimated_input_bytes=bundle['estimated_input'], omitted_count=len(bundle['omitted']))
        complete(status='draft' if result['status'] == 'answered' else 'abstained',
               result=result, raw=raw, metrics=metrics, evidence=bundle['evidence'], request=request)
        return get_run(db, run_id)
    except GenerationCancelled:
        metrics['error_type'] = 'cancelled'
        finish(db, run_id, status='cancelled', error='Cancelado por el usuario.', metrics=metrics)
        raise
    except KeyboardInterrupt:
        metrics['error_type'] = 'cancelled'
        finish(db, run_id, status='cancelled', error='Cancelado por el usuario.', raw=raw, metrics=metrics)
        raise KeyboardInterrupt(f'Operación cancelada. Registro: {run_id}') from None
    except Exception as exc:
        if execution and execution.cancelled.is_set():
            metrics['error_type'] = 'cancelled'
            finish(db, run_id, status='cancelled', error='Cancelado por el usuario.', metrics=metrics)
            raise GenerationCancelled('Consulta cancelada por el usuario.') from None
        raw = getattr(exc, 'content', raw)
        metrics['error_type'] = getattr(exc, 'error_type', 'internal')
        finish(db, run_id, status='failed', error=str(exc), raw=raw, metrics=metrics)
        raise GenerationFailure(f'Consulta fallida; registro {run_id}: {exc}') from exc


def get_run(db: Path, run_id: str):
    with closing(read_connection(db)) as connection:
        if connection.execute('PRAGMA user_version').fetchone()[0] < 4:
            raise ValueError('Todavía no hay registros generativos.')
        row = connection.execute('SELECT * FROM generation_runs WHERE id=?', (run_id,)).fetchone()
        if not row:
            raise ValueError(f'Registro generativo inexistente: {run_id}.')
        record = dict(row)
        for key in ('request', 'messages', 'evidence', 'omitted', 'result', 'metrics'):
            value = record.pop(key + '_json')
            record[key] = json.loads(value) if value is not None else None
        record.pop('raw_response')  # Una respuesta rechazada no se publica por accidente.
        review_raw = record.pop('review_json', None)
        record['review'] = json.loads(review_raw) if review_raw else None
        record['warnings'] = []
        if record['status'] in ('draft', 'abstained') and record['evidence']:
            try:
                check_evidence(connection, db, record['evidence'], record['request'])
            except (ValueError, OSError) as exc:
                record['warnings'].append('Registro histórico: la evidencia ya no está vigente. ' + str(exc))

        req = record.get('request') or {}
        orig = record.get('original_topic') or req.get('original_topic') or req.get('question') or ''
        disp = record.get('display_title') or req.get('display_title')
        if not disp:
            from docente_ai.teaching.terms import normalize_topic
            norm = normalize_topic(orig)
            disp = (norm[:1].upper() + norm[1:]) if norm else orig
        from docente_ai.teaching.fichas import get_ficha_for_run
        record['ficha'] = get_ficha_for_run(record, directory=db.parent / 'fichas')
        record['original_topic'] = orig
        record['display_title'] = disp
    return record


def list_runs(db: Path, limit=20):
    with closing(read_connection(db)) as connection:
        if connection.execute('PRAGMA user_version').fetchone()[0] < 4:
            return []
        cols = {col[1] for col in connection.execute('PRAGMA table_info(generation_runs)').fetchall()}
        has_display = 'display_title' in cols
        query = (
            'SELECT id,created_at,status,model,error,display_title,original_topic FROM generation_runs ORDER BY created_at DESC LIMIT ?'
            if has_display else
            'SELECT id,created_at,status,model,error FROM generation_runs ORDER BY created_at DESC LIMIT ?'
        )
        return [dict(row) for row in connection.execute(query, (limit,))]


def update_run_title(db: Path, run_id: str, title: str) -> dict:
    """Actualiza manualmente el título visible de una propuesta.

    La edición manual tiene prioridad sobre normalizaciones automáticas.
    """
    clean_title = (title or '').strip()
    if not clean_title:
        raise ValueError('El título no puede estar vacío.')
    if len(clean_title) > 500:
        raise ValueError('El título no puede exceder 500 caracteres.')
    with closing(connect(db)) as connection, connection:
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute('SELECT request_json FROM generation_runs WHERE id=?', (run_id,)).fetchone()
        if not row:
            raise ValueError(f'Registro generativo inexistente: {run_id}.')
        request_raw = row[0]
        req = json.loads(request_raw) if request_raw else {}
        req['display_title'] = clean_title
        req['manual_title'] = True
        connection.execute(
            'UPDATE generation_runs SET display_title = ?, request_json = ? WHERE id = ?',
            (clean_title, dump(req), run_id)
        )
    return get_run(db, run_id)


def run_stats(db: Path, limit=100):
    """Resumen acotado sin recuperar preguntas, fuentes ni respuestas crudas."""
    if type(limit) is not int or not 1 <= limit <= 10000:
        raise ValueError('El límite de estadísticas debe estar entre 1 y 10000.')
    with closing(read_connection(db)) as connection:
        if connection.execute('PRAGMA user_version').fetchone()[0] < 4:
            rows = []
        else:
            rows = connection.execute('SELECT status,metrics_json,error FROM generation_runs ORDER BY created_at DESC,id DESC LIMIT ?', (limit,)).fetchall()
    counts = dict.fromkeys(('draft', 'failed', 'abstained', 'cancelled', 'running'), 0)
    errors = {}
    repaired = 0
    for row in rows:
        counts[row['status']] += 1
        metrics = json.loads(row['metrics_json'])
        if row['status'] == 'draft' and len(metrics.get('attempts', [])) > 1:
            repaired += 1
        if row['status'] == 'failed':
            error_type = metrics.get('error_type') or 'legacy_untyped'
            errors[error_type] = errors.get(error_type, 0) + 1
    total = len(rows)
    return {'limit': limit, 'total': total, 'counts': counts,
            'rates': {key: round(value * 100 / total, 2) if total else 0.0 for key, value in counts.items()},
            'errors': dict(sorted(errors.items())), 'repaired_drafts': repaired}


def review_run(db: Path, run_id: str, *, action: str, notes: str = '') -> dict:
    """Aprobar o rechazar un borrador. Requiere status=draft y registra hash del result_json."""
    if action not in ('approved', 'rejected'):
        raise ValueError("La acción debe ser 'approved' o 'rejected'.")
    if not isinstance(notes, str) or len(notes) > 2000:
        raise ValueError('Las notas admiten hasta 2000 caracteres.')
    with closing(connect(db)) as connection, connection:
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute(
            'SELECT status, result_json FROM generation_runs WHERE id=?', (run_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f'Registro generativo inexistente: {run_id}.')
        status, result_json = row
        if status != 'draft':
            raise ValueError(f'Solo se pueden revisar borradores (estado actual: {status}).')
        approved_hash = hashlib.sha256(result_json.encode()).hexdigest() if result_json else None
        review = {'action': action, 'notes': notes, 'reviewed_at': now(), 'approved_hash': approved_hash}
        connection.execute(
            'UPDATE generation_runs SET review_json=? WHERE id=?',
            (dump(review), run_id)
        )
    return get_run(db, run_id)


def edit_run(db: Path, run_id: str, *, plan_patch: dict) -> dict:
    """Editar campos del plan pedagógico. Invalida la revisión anterior. Solo para borradores con plan."""
    allowed = {'objectives', 'difficulty', 'activities', 'resources', 'observations'}
    invalid = set(plan_patch) - allowed
    if invalid:
        raise ValueError(f'Campos no editables en el plan: {", ".join(sorted(invalid))}.')
    with closing(connect(db)) as connection, connection:
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute(
            'SELECT status, result_json FROM generation_runs WHERE id=?', (run_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f'Registro generativo inexistente: {run_id}.')
        status, result_json = row
        if status != 'draft':
            raise ValueError(f'Solo se puede editar un borrador (estado actual: {status}).')
        if not result_json:
            raise ValueError('Este registro no tiene un resultado que editar.')
        result = json.loads(result_json)
        plan = result.get('plan')
        if not isinstance(plan, dict):
            raise ValueError('Este borrador no contiene un plan pedagógico editable.')
        plan.update(plan_patch)
        # Revalidar suma de minutos si se editan actividades.
        if 'activities' in plan_patch:
            activities = plan.get('activities', [])
            if not isinstance(activities, list):
                raise ValueError('Las actividades deben ser una lista.')
            total = sum(a.get('minutes', 0) for a in activities if isinstance(a, dict))
            request = json.loads(connection.execute(
                'SELECT request_json FROM generation_runs WHERE id=?', (run_id,)
            ).fetchone()[0])
            expected = (request.get('pedagogy') or {}).get('duration_minutes')
            if expected is not None and total != expected:
                raise ValueError(
                    f'Las actividades editadas suman {total} minutos; la sesión requiere {expected}.'
                )
        result['plan'] = plan
        connection.execute(
            'UPDATE generation_runs SET result_json=?, review_json=NULL WHERE id=?',
            (dump(result), run_id)
        )
    return get_run(db, run_id)


def delete_run(db: Path, run_id: str) -> dict:
    if not db.is_file():
        raise StorageError('No existe la base de datos.')
    with closing(connect(db)) as connection, connection:
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('DELETE FROM session_records WHERE run_id=?', (run_id,))
        connection.execute('DELETE FROM generation_runs WHERE id=?', (run_id,))
    return {'run_id': run_id, 'deleted': True}


def adopt_score_candidate(
    db: Path,
    run_id: str,
    request_id: str,
    candidate_id: str,
    *,
    rango_compases: str = "1-8",
    voz_resaltar: str | None = None,
    directorio_destino: Path | str | None = None
) -> dict:
    """Adopta un candidato de partitura y lo guarda en data/ejemplos/ con verificado: true."""
    from docente_ai.teaching.score_resolver import usar_candidato_como_ejemplo
    with closing(connect(db)) as connection, connection:
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute(
            'SELECT status, result_json FROM generation_runs WHERE id=?', (run_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f'Registro generativo inexistente: {run_id}.')
        status, result_json = row
        if not result_json:
            raise ValueError('El registro no contiene resultado.')
        result = json.loads(result_json)
        music_requests = result.get('music_requests', [])
        resolved_list = result.get('resolved_music_requests', [])

        req = next((r for r in music_requests if r.get('id') == request_id), None)
        if not req:
            raise ValueError(f'Petición musical inexistente: {request_id}.')

        resolved_item = next((r for r in resolved_list if r.get('request_id') == request_id), None)
        if not resolved_item:
            raise ValueError(f'Resolución de petición musical no encontrada: {request_id}.')

        candidato = next((c for c in resolved_item.get('candidatos', []) if c.get('id') == candidate_id), None)
        if not candidato:
            raise ValueError(f'Candidato de partitura no encontrado: {candidate_id}.')

        nuevo_ejemplo = usar_candidato_como_ejemplo(
            req,
            candidato,
            rango_compases=rango_compases,
            voz_resaltar=voz_resaltar,
            directorio_destino=directorio_destino
        )

        resolved_item['status'] = 'resuelto_catalogo'
        resolved_item['origen'] = 'catalogo_local'
        resolved_item['ejemplo'] = nuevo_ejemplo
        resolved_item['verificado'] = True
        resolved_item['candidatos'] = []

        result['resolved_music_requests'] = resolved_list
        connection.execute(
            'UPDATE generation_runs SET result_json=? WHERE id=?',
            (dump(result), run_id)
        )
    return get_run(db, run_id)


def discard_score_candidate(
    db: Path,
    run_id: str,
    request_id: str,
    candidate_id: str
) -> dict:
    """Descarta un candidato de partitura para la petición indicada."""
    with closing(connect(db)) as connection, connection:
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute(
            'SELECT status, result_json FROM generation_runs WHERE id=?', (run_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f'Registro generativo inexistente: {run_id}.')
        status, result_json = row
        if not result_json:
            raise ValueError('El registro no contiene resultado.')
        result = json.loads(result_json)
        resolved_list = result.get('resolved_music_requests', [])
        resolved_item = next((r for r in resolved_list if r.get('request_id') == request_id), None)
        if not resolved_item:
            raise ValueError(f'Resolución de petición musical no encontrada: {request_id}.')

        candidatos = [c for c in resolved_item.get('candidatos', []) if c.get('id') != candidate_id]
        resolved_item['candidatos'] = candidatos
        descartes = resolved_item.setdefault('descartes', [])
        if candidate_id not in descartes:
            descartes.append(candidate_id)
        if not candidatos and resolved_item.get('status') == 'candidatos_pendientes':
            resolved_item['status'] = 'sin_resolver'

        result['resolved_music_requests'] = resolved_list
        connection.execute(
            'UPDATE generation_runs SET result_json=? WHERE id=?',
            (dump(result), run_id)
        )
    return get_run(db, run_id)


def search_open_score_repos(
    db: Path,
    run_id: str,
    request_id: str,
    *,
    proveedor_test: Any = None
) -> dict:
    """Busca candidatos en repositorios abiertos (requiere consentimiento explícito)."""
    from docente_ai.teaching.score_resolver import resolver_peticion_musical
    with closing(connect(db)) as connection, connection:
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute(
            'SELECT status, result_json FROM generation_runs WHERE id=?', (run_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f'Registro generativo inexistente: {run_id}.')
        status, result_json = row
        if not result_json:
            raise ValueError('El registro no contiene resultado.')
        result = json.loads(result_json)
        music_requests = result.get('music_requests', [])
        resolved_list = result.get('resolved_music_requests', [])

        req = next((r for r in music_requests if r.get('id') == request_id), None)
        if not req:
            raise ValueError(f'Petición musical inexistente: {request_id}.')

        resolved_item = next((r for r in resolved_list if r.get('request_id') == request_id), None)
        descartes = resolved_item.get('descartes', []) if resolved_item else []

        nueva_res = resolver_peticion_musical(
            req,
            con_repositorios_abiertos=True,
            descartes=descartes,
            proveedor_test=proveedor_test
        )

        if resolved_item:
            resolved_item.update(nueva_res)
        else:
            resolved_list.append(nueva_res)

        result['resolved_music_requests'] = resolved_list
        connection.execute(
            'UPDATE generation_runs SET result_json=? WHERE id=?',
            (dump(result), run_id)
        )
    return get_run(db, run_id)

