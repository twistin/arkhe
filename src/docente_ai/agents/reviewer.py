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
Evalúa rigurosamente el borrador de propuesta pedagógica recibido y su material del alumnado renderizado frente a los requisitos, la cobertura y los pasajes de evidencia.
Aplica estrictamente la escala de 0 a 3 de la rúbrica (eval/rubrica.md) para cada uno de los 6 criterios:
- cobertura: 0 a 3 (C1: Cobertura de lo que pide el profesor).
  * 0 si omite peticiones centrales o desvía el tema.
  * 1 si es superficial o falta la mitad sin declarar en coverage.
  * 2 si cubre la mayoría y declara honestamente sin_fuentes/parcial lo no respaldado.
  * 3 si aborda exhaustivamente todos los puntos requeridos.
- rigor_factual: 0 a 3 (C2: Corrección factual frente a las fuentes y pasajes autorizados; penaliza invenciones o afirmaciones sin respaldo).
  * 0 si inventa datos históricos o musicológicos graves o citas inexistentes.
  * 1 si contiene imprecisiones teóricas, afirmaciones sin respaldo en fuentes no marcadas como "aportación del profesor pendiente" o citas discrepantes.
  * 2 si los hechos son correctos y concuerdan con el corpus, marcando aportaciones docentes pendientes.
  * 3 si la precisión técnica, notacional y teórica es sobresaliente con citas textuales exactas verificables.
- separacion_roles: 0 a 3 (C3: Separación nítida entre guía docente y material del alumnado).
  * 0 si el material del alumnado contiene instrucciones, consignas o notas dirigidas al profesor (ej. "Explicar...", "Proyectar...", "Reproducir...", "Apertura metodológica...", notas docentes o soluciones).
  * 1 si habla del alumnado en tercera persona ("Pedir al alumnado que anote...") o incluye jerga metodológica docente en el cuaderno del alumno.
  * 2 si el alumno recibe explicaciones en 2ª persona sin notas del profesor.
  * 3 si la separación es modélica: guía docente completa y cuaderno del alumno limpio de directrices pedagógicas internas.
- actividades_activas: 0 a 3 (C4: Actividades reales del alumnado con tarea práctica activa, agrupación explícita y producto/entregable).
  * 0 si son pasivas (el alumno es mero oyente) o la tarea describe lo que hace el profesor ("El profesor explica..."), o exige materiales ausentes no marcados como pendientes.
  * 1 si la tarea es ambigua sin entregable claro ("Comprender y debatir") o sin modalidad de agrupación.
  * 2 si el alumno realiza acción práctica concreta (audición anotada, tabla, análisis), con agrupación explícita y entregable.
  * 3 si el diseño activo es excelente con consignas en 2ª persona ("Analiza...", "Compara..."), alternancia de agrupamientos y producto tangible.
- adecuacion_nivel: 0 a 3 (C5: Adecuación de lenguaje, profundidad teórica y repertorio al nivel y grupo).
  * 0 si hay desajuste radical (infantil o nivel tesis inasumible).
  * 1 si el nivel es irregular sin andamiaje pedagógico.
  * 2 si el nivel y vocabulario son adecuados al curso de conservatorio.
  * 3 si equilibra perfectamente el rigor técnico con la claridad y madurez del curso.
- temporizacion: 0 a 3 (C6: Temporización realista y coherencia con la duración solicitada).
  * 0 si los minutos no suman exactamente la duración de la sesión o la distribución es inverosímil.
  * 1 si la suma cuadra pero no reserva tiempo de exposición docente para teoría nueva o asigna tiempos irreales.
  * 2 si la temporización es viable y equilibrada para apertura, desarrollo y síntesis.
  * 3 si la calibración de ritmos, audiciones y análisis es ejemplar.

REGLAS OBLIGATORIAS DE EVALUACIÓN:
1. Revisa detenidamente el campo "student_material_markdown". Si encuentras instrucciones al docente ("Explicar", "Proyectar", "Reproducir", "Apertura metodológica", etc.), la nota de separacion_roles NO puede ser superior a 0 o 1.
2. Cada puntuación debe justificarse con una cita literal entrecomillada de la propuesta o del material del alumnado ("...").
3. NO puedes asignar la misma nota a los seis criterios (ej. todo 2 o todo 3) a menos que justifiques expresamente por qué ninguno de los criterios destaca positiva ni negativamente frente a los demás.
4. En teacher_notes y solution: afirmaciones fácticas concretas que no estén respaldadas en claim_ids ni marcadas como "aportación del profesor pendiente" penalizan en rigor_factual.
5. Actividades no ejecutables: si se requiere un material no disponible ni marcado como pendiente, penalizan en actividades_activas.

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
  "justifications": {
    "cobertura": "Justificación con cita literal de la propuesta respaldando la nota",
    "rigor_factual": "Justificación con cita literal de la propuesta respaldando la nota",
    "separacion_roles": "Justificación con cita literal de la propuesta o material de alumno respaldando la nota",
    "actividades_activas": "Justificación con cita literal de la propuesta respaldando la nota",
    "adecuacion_nivel": "Justificación con cita literal de la propuesta respaldando la nota",
    "temporizacion": "Justificación con cita literal de la propuesta respaldando la nota"
  },
  "issues": [
    {
      "field": "claims[0].text" | "plan.activities[1].student_task" | "student_material" | "plan.difficulty" | etc.,
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
        'justifications': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                key: {'type': 'string', 'minLength': 5, 'maxLength': 1500}
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
    'required': ['scores', 'justifications', 'issues', 'summary'],
}


class ReviewerGenerator(OllamaGenerator):
    response_schema = REVIEWER_SCHEMA


def build_reviewer_prompt(proposal_result, requirements, evidence, context, topic):
    """Construye el diálogo para que el revisor examine la propuesta con la rúbrica."""
    from docente_ai.generation.render import render_student
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

    # Renderizamos el material del alumnado para que el revisor examine la salida real
    try:
        student_rendered = render_student({
            'result': proposal_result,
            'evidence': evidence,
            'request': {'pedagogy': context, 'question': topic}
        })
    except Exception:
        student_rendered = ''

    payload = {
        'topic': topic,
        'level': level,
        'duration_minutes': duration,
        'teacher_criteria': criteria,
        'requirements': requirements,
        'sources_evidence': sources_summary,
        'proposal_to_review': proposal_result,
        'student_material_markdown': student_rendered,
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

    # Validar justificaciones (o generar a partir de summary e issues si vienen ausentes por compatibilidad)
    justifications = data.get('justifications')
    if justifications is None:
        justifications = {k: f"Puntuación {scores[k]}/3 evaluada conforme a la rúbrica." for k in CRITERIA_KEYS}
        data['justifications'] = justifications
    elif not isinstance(justifications, dict):
        fail('justifications debe ser un objeto con las justificaciones de cada criterio.')

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
    from docente_ai.generation.render import render_student
    scores = {
        'cobertura': 3,
        'rigor_factual': 3,
        'separacion_roles': 3,
        'actividades_activas': 3,
        'adecuacion_nivel': 3,
        'temporizacion': 3,
    }
    justifications = {}
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
        justifications['cobertura'] = 'Puntuación 1: Se registran requisitos como "sin_fuentes" en la cobertura declarada.'
    elif has_parcial:
        scores['cobertura'] = 2
        justifications['cobertura'] = 'Puntuación 2: Se cubren los requisitos principales con algunos aspectos en estado parcial.'
    else:
        justifications['cobertura'] = 'Puntuación 3: Todos los requisitos solicitados quedan respaldados por las fuentes documentales.'

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
        justifications['rigor_factual'] = f'Puntuación 1: Contenido {unbacked_claims[0]} carece de cita textual exacta respaldada en pasajes autorizados.'

    # 2b. Hechos en teacher_notes / solution sin respaldo ni marca de aportación pendiente
    plan = proposal_result.get('plan') or {}
    activities = plan.get('activities') or []
    fact_regex = re.compile(r'\b(?:\d{3,4}\s*(?:a\.\s*C\.|d\.\s*C\.)?|siglo\s+[IVXLCDM]+|«[^»]+»|"[^"]+")\b', re.IGNORECASE)
    for idx, act in enumerate(activities, 1):
        tn = act.get('teacher_notes', '')
        sol = act.get('solution', '')
        combined = f"{tn} {sol}"
        has_facts = fact_regex.search(combined)
        is_pending = 'aportación del profesor pendiente' in combined.lower() or 'pendiente de aportar por el profesor' in combined.lower()
        if has_facts and not is_pending and not act.get('claim_ids'):
            scores['rigor_factual'] = min(scores['rigor_factual'], 2)
            issues.append({
                'field': f'plan.activities[{idx-1}].teacher_notes',
                'issue': f'La actividad {idx} contiene hechos o citas en notas/solución sin respaldo en claim_ids ni indicación de aportación pendiente.',
                'proposal': 'Vincular claim_ids que los respalden o marcar explícitamente como "aportación del profesor pendiente".'
            })
            justifications['rigor_factual'] = f'Puntuación 2: Actividad {idx} incluye datos factuales en notas/solución sin claim_ids respaldados ni marca de aportación pendiente.'
            break
    if 'rigor_factual' not in justifications:
        justifications['rigor_factual'] = 'Puntuación 3: Afirmaciones y contenidos fundamentados con rigor y citas documentales verificables.'

    # Renderizado del material del alumno para verificar posibles filtraciones docentes
    try:
        student_md = render_student({
            'result': proposal_result,
            'evidence': evidence,
            'request': {'pedagogy': context, 'question': context.get('topic', '')}
        })
    except Exception:
        student_md = ''

    # 3. Separación de roles (guía vs alumno)
    # Anclas de rúbrica:
    # 0 si el material del alumno contiene consignas directas al profesor ("Explicar...", "Proyectar...", "Reproducir...", etc.)
    # 1 si habla del alumnado en 3ª persona o incluye jerga metodológica
    teacher_instr_regex = re.compile(r'\b(?:explicar|proyectar|reproducir|apertura metodol[oó]gica)\b', re.IGNORECASE)
    teacher_matches = list(teacher_instr_regex.finditer(student_md))
    third_person_matches = list(re.finditer(r'\b(?:el alumnado|al alumnado|pedir al alumnado)\b', student_md, re.IGNORECASE))

    role_mixed = False
    for idx, act in enumerate(activities, 1):
        st = act.get('student_task', '')
        if 'profesor' in st.lower() and ('explica' in st.lower() or 'evalúa' in st.lower()):
            role_mixed = True
            break

    if teacher_matches:
        scores['separacion_roles'] = 0
        leak_snippet = teacher_matches[0].group(0)
        issues.append({
            'field': 'student_material',
            'issue': f'El material del alumnado contiene consignas directas dirigidas al profesor ("{leak_snippet}").',
            'proposal': 'Eliminar directrices docentes del cuaderno del estudiante y mantenerlas únicamente en la guía del profesor.'
        })
        justifications['separacion_roles'] = f'Puntuación 0: Filtración de consignas docentes ("{leak_snippet}") en el material del alumnado renderizado.'
    elif third_person_matches or role_mixed:
        scores['separacion_roles'] = 1
        issues.append({
            'field': 'student_material',
            'issue': 'El material del alumnado habla de los estudiantes en tercera persona ("el alumnado") o mezcla perspectivas.',
            'proposal': 'Redactar en 2ª persona directa al estudiante sin hablar de él en 3ª persona.'
        })
        justifications['separacion_roles'] = 'Puntuación 1: El material del estudiante utiliza la tercera persona ("el alumnado") en vez de dirigirse directamente a él.'
    else:
        justifications['separacion_roles'] = 'Puntuación 3: Separación nítida entre guía didáctica del profesor y cuaderno autónomo del alumno.'

    # 4. Actividades activas
    # Anclas de rúbrica:
    # 0 si son pasivas (el profesor hace la acción: "Explicar...", "Proyectar...", "Reproducir...") o mero oyente
    # 1 si la tarea no tiene entregable claro o no define modalidad de agrupación
    teacher_action_acts = []
    passive_acts = []
    missing_grouping_acts = []
    for idx, act in enumerate(activities, 1):
        st = (act.get('student_task') or act.get('instructions') or '').strip()
        if re.match(r'^\s*(?:explicar|proyectar|reproducir|manejar)\b', st, re.IGNORECASE):
            teacher_action_acts.append((idx, st[:50]))
        elif re.search(r'\b(?:atender|escuchar la explicación|el profesor explica)\b', st, re.IGNORECASE) and not re.search(r'\b(?:analiza|escucha|compara|transcribe|interpreta|debate|diseña)\b', st, re.IGNORECASE):
            passive_acts.append(idx)
        if not act.get('grouping'):
            missing_grouping_acts.append(idx)

    if len(teacher_action_acts) >= 2 or len(teacher_action_acts) >= len(activities) / 2:
        scores['actividades_activas'] = 0
        issues.append({
            'field': f'plan.activities[{teacher_action_acts[0][0]-1}].student_task',
            'issue': f'Las actividades describen la acción docente en lugar de tareas prácticas para el estudiante ("{teacher_action_acts[0][1]}...").',
            'proposal': 'Rediseñar las actividades con acciones prácticas de aprendizaje activo ejecutables por el alumno en 2ª persona.'
        })
        justifications['actividades_activas'] = f'Puntuación 0: La mayoría de tareas describen la acción del profesor ("{teacher_action_acts[0][1]}...") en vez de trabajo práctico del alumno.'
    elif teacher_action_acts or passive_acts or missing_grouping_acts:
        scores['actividades_activas'] = 1
        bad_idx = teacher_action_acts[0][0] if teacher_action_acts else (passive_acts[0] if passive_acts else missing_grouping_acts[0])
        issues.append({
            'field': f'plan.activities[{bad_idx-1}].student_task',
            'issue': f'La actividad {bad_idx} carece de tarea práctica activa, producto claro o modalidad explícita de agrupación.',
            'proposal': 'Asignar acción observable (audición anotada, análisis, debate), agrupación explícita y producto entregable.'
        })
        justifications['actividades_activas'] = f'Puntuación 1: Falta de agrupación explícita o formulación pasiva en la actividad {bad_idx}.'
    else:
        justifications['actividades_activas'] = 'Puntuación 3: Tareas activas bien definidas en 2ª persona con entregables y agrupamiento explícito.'

    # 5. Adecuación de nivel
    level_diff = plan.get('difficulty', '')
    if not level_diff:
        scores['adecuacion_nivel'] = 2
        justifications['adecuacion_nivel'] = 'Puntuación 2: Nivel adecuado de conservatorio profesional sin justificación curricular detallada.'
    else:
        scores['adecuacion_nivel'] = 3
        justifications['adecuacion_nivel'] = f'Puntuación 3: Nivel pedagógico adaptado ("{level_diff[:60]}...").'

    # 6. Temporización
    expected_dur = context.get('duration_minutes', 60)
    total_minutes = sum(a.get('minutes', 0) for a in activities if isinstance(a, dict))
    if total_minutes != expected_dur:
        scores['temporizacion'] = 0
        issues.append({
            'field': 'plan.activities',
            'issue': f'Los tiempos de las actividades suman {total_minutes} min, pero la sesión exige {expected_dur} min.',
            'proposal': f'Ajustar la duración de las actividades para que sumen exactamente {expected_dur} minutos.'
        })
        justifications['temporizacion'] = f'Puntuación 0: La suma de minutos ({total_minutes} min) no coincide con la duración programada ({expected_dur} min).'
    else:
        justifications['temporizacion'] = f'Puntuación 3: Temporización exacta y equilibrada que suma exactamente {expected_dur} minutos.'

    min_score = min(scores.values())
    summary = (
        'Propuesta sólida y alineada con la rúbrica pedagógica.'
        if min_score >= 2
        else f'Se detectaron {len(issues)} problemas pedagógicos que requieren subsanación según la rúbrica.'
    )
    return {'scores': scores, 'justifications': justifications, 'issues': issues, 'summary': summary}
