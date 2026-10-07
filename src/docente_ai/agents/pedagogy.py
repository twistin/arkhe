"""Contrato del primer rol pedagógico: propuesta y base documental separadas."""

from copy import deepcopy
from datetime import date
import json
import re

from docente_ai.generation import prompt as grounded
from docente_ai.generation.validation import validate_response, unique_object, fail, JsonFormatError, ExtraFieldsError
from docente_ai.llm.generation import OllamaGenerator
from docente_ai.storage import read_config
from docente_ai.teaching.curriculum import show_curriculum

PROMPT_VERSION = 'pedagogy:7'
SYSTEM = '''Eres un asistente pedagógico y musicológico de conservatorio y universidad. Responde en el idioma del grupo en JSON y usa solo los pasajes enviados. Cada fuente incluye su autor, título, año y tipo. Los criterios del profesor orientan la búsqueda y las actividades, pero no son evidencia factual. Las fuentes con role="programming" son la programación didáctica de la materia: sus pasajes determinan objetivos, contenidos, secuencia, temporalización y evaluación de la propuesta. Las demás fuentes documentan el contenido técnico o académico. Si ambos papeles entran en conflicto, indícalo en observations. Si un autor, obra o técnica solicitada no aparece en absoluto en las fuentes disponibles, indícalo en observations y no inventes contenido no respaldado.
Estructura obligatoria JSON:
- status: "answered" (o "insufficient_sources" con claims=[], plan=null, visualizations=[]).
- claims: 2 a 8 bloques con kind (summary o inference), text y evidence. Desarrolla en text la explicación teórica que el profesor necesita para impartir la sesión: definición, funcionamiento, relaciones entre elementos, contexto histórico, formas y técnicas relevantes presentes en las fuentes. Evita simples titulares o frases sueltas. evidence es una lista de objetos {"source_id":"S1","quote":"quote_001"}; nunca uses citas libres.
- plan: objectives (2-5), difficulty, activities (2-5), resources (1-5) y observations. Cada actividad lleva title, instructions, minutes y claim_ids. claim_ids usa índices desde 1: el primer claim es 1, nunca 0. Los minutos suman exactamente duration_minutes. Incluye práctica [Individual], [En grupo] o [Colectivo]. No presupongas partituras, grabaciones o ejemplos concretos no presentes entre las fuentes.
- visualizations: 0 a 2 esquemas con type (sequence, relationship o table), title, items [{"label":"...","detail":"..."}], caption y evidence con source_id y quote_XXX. No uses data, rows, steps, Mermaid ni HTML.
Cada claim debe tener entre 1 y 30 evidencias verificables. No incluyas claims con evidence vacío ni uses los criterios del profesor como citas. Las actividades originales pertenecen al plan, separadas de la explicación documental. Omite contenido solicitado que no tenga respaldo e indica esa limitación en plan.observations.
Devuelve solo JSON.'''



TEXT = {'type': 'string', 'minLength': 1, 'maxLength': 1000}
STRINGS = {'type': 'array', 'minItems': 1, 'maxItems': 5, 'items': TEXT}
RESPONSE_SCHEMA = deepcopy(grounded.RESPONSE_SCHEMA)
RESPONSE_SCHEMA['properties']['plan'] = {
    'anyOf': [{'type': 'null'}, {
        'type': 'object', 'additionalProperties': False,
        'properties': {
            'objectives': STRINGS,
            'difficulty': TEXT,
            'activities': {'type': 'array', 'minItems': 2, 'maxItems': 5, 'items': {
                'type': 'object', 'additionalProperties': False,
                'properties': {'title': TEXT, 'instructions': TEXT,
                               'minutes': {'type': 'integer', 'minimum': 1},
                               'claim_ids': {'type': 'array', 'minItems': 1, 'maxItems': 12,
                                             'items': {'type': 'integer', 'minimum': 1, 'maximum': 12}}},
                'required': ['title', 'instructions', 'minutes', 'claim_ids']}},
            'resources': STRINGS, 'observations': TEXT,
        }, 'required': ['objectives', 'difficulty', 'activities', 'resources', 'observations'],
    }]
}
RESPONSE_SCHEMA['required'].append('plan')


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
    def messages(sources):
        return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': grounded.compact({
            'topic': question, 'context': context,
            'sources': [
                {'source_id': s['source_id'],
                 'title': (s.get('metadata') or {}).get('title') or s.get('source_title', ''),
                 'authors': (s.get('metadata') or {}).get('authors') or s.get('authors', []),
                 'year': (s.get('metadata') or {}).get('year'),
                 'category': s['category'],
                 'role': ('programming' if (s.get('metadata') or {}).get('document_type') == 'programacion_didactica' else 'content'),
                 'passages': grounded.passages(s['text'])}
                for s in sources
            ]})}]
    def size(sources):
        dialogue = messages(sources)
        return grounded.estimate_input(dialogue, grounded.response_schema(dialogue, RESPONSE_SCHEMA))
    if size([]) > settings.input_budget:
        raise ValueError('El contexto pedagógico no cabe; reduce criterios o amplía num_ctx.')
    selected, omitted, seen = [], [], set()
    for candidate in candidates:
        source = {**candidate, 'source_id': f'S{len(selected) + 1}'}
        reason = 'duplicate_text' if candidate['text'] in seen else 'context_budget' if size([*selected, source]) > settings.input_budget else None
        seen.add(candidate['text'])
        if reason:
            omitted.append({'chunk_id': candidate['chunk_id'], 'reason': reason})
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


def validate(content, evidence, context):
    try:
        data = json.loads(content, object_pairs_hook=unique_object, parse_constant=lambda _: fail('Constante JSON inválida.'))
    except (json.JSONDecodeError, RecursionError):
        raise JsonFormatError('La propuesta no es JSON válido; devuelve un objeto JSON completo.') from None
    if not isinstance(data, dict) or not {'status', 'claims', 'plan'}.issubset(set(data)):
        fail('La propuesta requiere status, claims y plan.')
    top_level_obs = data.pop('observations', None) or data.pop('reason', None) or data.pop('notes', None)
    for k in list(data.keys()):
        if k not in {'status', 'claims', 'plan', 'visualizations'}:
            data.pop(k, None)
    if 'claims' in data:
        data['claims'] = normalize_claims(data['claims'])
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
    if isinstance(plan, dict):
        if 'difficulty_reason' in plan:
            reason = plan.pop('difficulty_reason')
            if isinstance(reason, str) and reason.strip() and isinstance(plan.get('difficulty'), str):
                if reason not in plan['difficulty']:
                    plan['difficulty'] = f"{plan['difficulty']}: {reason}"[:900]
        data['plan'] = plan
    if not isinstance(plan, dict) or set(plan) != {'objectives', 'difficulty', 'activities', 'resources', 'observations'}:
        fail('Estructura de plan inválida.')
    def text(value):
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 1000:
            fail('Texto pedagógico vacío o demasiado largo.')
        if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
            fail('Caracteres de control no permitidos.')
        if re.search(r'https?://|\b10\.\d{4,9}/|\b(?:p|pp|pág|página|páginas)\.?\s*\d+|\[S\d+\]', value, re.I):
            fail('Las referencias se añaden por código, no en el plan.')
    for key in ('objectives', 'resources'):
        if not isinstance(plan[key], list) or not 1 <= len(plan[key]) <= 5:
            fail(f'{key} requiere entre uno y cinco elementos.')
        for item in plan[key]:
            text(item)
    text(plan['difficulty'])
    text(plan['observations'])
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
    for activity in activities:
        if not isinstance(activity, dict) or set(activity) != {'title', 'instructions', 'minutes', 'claim_ids'}:
            fail('Actividad con campos inválidos.')
        text(activity['title'])
        text(activity['instructions'])
        if type(activity['minutes']) is not int or activity['minutes'] <= 0:
            fail('Cada actividad necesita minutos enteros positivos.')
        ids = activity['claim_ids']
        if not isinstance(ids, list) or not 1 <= len(ids) <= len(data['claims']) or any(type(i) is not int or not 1 <= i <= len(data['claims']) for i in ids):
            fail('Actividad sin vínculo válido al contenido documentado.')
        if len(set(ids)) != len(ids):
            fail('Vínculos de contenido duplicados.')
    if sum(a['minutes'] for a in activities) != context['duration_minutes']:
        fail('La temporización no coincide con la duración solicitada.')

    return data
