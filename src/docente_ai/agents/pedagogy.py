"""Contrato del primer rol pedagógico: propuesta y base documental separadas."""

from copy import deepcopy
from datetime import date
import json
import re

from docente_ai.generation import prompt as grounded
from docente_ai.generation.validation import (
    validate_response, unique_object, fail, JsonFormatError, ExtraFieldsError, ResponseValidationError,
    check_no_musical_notation
)
from docente_ai.llm.generation import OllamaGenerator
from docente_ai.storage import read_config
from docente_ai.teaching.curriculum import show_curriculum

ValidationError = ResponseValidationError

PROMPT_VERSION = 'pedagogy:9'
SYSTEM = '''Eres un asistente pedagógico y musicológico de conservatorio y universidad. Responde en el idioma del grupo en JSON con los pasajes enviados. Las fuentes role="programming" son la programación didáctica: fijan objetivos, contenidos y evaluación; las demás documentan contenido técnico. Lagunas documentales van solo en coverage y observations de la guía docente; nunca inventes ni menciones fuentes ni autores ausentes en objetivos, student_summary ni tareas del alumno.
Estructura obligatoria JSON:
- status: "answered" (o "insufficient_sources" con claims=[], plan=null, visualizations=[], coverage=[]).
- coverage: requisitos ("R1"-"RN") con status ("cubierto", "sin_fuentes" o "parcial"), claim_ids y note. Cada claim vinculado a su requisito. Si piden cronología o autores no documentados en fuentes, declararlo expresamente aquí y en observations.
- claims: 2 a 8 bloques con kind (summary o inference), text (teoría profunda), student_summary (2 a 4 frases directas al alumno en 2ª persona sin hablar de fuentes ni 'alumnado' en 3ª persona) y evidence ([{"source_id":"S1","quote":"quote_001"}]).
- plan: objectives (2-5, orientados al aprendizaje musical; sin hablar de fuentes ni autores ausentes), difficulty, activities (2-5), resources (1-5), assessment y observations. Actividades: title, teacher_notes, student_task (2ª persona, tarea práctica activa; sin hablar de fuentes ni verbos docentes), grouping ("individual", "grupo" o "colectivo"), deliverable, solution, minutes (suman duration_minutes), claim_ids (1-based). En teacher_notes y solution, hechos sin respaldo indican "aportación del profesor pendiente". Temporización: si hay teoría nueva, reserva 15-20 min de exposición; no comprimir teoría y transcripción en 10 min.
- visualizations: 0 a 2 esquemas con type (sequence, relationship o table), title, items ([{"label":"...","detail":"..."}]), caption y evidence.
- music_requests: 0 a 4 peticiones de ejemplos musicales con id ("MR1"-"MR4"), composer, work, section, voice (o null), technique (o null), activity_title y description (qué ilustra). Prohibido terminantemente escribir código o notación musical en la respuesta (el validador la rechaza).
Devuelve solo JSON.'''

TEXT = {'type': 'string'}
STRINGS = {'type': 'array', 'items': TEXT}

ACTIVITY_SCHEMA = {
    'type': 'object',
    'properties': {
        'title': TEXT,
        'teacher_notes': TEXT,
        'student_task': TEXT,
        'grouping': {'type': 'string', 'enum': ['individual', 'grupo', 'colectivo']},
        'deliverable': TEXT,
        'solution': TEXT,
        'minutes': {'type': 'integer', 'minimum': 1},
        'claim_ids': {'type': 'array', 'items': {'type': 'integer', 'minimum': 1}}
    },
    'required': ['title', 'minutes', 'claim_ids']
}

COVERAGE_ITEM_SCHEMA = {
    'type': 'object',
    'properties': {
        'requirement_id': TEXT,
        'status': {'type': 'string', 'enum': ['cubierto', 'sin_fuentes', 'parcial']},
        'claim_ids': {'type': 'array', 'items': {'type': 'integer'}},
        'note': TEXT
    },
    'required': ['requirement_id', 'status', 'claim_ids']
}

RESPONSE_SCHEMA = deepcopy(grounded.RESPONSE_SCHEMA)
# Claims en schema generativo: text, kind, student_summary, evidence
RESPONSE_SCHEMA['properties']['claims']['items']['properties']['student_summary'] = TEXT
RESPONSE_SCHEMA['properties']['coverage'] = {
    'type': 'array',
    'items': COVERAGE_ITEM_SCHEMA
}
RESPONSE_SCHEMA['properties']['plan'] = {
    'anyOf': [
        {'type': 'null'},
        {
            'type': 'object',
            'properties': {
                'objectives': STRINGS,
                'difficulty': TEXT,
                'activities': {
                    'type': 'array',
                    'items': ACTIVITY_SCHEMA
                },
                'resources': STRINGS,
                'assessment': TEXT,
                'observations': TEXT,
            },
            'required': ['objectives', 'difficulty', 'activities', 'resources', 'assessment', 'observations'],
        }
    ]
}
RESPONSE_SCHEMA['required'].append('plan')

MUSIC_REQUEST_SCHEMA = {
    'type': 'object',
    'properties': {
        'id': TEXT,
        'composer': TEXT,
        'work': TEXT,
        'section': TEXT,
        'voice': {'anyOf': [{'type': 'string'}, {'type': 'null'}]},
        'technique': {'anyOf': [{'type': 'string'}, {'type': 'null'}]},
        'activity_title': {'anyOf': [{'type': 'string'}, {'type': 'null'}]},
        'description': TEXT,
    },
    'required': ['id', 'composer', 'work', 'section', 'description'],
}
RESPONSE_SCHEMA['properties']['music_requests'] = {
    'type': 'array',
    'items': MUSIC_REQUEST_SCHEMA,
}


class PedagogicalGenerator(OllamaGenerator):
    response_schema = RESPONSE_SCHEMA


def context_for(db, group_id, duration, *, unit_id=None, criteria='', session_date=None):
    if type(duration) is not int or not 5 <= duration <= 240:
        raise ValueError('La duración debe ser un entero entre 5 y 240 minutos.')
    if not isinstance(criteria, str) or len(criteria) > 2000:
        raise ValueError('Los criterios del profesor admiten hasta 2000 caracteres.')
    config = read_config(db)
    group = next((g for g in config['groups'] if g['id'] == group_id), None)
    if group is None:
        raise ValueError(f'Grupo inexistente: {group_id}.')
    curriculum = show_curriculum(config, group_id)
    unit = None
    if unit_id:
        unit = next((u for u in curriculum['units'] if u['id'] == unit_id), None)
        if unit is None:
            raise ValueError('La unidad no pertenece a la programación del grupo.')
    session = None
    if session_date is not None:
        from docente_ai.teaching.calendar import sessions as calendar_sessions
        day_sessions = calendar_sessions(config, session_date, session_date, group_id)
        if not day_sessions:
            raise ValueError(
                f'El grupo {group_id} no tiene sesiones previstas el {session_date.isoformat()}.'
            )
        session = day_sessions[0]
        academic_year = next(y for y in config['academic_years'] if y['id'] == group['academic_year_id'])
        course_sessions = calendar_sessions(
            config, date.fromisoformat(academic_year['start_date']),
            session_date, group_id,
        )
        sequence_number = next(i for i, item in enumerate(course_sessions, 1) if item['id'] == session['id'])
        session = {'id': session['id'], 'date': session_date.isoformat(),
                   'start': session['start'], 'duration_minutes': session['duration_minutes'],
                   'room': session['room'], 'sequence_number': sequence_number}
    from docente_ai.record.service import recent_experience
    prior = recent_experience(db, group_id, limit=3)
    return {'group': group, 'unit': unit, 'duration_minutes': duration,
            'teacher_criteria': criteria, 'prior_experience': prior or None, 'session': session}


def build_prompt(question, candidates, settings, context):
    if settings.is_remote:
        context = remote_context(context)
    requirements = context.get('requirements') or []
    def messages(sources):
        return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': grounded.compact({
            'topic': question, 'context': context,
            'sources': [
                {'source_id': s['source_id'],
                 'title': (s.get('metadata') or {}).get('title') or s.get('source_title', ''),
                 'authors': (s.get('metadata') or {}).get('authors') or s.get('authors', []),
                 'year': (s.get('metadata') or {}).get('year'),
                 'category': s['category'],
                 'origin': (s.get('metadata') or {}).get('origin', 'bibliografia'),
                 'role': ('programming' if (s.get('metadata') or {}).get('document_type') == 'programacion_didactica' else 'content'),
                 'passages': grounded.passages(s['text'])}
                for s in sources
            ]})}]
    def size(sources):
        dialogue = messages(sources)
        return grounded.estimate_input(dialogue, grounded.response_schema(dialogue, RESPONSE_SCHEMA))
    if size([]) > settings.input_budget:
        raise ValueError('El contexto pedagógico no cabe; reduce criterios o amplía num_ctx.')
    
    # Reparto equitativo entre requisitos: seleccionar el mejor pasaje por cada requisito primero
    selected, omitted, seen = [], [], set()
    req_covered = set()
    
    if requirements:
        for req in requirements:
            req_id = req.get('id')
            req_candidates = [c for c in candidates if c.get('requirement_id') == req_id]
            for candidate in req_candidates:
                if candidate['text'] in seen:
                    continue
                source = {**candidate, 'source_id': f'S{len(selected) + 1}'}
                if size([*selected, source]) <= settings.input_budget:
                    seen.add(candidate['text'])
                    selected.append(source)
                    req_covered.add(req_id)
                    break
        for req in requirements:
            req_id = req.get('id')
            if req_id not in req_covered:
                omitted.append({'requirement_id': req_id, 'reason': 'no_source_found_or_budget'})

    # Completar con el resto de candidatos hasta agotar el presupuesto
    for candidate in candidates:
        source = {**candidate, 'source_id': f'S{len(selected) + 1}'}
        reason = 'duplicate_text' if candidate['text'] in seen else 'context_budget' if size([*selected, source]) > settings.input_budget else None
        seen.add(candidate['text'])
        if reason:
            omitted_entry = {'chunk_id': candidate['chunk_id'], 'reason': reason}
            if candidate.get('requirement_id'):
                omitted_entry['requirement_id'] = candidate['requirement_id']
            omitted.append(omitted_entry)
        else:
            selected.append(source)
    if not selected:
        raise ValueError('Ningún fragmento completo cabe en el contexto pedagógico.')
    return {'messages': messages(selected), 'evidence': selected, 'omitted': omitted, 'estimated_input': size(selected)}


def remote_context(context):
    """Lista permitida: ningún registro, feedback, calendario o identificador personal."""
    group = context.get('group') or {}
    unit = context.get('unit')
    return {'group': {key: group[key] for key in ('level', 'language') if key in group},
            'duration_minutes': context.get('duration_minutes'),
            'teacher_criteria': context.get('teacher_criteria', ''),
            'requirements': context.get('requirements', []),
            'unit': {key: unit[key] for key in ('title', 'objectives', 'contents', 'competencies', 'criteria') if key in unit} if isinstance(unit, dict) else None}


def normalize_claims(claims):
    if not isinstance(claims, list):
        return claims
    normalized = []
    for c in claims:
        if isinstance(c, dict):
            item = dict(c)
            if 'type' in item and 'kind' not in item:
                k = item.pop('type')
                item['kind'] = 'summary' if k in ('summary', 'synthesis') else 'inference'
            if 'summary' in item and 'text' not in item:
                item['text'] = item.pop('summary')
            if item.get('kind') == 'synthesis':
                item['kind'] = 'summary'
            normalized.append(item)
        else:
            normalized.append(c)
    return normalized


def validate(content, evidence, context, *, retry: bool = True):
    check_no_musical_notation(content)
    try:
        data = json.loads(content, object_pairs_hook=unique_object, parse_constant=lambda _: fail('Constante JSON inválida.'))
    except (json.JSONDecodeError, RecursionError):
        raise JsonFormatError('La propuesta no es JSON válido; devuelve un objeto JSON completo.') from None
    if not isinstance(data, dict) or not {'status', 'claims', 'plan'}.issubset(set(data)):
        fail('La propuesta requiere status, claims y plan.')
    top_level_obs = data.pop('observations', None) or data.pop('reason', None) or data.pop('notes', None)
    for k in list(data.keys()):
        if k not in {'status', 'claims', 'plan', 'visualizations', 'coverage', 'music_requests'}:
            data.pop(k, None)
    if 'claims' in data:
        data['claims'] = normalize_claims(data['claims'])
    student_summaries = []
    if 'claims' in data and isinstance(data['claims'], list):
        for c in data['claims']:
            if isinstance(c, dict):
                student_summaries.append(c.pop('student_summary', None))
            else:
                student_summaries.append(None)
    grounding_payload = {k: data[k] for k in ('status', 'claims')}
    if 'visualizations' in data:
        grounding_payload['visualizations'] = data['visualizations']
    validated_grounding = validate_response(json.dumps(grounding_payload), evidence)
    data['claims'] = validated_grounding['claims']
    if 'visualizations' in validated_grounding:
        data['visualizations'] = validated_grounding['visualizations']

    plan = data.get('plan')
    if data['status'] == 'insufficient_sources':
        if plan is not None:
            fail('Una abstención no puede incluir un plan.')
        if top_level_obs:
            data['observations'] = str(top_level_obs)
        return data

    # Validar student_summary por cada claim
    THIRD_PERSON_ALUMNADO = re.compile(r'\b(?:el\s+alumnado|los\s+alumnos|las\s+alumnas|los\s+estudiantes|las\s+estudiantes)\b', re.IGNORECASE)
    SOURCE_META_TALK = re.compile(
        r'\b(?:las\s+fuentes|los\s+pasajes|la\s+biblioteca|en\s+las\s+fuentes|seg[uú]n\s+las\s+fuentes|'
        r'ausencia\s+de\s+[a-záéíóúñ\s]+\s+en\s+las\s+fuentes|falta\s+de\s+fuentes|sin\s+fuentes|'
        r'fuentes\s+no\s+(?:mencionan|documentan|aportan|disponen|desarrollan)|laguna\s+documental|'
        r'no\s+(?:hay|tenemos|se\s+dispone\s+de)\s+fuentes|pendiente\s+de\s+aportar\s+por\s+el\s+profesor)\b',
        re.IGNORECASE
    )
    for index, claim in enumerate(data['claims']):
        ss = student_summaries[index] if index < len(student_summaries) else None
        if ss is not None:
            if not isinstance(ss, str) or not 1 <= len(ss.strip()) <= 1500:
                fail(f'claims[{index}].student_summary vacío o demasiado largo (máximo 1500 caracteres).')
            if any(ord(c) < 32 and c not in '\n\r\t' for c in ss):
                fail(f'claims[{index}].student_summary contiene caracteres de control no permitidos.')
            if THIRD_PERSON_ALUMNADO.search(ss):
                fail(
                    f'claims[{index}].student_summary no debe hablar del "alumnado" o de los estudiantes en tercera persona '
                    'ni incluir instrucciones metodológicas. Explica el concepto directamente al grupo en 2 a 4 frases.'
                )
            if SOURCE_META_TALK.search(ss):
                fail(
                    f'claims[{index}].student_summary menciona fuentes o lagunas documentales. '
                    'El material del alumnado explica los conceptos directamente sin hablar de "las fuentes", '
                    '"los pasajes" ni de la ausencia de autores en la biblioteca. Esas observaciones van exclusivamente '
                    'en la guía docente (cobertura y observaciones del plan).'
                )
            claim['student_summary'] = ss.strip()

    if isinstance(plan, dict):
        if 'difficulty_reason' in plan:
            reason = plan.pop('difficulty_reason')
            if isinstance(reason, str) and reason.strip() and isinstance(plan.get('difficulty'), str):
                if reason not in plan['difficulty']:
                    plan['difficulty'] = f"{plan['difficulty']}: {reason}"[:900]
        data['plan'] = plan

    ALLOWED_PLAN_KEYS = {'objectives', 'difficulty', 'activities', 'resources', 'assessment', 'observations'}
    LEGACY_PLAN_KEYS = {'objectives', 'difficulty', 'activities', 'resources', 'observations'}
    if not isinstance(plan, dict) or set(plan) not in (ALLOWED_PLAN_KEYS, LEGACY_PLAN_KEYS):
        fail('Estructura de plan inválida.')

    def text(value, label='Texto pedagógico', max_len=3500):
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= max_len:
            fail(f'{label} vacío o demasiado largo.')
        if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
            fail('Caracteres de control no permitidos.')
        if re.search(r'https?://|\b10\.\d{4,9}/|\b(?:p|pp|pág|página|páginas)\.?\s*\d+|\[S\d+\]', value, re.I):
            fail('Las referencias se añaden por código, no en el plan.')

    for key in ('objectives', 'resources'):
        if not isinstance(plan[key], list) or not 1 <= len(plan[key]) <= 5:
            fail(f'{key} requiere entre uno y cinco elementos.')
        for item in plan[key]:
            text(item, label=f'Elemento de {key}', max_len=1500)
    for obj_idx, obj in enumerate(plan.get('objectives', [])):
        if SOURCE_META_TALK.search(obj):
            fail(
                f'plan.objectives[{obj_idx}] menciona fuentes o lagunas documentales. '
                'Los objetivos corresponden al aprendizaje musical e histórico del alumnado y no deben hablar de "las fuentes", '
                '"la biblioteca" ni de la ausencia de autores en los textos. Esas observaciones van exclusivamente '
                'en la guía docente (cobertura y observaciones del plan).'
            )
    text(plan['difficulty'], label='Dificultad', max_len=1500)
    text(plan['observations'], label='Observaciones', max_len=1500)
    if 'assessment' in plan:
        text(plan['assessment'], label='Evaluación de la sesión', max_len=1500)

    activities = plan['activities']
    if not isinstance(activities, list) or not 2 <= len(activities) <= 5:
        fail('Se necesitan entre dos y cinco actividades.')

    # JSON generado por algunos proveedores numera arrays desde 0 pese a la
    # instrucción. Se corrige solo si todo el plan es inequívocamente 0-based.
    for activity in activities:
        if not isinstance(activity, dict) or not isinstance(activity.get('claim_ids'), list):
            fail('Cada actividad necesita claim_ids como lista de índices enteros desde 1.')
        if isinstance(activity, dict) and isinstance(activity.get('claim_ids'), list):
            clean_ids = []
            for cid in activity['claim_ids']:
                if type(cid) is int:
                    clean_ids.append(cid)
                elif isinstance(cid, str) and re.fullmatch(r'(?:claim[_ -]?)?\d+', cid.strip(), re.I):
                    clean_ids.append(int(re.search(r'\d+', cid).group(0)))
                else:
                    clean_ids.append(cid)
            activity['claim_ids'] = clean_ids
    all_ids = [cid for activity in activities if isinstance(activity, dict)
               for cid in activity.get('claim_ids', [])]
    if any(cid == 0 for cid in all_ids) and all(type(cid) is int and 0 <= cid < len(data['claims']) for cid in all_ids):
        for activity in activities:
            activity['claim_ids'] = [cid + 1 for cid in activity['claim_ids']]

    TIME_RANGE_AT_END = re.compile(
        r'\s*[\(\[]\s*(?:\d+\s*(?:[-–—]|a)\s*)?\d+\s*(?:min(?:utos?)?|m|min\.)\s*[\)\]]\s*$',
        re.IGNORECASE
    )
    TEACHER_ACTION_VERBS = re.compile(
        r'^\s*(?:explicar|explicad|explica|proyectar|proyectad|proyecta|reproducir|reproducid|reproduce|dibujar|dibujad|dibuja|manejar|manejad|maneja|introducir|introducid|introduce|presentar|presentad|presenta|impartir|exponer)\b',
        re.IGNORECASE
    )

    VALID_NEW_KEYS = {'title', 'teacher_notes', 'student_task', 'grouping', 'deliverable', 'solution', 'minutes', 'claim_ids'}
    for index, activity in enumerate(activities):
        if not isinstance(activity, dict):
            fail('Actividad con estructura inválida.')
        keys = set(activity)
        is_legacy = ('instructions' in keys and 'student_task' not in keys)
        if not is_legacy and not keys.issubset(VALID_NEW_KEYS | {'instructions'}):
            fail('Actividad con campos inválidos.')
        if not is_legacy and not {'title', 'teacher_notes', 'student_task', 'grouping', 'deliverable', 'solution', 'minutes', 'claim_ids'}.issubset(keys):
            fail('Actividad incompleta en pedagogy:8: requiere title, teacher_notes, student_task, grouping, deliverable, solution, minutes y claim_ids.')
        if is_legacy:
            if not {'title', 'instructions', 'minutes', 'claim_ids'}.issubset(keys):
                fail('Actividad histórica con campos inválidos.')

        if isinstance(activity.get('title'), str):
            activity['title'] = TIME_RANGE_AT_END.sub('', activity['title']).strip()
        text(activity['title'], label=f'Título de actividad {index + 1}', max_len=200)

        if is_legacy:
            text(activity['instructions'], label=f'Instrucciones de actividad {index + 1}', max_len=2000)
        else:
            text(activity['teacher_notes'], label=f'Notas del profesor en actividad {index + 1}', max_len=2000)
            text(activity['student_task'], label=f'Consigna del estudiante en actividad {index + 1}', max_len=2000)
            text(activity['deliverable'], label=f'Entregable de actividad {index + 1}', max_len=1000)
            text(activity['solution'], label=f'Solución/criterios de actividad {index + 1}', max_len=2500)
            if activity.get('grouping') not in ('individual', 'grupo', 'colectivo'):
                fail(f'Modalidad de agrupación inválida en actividad {index + 1}; usa individual, grupo o colectivo.')
            if TEACHER_ACTION_VERBS.search(activity['student_task']):
                fail(
                    f'student_task en actividad {index + 1} no debe empezar con un verbo de acción del profesor '
                    '(explicar, proyectar, reproducir, dibujar, manejar, introducir, etc.). '
                    'Redáctala en segunda persona dirigida al alumno con una acción práctica (p. ej., "Escucha...", "Analiza...", "Compara...").'
                )
            if SOURCE_META_TALK.search(activity['student_task']):
                fail(
                    f'activities[{index}].student_task menciona fuentes o lagunas documentales. '
                    'La consigna del estudiante no debe hablar de "las fuentes", "los pasajes" ni de la ausencia de autores en la biblioteca. '
                    'Esas observaciones van exclusivamente en la guía docente (cobertura y observaciones del plan).'
                )
            if SOURCE_META_TALK.search(activity['deliverable']):
                fail(
                    f'activities[{index}].deliverable menciona fuentes o lagunas documentales. '
                    'El entregable no debe hablar de "las fuentes", "los pasajes" ni de la ausencia de autores en la biblioteca. '
                    'Esas observaciones van exclusivamente en la guía docente (cobertura y observaciones del plan).'
                )
            if SOURCE_META_TALK.search(activity['title']):
                fail(
                    f'activities[{index}].title menciona fuentes o lagunas documentales. '
                    'El título de la actividad no debe hablar de "las fuentes", "los pasajes" ni de la ausencia de autores en la biblioteca. '
                    'Esas observaciones van exclusivamente en la guía docente (cobertura y observaciones del plan).'
                )

        if type(activity['minutes']) is not int or activity['minutes'] <= 0:
            fail('Cada actividad necesita minutos enteros positivos.')
        ids = activity['claim_ids']
        if not isinstance(ids, list) or not 1 <= len(ids) <= len(data['claims']) or any(type(i) is not int or not 1 <= i <= len(data['claims']) for i in ids):
            fail('Actividad sin vínculo válido al contenido documentado.')
        if len(set(ids)) != len(ids):
            fail('Vínculos de contenido duplicados.')

    actual_total = sum(a.get('minutes', 0) for a in activities)
    expected_total = context['duration_minutes']
    if actual_total != expected_total:
        fail(f'La temporización de las actividades suma {actual_total} min y no coincide con la duración solicitada de {expected_total} min. Ajusta los minutos de cada actividad para que sumen exactamente {expected_total}.')

    # Comprobación de modalidad explícita (en pedagogy:8 la da 'grouping'; en legacy los corchetes o términos)
    has_grouping_field = all(a.get('grouping') in ('individual', 'grupo', 'colectivo') for a in activities)
    if not has_grouping_field:
        activity_texts = ' '.join(
            (a.get('title', '') + ' ' + a.get('instructions', '') + ' ' + a.get('student_task', '') + ' ' + a.get('teacher_notes', ''))
            for a in activities
        )
        has_marker = bool(re.search(
            r'\[(?:Individual|En\s+grupo|Colectivo)\]|\b(?:Individual|En\s+grupo|Colectivo)\b',
            activity_texts,
            re.IGNORECASE
        ))
        if not has_marker:
            fail(
                'El plan debe marcar la modalidad de práctica en las actividades usando '
                '[Individual], [En grupo] o [Colectivo]. Indica al menos una modalidad explícita.'
            )

    # Validar campo coverage frente a requirements
    requirements = context.get('requirements') or []
    coverage = data.get('coverage')
    is_legacy_plan = any(isinstance(a, dict) and 'instructions' in a and 'student_task' not in a for a in activities)
    if requirements and not is_legacy_plan:
        if not isinstance(coverage, list):
            fail('La propuesta requiere una lista coverage para evaluar los requisitos solicitados.')
        cov_by_id = {}
        for idx, item in enumerate(coverage):
            if not isinstance(item, dict):
                fail(f'Elemento de coverage[{idx}] inválido.')
            rid = item.get('requirement_id')
            if not isinstance(rid, str) or not rid.strip():
                fail(f'coverage[{idx}] requiere un requirement_id válido.')
            if rid in cov_by_id:
                fail(f'Requisito {rid} duplicado en coverage.')
            cov_by_id[rid] = item
            c_status = item.get('status')
            if c_status not in ('cubierto', 'sin_fuentes', 'parcial'):
                fail(f'Estado de coverage[{idx}] inválido: {c_status}; usa cubierto, sin_fuentes o parcial.')
            c_claims = item.get('claim_ids')
            if not isinstance(c_claims, list) or any(type(cid) is not int or not 1 <= cid <= len(data['claims']) for cid in c_claims):
                fail(f'coverage[{idx}].claim_ids debe ser una lista de índices de claims válidos (1 a {len(data["claims"])}).')
            if c_status == 'cubierto' and not c_claims:
                fail(f'El requisito {rid} está marcado como "cubierto" pero no enlaza ningún claim.')
            if c_status == 'sin_fuentes' and c_claims:
                fail(f'El requisito {rid} está marcado como "sin_fuentes" pero incluye claim_ids.')
            if 'note' in item and (not isinstance(item['note'], str) or len(item['note']) > 500):
                fail(f'coverage[{idx}].note debe ser texto de hasta 500 caracteres.')
        
        # Comprobar que no falte ningún requisito
        req_ids = {r['id'] for r in requirements}
        missing_reqs = req_ids - set(cov_by_id.keys())
        if missing_reqs:
            fail(f'Faltan requisitos en coverage: {", ".join(sorted(missing_reqs))}.')

        # Comprobar que no haya claims espurios (que no respondan a ningún requisito, ni a la unidad ni al tema)
        referenced_claims = {cid for item in coverage for cid in item.get('claim_ids', [])}
        unit_text = ''
        if isinstance(context.get('unit'), dict):
            u = context['unit']
            unit_text = ' '.join([str(u.get('title', '')), *u.get('objectives', []), *u.get('contents', []), *u.get('criteria', [])]).lower()
        topic_text = str(context.get('topic') or '').lower()
        context_corpus = f"{unit_text} {topic_text}"
        
        for c_idx, claim in enumerate(data['claims'], 1):
            if c_idx not in referenced_claims:
                # Comprobar si al menos responde a la unidad didáctica o al tema de la clase
                claim_words = re.findall(r'\b[A-Za-zÀ-ÿ]{4,}\b', claim.get('text', '').lower())
                matches_unit = any(w in context_corpus for w in claim_words if len(w) > 4) if context_corpus.strip() else False
                if not matches_unit:
                    fail(
                        f'El claim {c_idx} no responde a ningún requisito del profesor ni a la unidad didáctica de la programación. '
                        'Elimínalo o vincúlalo a un requisito en coverage.'
                    )

        # Comprobación determinista de omisiones en requisitos de línea temporal o autores:
        # Si un requisito pide cronología, línea temporal o autores, extrae los nombres de autores canónicos
        # que aparezcan en los pasajes de evidencia enviados al modelo. Si alguno no figura en la propuesta
        # (claims, línea temporal/visualizaciones o plan) ni en una nota de coverage que justifique su exclusión,
        # devolver a reparación con la lista concreta.
        from docente_ai.teaching.terms import find_canonical_authors_in_text
        TIMELINE_AUTHOR_KEYWORDS = re.compile(
            r'\b(?:l[ií]nea\s+de\s+tiempo|cronolog[íi]a|timeline|autores|principales\s+autores|pensadores|te[óo]ricos)\b',
            re.IGNORECASE
        )
        timeline_reqs = [
            r for r in requirements
            if TIMELINE_AUTHOR_KEYWORDS.search(r.get('description', ''))
        ]
        if timeline_reqs and evidence:
            # Extraer autores canónicos presentes en los pasajes de evidencia enviados
            all_evidence_text = ' '.join(
                s.get('text', '') or ' '.join(p.get('text', '') for p in s.get('passages', []))
                for s in evidence
            )
            canonical_in_sources = find_canonical_authors_in_text(all_evidence_text)
            if canonical_in_sources:
                # Comprobar dónde aparecen en la propuesta generada
                # 1. En el texto de claims
                claims_text = ' '.join(c.get('text', '') for c in data.get('claims', []))
                # 2. En las visualizaciones (línea temporal / esquemas)
                viz_text = ' '.join(
                    str(v.get('title', '')) + ' ' + ' '.join(str(item.get('label', '')) + ' ' + str(item.get('detail', '')) for item in v.get('items', []))
                    for v in data.get('visualizations', []) or []
                )
                # 3. En las notas de coverage para los requisitos de timeline
                cov_notes = ' '.join(
                    cov_by_id[r['id']].get('note', '')
                    for r in timeline_reqs
                    if r['id'] in cov_by_id
                )
                # 4. En observaciones generales si las hubiera
                obs_text = str(top_level_obs or '')

                proposal_coverage_corpus = f"{claims_text} {viz_text} {cov_notes} {obs_text}"
                omitted_authors = []
                for author in sorted(canonical_in_sources):
                    author_in_proposal = bool(find_canonical_authors_in_text(proposal_coverage_corpus).intersection({author}))
                    if not author_in_proposal:
                        omitted_authors.append(author)

                if omitted_authors:
                    msg = (
                        f'Autores presentes en las fuentes y no incluidos: {", ".join(omitted_authors)}. '
                        f'Deben incluirse en la línea temporal o documentarse con una nota de cobertura '
                        f'en el requisito que justifique su exclusión o falta de desarrollo.'
                    )
                    if retry:
                        fail(f'Omisión en la línea temporal / autores canónicos documentados en las fuentes: {", ".join(omitted_authors)}.')
                    else:
                        # Si tras la ronda de reparación persisten omisiones, no abortar la propuesta:
                        # marcar cobertura en estado parcial y registrar el aviso visible para la guía docente.
                        aviso = f"Autores presentes en las fuentes y no incluidos: {', '.join(omitted_authors)}"
                        for r in timeline_reqs:
                            if r['id'] in cov_by_id:
                                cov_item = cov_by_id[r['id']]
                                cov_item['status'] = 'parcial'
                                prev_note = cov_item.get('note') or ''
                                if aviso not in prev_note:
                                    cov_item['note'] = (prev_note + f' | {aviso}').strip(' |')
                        # Añadir aviso a observaciones del plan para que aparezca visible en la guía docente
                        plan = data.get('plan')
                        if isinstance(plan, dict):
                            obs_prev = plan.get('observations') or ''
                            if aviso not in obs_prev:
                                plan['observations'] = (obs_prev + f' · {aviso}').strip(' ·')

            # Si el profesor o los requisitos mencionan autores canónicos y alguno no figura en las fuentes:
            requested_authors = find_canonical_authors_in_text(
                ' '.join(r.get('description', '') for r in requirements) + ' ' + str(context.get('teacher_criteria', ''))
            )
            authors_without_sources = requested_authors - canonical_in_sources
            if authors_without_sources:
                aviso_sin_fuentes = f"Fuentes no documentan pasajes específicos para: {', '.join(sorted(authors_without_sources))}"
                for r in timeline_reqs:
                    if r['id'] in cov_by_id:
                        cov_item = cov_by_id[r['id']]
                        prev_note = cov_item.get('note') or ''
                        if aviso_sin_fuentes not in prev_note:
                            cov_item['note'] = (prev_note + f' | {aviso_sin_fuentes}').strip(' |')

    elif coverage is not None:
        if not isinstance(coverage, list):
            fail('coverage debe ser una lista.')

    if 'music_requests' in data:
        m_reqs = data['music_requests']
        if not isinstance(m_reqs, list) or len(m_reqs) > 6:
            fail('music_requests debe ser una lista con un máximo de seis peticiones.')
        valid_requests = []
        for idx, mr in enumerate(m_reqs):
            if not isinstance(mr, dict):
                fail(f'music_requests[{idx}] debe ser un objeto.')
            for req_field in ('id', 'composer', 'work', 'section', 'description'):
                val = mr.get(req_field)
                if not isinstance(val, str) or not val.strip():
                    fail(f'music_requests[{idx}].{req_field} es obligatorio y debe ser texto no vacío.')
            valid_requests.append({
                'id': str(mr['id']).strip(),
                'composer': str(mr['composer']).strip(),
                'work': str(mr['work']).strip(),
                'section': str(mr['section']).strip(),
                'voice': str(mr['voice']).strip() if mr.get('voice') else None,
                'technique': str(mr['technique']).strip() if mr.get('technique') else None,
                'activity_title': str(mr['activity_title']).strip() if mr.get('activity_title') else None,
                'description': str(mr['description']).strip(),
            })
        data['music_requests'] = valid_requests

    return data
