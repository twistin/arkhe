"""Ejecuciones documentadas y auditadas, sin aprobación automática."""

from contextlib import closing
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from docente_ai import __version__
from docente_ai.generation.prompt import PROMPT_VERSION, build_prompt
from docente_ai.generation.validation import validate_response
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
            raise ValueError('Una fuente ha sido excluida, reasignada o sustituida. Repite la consulta con el corpus actual.')
        if json.loads(version['metadata']) != source['metadata']:
            raise ValueError('Los metadatos de una fuente han cambiado durante la consulta.')
        chunk = connection.execute('SELECT text,locator,version_id,profile_id FROM rag_chunks WHERE id=?', (source['chunk_id'],)).fetchone()
        if not chunk or chunk['version_id'] != source['version_id'] or chunk['text'] != source['text'] or json.loads(chunk['locator']) != source['locator']:
            raise ValueError('La evidencia recuperada ya no coincide con el índice.')
        if source['version_id'] not in checked:
            verify_original(db, version)
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
    generation_request['api_key_configured'] = bool(generation_request.pop('api_key', ''))
    request = {'app_version': __version__, 'question': question, 'subject': subject, 'category': category,
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
    is_local = settings.provider == 'ollama'
    if default_generator:
        if not is_local:
            from docente_ai.llm.deepseek import DeepSeekGenerator
            generator_factory = DeepSeekGenerator
        elif pedagogy_context is not None:
            generator_factory = pedagogy.PedagogicalGenerator
    enhanced_retrieval = default_generator
    if pedagogy_context is not None:
        top_k = max(top_k, 16)
    with closing(connect(db)) as connection, connection:
        migrate(connection)
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('INSERT INTO generation_runs(id,created_at,status,request_json,prompt_version) VALUES (?,?,?,?,?)',
                           (run_id, now(), 'running', dump(request), prompt_version))
    raw, metrics = None, {}
    try:
        retrieval_started = time.monotonic()
        report = progress or (lambda message: None)
        retrieval_question = question
        if pedagogy_context is not None and pedagogy_context.get('teacher_criteria', '').strip():
            retrieval_question += '\nEnfoque indicado por el profesor: ' + pedagogy_context['teacher_criteria'].strip()
        variants = []
        if sources and enhanced_retrieval:
            from docente_ai.rag.planning import plan_queries
            report('Preparando búsqueda multilingüe')
            variants = plan_queries(retrieval_question, settings, generator_factory=generator_factory)
        programming_results = []
        if sources:
            report('Buscando pasajes en tus fuentes')
            # Cerrar el adaptador de embeddings antes de cargar el generativo.
            with embedder_factory(rag_settings) as embedder:
                retrieved = search(db, rag_settings, embedder, retrieval_question, subject=subject,
                                   category=category, document_ids=document_ids, top_k=max(top_k, 24) if variants else top_k, max_distance=max_distance, query_variants=variants)
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
            finish(db, run_id, status='abstained', result=result, metrics=metrics)
            return get_run(db, run_id)
        bundle = (build_prompt(question, retrieved['results'], settings) if pedagogy_context is None else
                  pedagogy.build_prompt(question, retrieved['results'], settings, pedagogy_context))
        report('Redactando con los pasajes seleccionados')
        record_prompt(db, run_id, bundle, settings.model, None)
        with generator_factory(settings) as generator:
            model_id = getattr(generator, 'model', settings.model)
            digest = getattr(generator, 'digest', None)
            record_prompt(db, run_id, bundle, model_id, digest)
            with closing(read_connection(db)) as connection:
                check_evidence(connection, db, bundle['evidence'], request)
            response = generator.generate(bundle['messages'])
        raw = response['content']
        metrics = {**metrics, **response['metrics'], 'estimated_input_bytes': bundle['estimated_input'], 'omitted_count': len(bundle['omitted'])}
        result = (validate_response(raw, bundle['evidence']) if pedagogy_context is None else
                  pedagogy.validate(raw, bundle['evidence'], pedagogy_context))
        finish(db, run_id, status='draft' if result['status'] == 'answered' else 'abstained',
               result=result, raw=raw, metrics=metrics, evidence=bundle['evidence'], request=request)
        return get_run(db, run_id)
    except KeyboardInterrupt:
        finish(db, run_id, status='cancelled', error='Cancelado por el usuario.', raw=raw, metrics=metrics)
        raise KeyboardInterrupt(f'Operación cancelada. Registro: {run_id}') from None
    except Exception as exc:
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
    return record


def list_runs(db: Path, limit=20):
    with closing(read_connection(db)) as connection:
        if connection.execute('PRAGMA user_version').fetchone()[0] < 4:
            return []
        return [dict(row) for row in connection.execute(
            'SELECT id,created_at,status,model,error FROM generation_runs ORDER BY created_at DESC LIMIT ?', (limit,))]


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
