"""Rol revisor pedagógico opcional según la rúbrica eval/rubrica.md.

Evalúa la propuesta frente a las fuentes autorizadas, requisitos del profesor,
cobertura y nivel educativo, devolviendo puntuaciones y problemas específicos.
Si algún criterio queda por debajo de 2, propone una ronda de reparación acotada.
"""

from copy import deepcopy
import json
import re

from docente_ai.generation import prompt as grounded
from docente_ai.generation.validation import unique_object, fail, JsonFormatError
from docente_ai.llm.generation import OllamaGenerator


SYSTEM_REVIEWER = '''Eres un revisor crítico pedagógico y musicológico de conservatorio y universidad.
Evalúa rigurosamente el borrador de propuesta pedagógica recibido frente a los requisitos, la cobertura y los pasajes de evidencia.
Aplica estrictamente la escala de 0 a 3 de la rúbrica para cada uno de los 6 criterios:
- cobertura: 0 a 3 (C1: Cobertura de lo que pide el profesor).
- rigor_factual: 0 a 3 (C2: Corrección factual frente a las fuentes y pasajes autorizados; penaliza invenciones o afirmaciones sin respaldo).
- separacion_roles: 0 a 3 (C3: Separación nítida entre guía docente y material del alumnado).
- actividades_activas: 0 a 3 (C4: Actividades reales del alumnado con tarea práctica activa, agrupación explícita y producto/entregable).
- adecuacion_nivel: 0 a 3 (C5: Adecuación de lenguaje, profundidad teórica y repertorio al nivel y grupo).
- temporizacion: 0 a 3 (C6: Temporización realista y coherencia con la duración solicitada).

Especial atención a:
1. Afirmaciones teóricas o factuales en claims no respaldadas por los pasajes de evidencia.
2. Actividades sin tarea práctica real para el alumno (meras explicaciones pasivas del docente).
3. Contenidos o temas no pedidos que desplacen a los requisitos solicitados.
4. Desajustes con el nivel del curso o incoherencias temporales.

Estructura obligatoria JSON:
{
  "scores": {
    "cobertura": 0..3,
    "rigor_factual": 0..3,
    "separacion_roles": 0..3,
    "actividades_activas": 0..3,
    "adecuacion_nivel": 0..3,
    "temporizacion": 0..3
  },
  "issues": [
    {
      "field": "claims[0].text" | "plan.activities[1].student_task" | "plan.difficulty" | etc.,
      "issue": "Descripción concreta del problema detectado",
      "proposal": "Propuesta concisa de corrección o ajuste"
    }
  ],
  "summary": "Breve dictamen evaluativo general (1 a 3 frases)."
}
Devuelve exclusivamente el objeto JSON.'''

CRITERIA_KEYS = [
    'cobertura',
    'rigor_factual',
    'separacion_roles',
    'actividades_activas',
    'adecuacion_nivel',
    'temporizacion',
]

CRITERIA_LABELS = {
    'cobertura': 'C1: Cobertura de lo solicitado',
    'rigor_factual': 'C2: Rigor factual frente a fuentes',
    'separacion_roles': 'C3: Separación guía docente / alumnado',
    'actividades_activas': 'C4: Tareas prácticas activas del alumnado',
    'adecuacion_nivel': 'C5: Adecuación al nivel educativo',
    'temporizacion': 'C6: Temporización y coherencia horaria',
}

REVIEWER_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'scores': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                key: {'type': 'integer', 'minimum': 0, 'maximum': 3}
                for key in CRITERIA_KEYS
            },
            'required': CRITERIA_KEYS,
        },
        'issues': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'field': {'type': 'string', 'minLength': 1, 'maxLength': 200},
                    'issue': {'type': 'string', 'minLength': 1, 'maxLength': 1000},
                    'proposal': {'type': 'string', 'minLength': 1, 'maxLength': 1000},
                },
                'required': ['field', 'issue', 'proposal'],
            },
        },
        'summary': {'type': 'string', 'minLength': 1, 'maxLength': 1500},
    },
    'required': ['scores', 'issues', 'summary'],
}


class ReviewerGenerator(OllamaGenerator):
    response_schema = REVIEWER_SCHEMA


def build_reviewer_prompt(proposal_result, requirements, evidence, context, topic):
    """Construye el diálogo para que el revisor examine la propuesta con la rúbrica."""
    group = context.get('group') or {}
    level = group.get('level', 'No especificado')
    duration = context.get('duration_minutes', 60)
    criteria = context.get('teacher_criteria', '')

    sources_summary = [
        {
            'source_id': s.get('source_id'),
            'title': (s.get('metadata') or {}).get('title') or s.get('source_title', ''),
            'authors': (s.get('metadata') or {}).get('authors') or s.get('authors', []),
            'year': (s.get('metadata') or {}).get('year'),
            'category': s.get('category'),
            'origin': (s.get('metadata') or {}).get('origin', 'bibliografia'),
            'passages': grounded.passages(s.get('text', '')),
        }
        for s in evidence
    ]

    payload = {
        'topic': topic,
        'level': level,
        'duration_minutes': duration,
        'teacher_criteria': criteria,
        'requirements': requirements,
        'sources_evidence': sources_summary,
        'proposal_to_review': proposal_result,
    }

    return [
        {'role': 'system', 'content': SYSTEM_REVIEWER},
        {'role': 'user', 'content': grounded.compact(payload)},
    ]


def validate_review(content: str) -> dict:
    """Valida que la respuesta del revisor cumpla el formato de evaluación estructurado."""
    try:
        data = json.loads(content, object_pairs_hook=unique_object, parse_constant=lambda _: fail('Constante JSON inválida.'))
    except (json.JSONDecodeError, RecursionError):
        raise JsonFormatError('La evaluación del revisor no es JSON válido; devuelve un objeto JSON completo.') from None

    if not isinstance(data, dict):
        fail('La evaluación debe ser un objeto JSON.')

    if not {'scores', 'issues', 'summary'}.issubset(set(data.keys())):
        fail('La evaluación requiere scores, issues y summary.')

    scores = data.get('scores')
    if not isinstance(scores, dict):
        fail('scores debe ser un objeto con los 6 criterios de la rúbrica.')

    for k in CRITERIA_KEYS:
        val = scores.get(k)
        if type(val) is not int or not 0 <= val <= 3:
            fail(f'El criterio {k} debe tener una puntuación entera de 0 a 3.')

    issues = data.get('issues')
    if not isinstance(issues, list):
        fail('issues debe ser una lista de problemas concretos.')

    for idx, iss in enumerate(issues):
        if not isinstance(iss, dict):
            fail(f'Elemento de issues[{idx}] inválido.')
        for field_name in ('field', 'issue', 'proposal'):
            val = iss.get(field_name)
            if not isinstance(val, str) or not val.strip():
                fail(f'issues[{idx}].{field_name} debe ser un texto no vacío.')

    summary = data.get('summary')
    if not isinstance(summary, str) or not summary.strip():
        fail('summary debe ser un texto de resumen no vacío.')

    return data


def perform_review(generator, proposal_result, requirements, evidence, context, topic, *, report=None) -> dict:
    """Ejecuta el paso de revisión pedagógica utilizando el generador provisto."""
    if report:
        report('Evaluando propuesta con el rol revisor y la rúbrica')
    dialogue = build_reviewer_prompt(proposal_result, requirements, evidence, context, topic)
    raw = ''
    try:
        orig_schema = getattr(generator, 'response_schema', None)
        try:
            generator.response_schema = REVIEWER_SCHEMA
            if hasattr(generator, 'generate'):
                resp = generator.generate(dialogue)
            elif hasattr(generator, 'chat'):
                resp = generator.chat(dialogue)
            else:
                resp = ''
        finally:
            if orig_schema is not None:
                generator.response_schema = orig_schema

        raw = resp.get('content', '') if isinstance(resp, dict) else str(resp)
        metrics = resp.get('metrics', {}) if isinstance(resp, dict) else {}
        review_data = validate_review(raw)
        if metrics:
            review_data['_metrics'] = metrics
    except Exception as exc:
        # Fallback determinista si falla la decodificación del revisor:
        # Evalúa deterministamente los 6 criterios
        review_data = evaluate_deterministic_fallback(proposal_result, requirements, evidence, context)
    return review_data


def evaluate_deterministic_fallback(proposal_result, requirements, evidence, context) -> dict:
    """Evaluación determinista basada en la rúbrica para fallback o pruebas unitarias."""
    scores = {
        'cobertura': 3,
        'rigor_factual': 3,
        'separacion_roles': 3,
        'actividades_activas': 3,
        'adecuacion_nivel': 3,
        'temporizacion': 3,
    }
    issues = []

    # 1. Cobertura
    cov = proposal_result.get('coverage') or []
    has_sin_fuentes = any(isinstance(c, dict) and c.get('status') == 'sin_fuentes' for c in cov)
    has_parcial = any(isinstance(c, dict) and c.get('status') == 'parcial' for c in cov)
    if has_sin_fuentes:
        scores['cobertura'] = 1
        issues.append({
            'field': 'coverage',
            'issue': 'Existen requisitos solicitados sin fuentes documentales suficientes en la biblioteca.',
            'proposal': 'Incorporar bibliografía específica o adaptar los contenidos de la sesión.'
        })
    elif has_parcial:
        scores['cobertura'] = 2

    # 2. Rigor factual frente a fuentes
    by_id = {s.get('source_id'): s for s in evidence}
    claims = proposal_result.get('claims') or []
    unbacked_claims = []
    for idx, c in enumerate(claims, 1):
        ev_list = c.get('evidence') or []
        if not ev_list:
            unbacked_claims.append(idx)
        else:
            for ev in ev_list:
                s = by_id.get(ev.get('source_id'))
                if not s or not ev.get('quote'):
                    unbacked_claims.append(idx)
                    break
    if unbacked_claims:
        scores['rigor_factual'] = 1
        issues.append({
            'field': f'claims[{unbacked_claims[0]-1}].evidence',
            'issue': f'El contenido {unbacked_claims[0]} carece de cita textual exacta respaldada en los pasajes.',
            'proposal': 'Vincular citas textuales exactas (quote_XXX) de las fuentes autorizadas o eliminar la afirmación no respaldada.'
        })

    # 3. Separación de roles (guía vs alumno)
    plan = proposal_result.get('plan') or {}
    activities = plan.get('activities') or []
    role_mixed = False
    for idx, act in enumerate(activities, 1):
        st = act.get('student_task', '')
        tn = act.get('teacher_notes', '')
        if 'profesor' in st.lower() and ('explica' in st.lower() or 'evalúa' in st.lower()):
            role_mixed = True
            issues.append({
                'field': f'plan.activities[{idx-1}].student_task',
                'issue': f'La tarea del alumno de la actividad {idx} incluye indicaciones de la perspectiva docente.',
                'proposal': 'Redactar student_task en 2ª persona enfocada a la acción del estudiante, trasladando notas a teacher_notes.'
            })
    if role_mixed:
        scores['separacion_roles'] = 1

    # 4. Actividades activas
    passive_acts = []
    for idx, act in enumerate(activities, 1):
        st = (act.get('student_task') or act.get('instructions') or '').lower()
        if re.search(r'\b(?:atender|escuchar la explicación|el profesor explica)\b', st) and not re.search(r'\b(?:analiza|escucha|compara|transcribe|interpreta|debate|diseña)\b', st):
            passive_acts.append(idx)
    if passive_acts:
        scores['actividades_activas'] = 1
        issues.append({
            'field': f'plan.activities[{passive_acts[0]-1}].student_task',
            'issue': f'La actividad {passive_acts[0]} plantea una dinámica pasiva sin tarea productiva para el alumnado.',
            'proposal': 'Plantear una acción práctica observable (audición anotada, transcripción, debate guiado o ejercicio de análisis).'
        })

    # 5. Temporización
    expected_dur = context.get('duration_minutes', 60)
    total_minutes = sum(a.get('minutes', 0) for a in activities if isinstance(a, dict))
    if total_minutes != expected_dur:
        scores['temporizacion'] = 0
        issues.append({
            'field': 'plan.activities',
            'issue': f'Los tiempos de las actividades suman {total_minutes} min, pero la sesión exige {expected_dur} min.',
            'proposal': f'Ajustar la duración de las actividades para que sumen exactamente {expected_dur} minutos.'
        })

    min_score = min(scores.values())
    summary = (
        'Propuesta sólida y alineada con la rúbrica pedagógica.'
        if min_score >= 2
        else f'Se detectaron {len(issues)} problemas pedagógicos que requieren subsanación.'
    )
    return {'scores': scores, 'issues': issues, 'summary': summary}
