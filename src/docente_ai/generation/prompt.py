"""Contrato de respuesta y selección de evidencia dentro del presupuesto."""

import json
from copy import deepcopy
from docente_ai.generation.quotations import passages

PROMPT_VERSION = 'grounded-answer:6'
SYSTEM = """Eres un asistente académico de conservatorio y universidad. Responde con rigor basándote solo en los pasajes dados. Redacta explicaciones amplias, profundas y articuladas en prosa continua (evita fragmentar en pocas líneas); desarrolla contexto histórico, técnica y análisis musical formal. Usa títulos Markdown (###), listas y tablas comparativas cuando proceda.
Cada claim es una sección temática con kind (summary o inference), text y evidence ([{"source_id":"S1","quote":"quote_001"}]).
Si la pregunta analiza formas musicales, evolución o taxonomía, añade 1 o 2 visualizations (type sequence, relationship o table) con title, items (label y detail), caption y evidence. No escribas HTML ni Mermaid en text.
Devuelve exactamente {"status":"answered","claims":[...],"visualizations":[...]}. Si no hay respaldo, devuelve {"status":"insufficient_sources","claims":[],"visualizations":[]}. Devuelve solo JSON."""

EVIDENCE_SCHEMA = {'type': 'array', 'minItems': 1, 'maxItems': 10, 'items': {
    'type': 'object', 'additionalProperties': False,
    'properties': {'source_id': {'type': 'string'}, 'quote': {'type': 'string', 'minLength': 8, 'maxLength': 500}},
    'required': ['source_id', 'quote'],
}}

RESPONSE_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'status': {'type': 'string', 'enum': ['answered', 'insufficient_sources']},
        'claims': {'type': 'array', 'minItems': 0, 'maxItems': 10, 'items': {
            'type': 'object', 'additionalProperties': False,
            'properties': {
                'kind': {'type': 'string', 'enum': ['summary', 'inference']},
                'text': {'type': 'string', 'minLength': 1, 'maxLength': 3500},
                'evidence': deepcopy(EVIDENCE_SCHEMA),
            }, 'required': ['kind', 'text', 'evidence'],
        }},
        'visualizations': {'type': 'array', 'maxItems': 3, 'items': {
            'type': 'object', 'additionalProperties': False,
            'properties': {
                'type': {'type': 'string', 'enum': ['sequence', 'relationship', 'table']},
                'title': {'type': 'string', 'minLength': 1, 'maxLength': 140},
                'items': {'type': 'array', 'minItems': 2, 'maxItems': 12, 'items': {
                    'type': 'object', 'additionalProperties': False,
                    'properties': {
                        'label': {'type': 'string', 'minLength': 1, 'maxLength': 100},
                        'detail': {'type': 'string', 'minLength': 1, 'maxLength': 360},
                    }, 'required': ['label', 'detail'],
                }},
                'caption': {'type': 'string', 'minLength': 1, 'maxLength': 700},
                'evidence': deepcopy(EVIDENCE_SCHEMA),
            }, 'required': ['type', 'title', 'items', 'caption', 'evidence'],
        }},
    }, 'required': ['status', 'claims', 'visualizations'],
}


def response_schema(messages, base_schema=None):
    payload = None
    claim_limit = None
    for message in messages:
        if message.get('role') != 'user':
            continue
        try:
            value = json.loads(message['content'])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        if isinstance(value, dict) and isinstance(value.get('sources'), list):
            payload = value
        if isinstance(value, dict) and value.get('repair') is True and value.get('max_claims') == 5:
            claim_limit = 5
    if base_schema is None and payload and 'context' in payload:
        from docente_ai.agents.pedagogy import RESPONSE_SCHEMA as base_schema
    schema = deepcopy(base_schema or RESPONSE_SCHEMA)
    if claim_limit and 'claims' in schema.get('properties', {}):
        schema['properties']['claims']['maxItems'] = claim_limit
    if not payload or 'claims' not in schema.get('properties', {}):
        return schema
    options = []
    for source in payload.get('sources', []):
        # Exact short excerpts: constrained decoding cannot repair OCR or translate them.
        excerpts = [p['id'] for p in source.get('passages', [])]
        if excerpts:
            options.append({'type': 'object', 'additionalProperties': False,
                'properties': {'source_id': {'const': source['source_id']},
                               'quote': {'type': 'string', 'enum': excerpts}},
                'required': ['source_id', 'quote']})
    if options:
        constrained = {'anyOf': options}
        schema['properties']['claims']['items']['properties']['evidence']['items'] = constrained
        schema['properties']['visualizations']['items']['properties']['evidence']['items'] = deepcopy(constrained)
    return schema


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def make_messages(question, evidence):
    sources = [
        {'source_id': source['source_id'],
         'title': (source.get('metadata') or {}).get('title') or source.get('source_title', ''),
         'authors': (source.get('metadata') or {}).get('authors') or source.get('authors', []),
         'year': (source.get('metadata') or {}).get('year'),
         'category': source['category'],
         'passages': passages(source['text'])}
        for source in evidence
    ]
    return [{'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': compact({'question': question, 'sources': sources})}]


def estimate_input(messages, schema=None):
    if schema is None:
        schema = response_schema(messages)
    # Conservador para los tokenizadores BPE habituales: contar bytes UTF-8,
    # incluidos el esquema y roles. El margen adicional cubre la plantilla chat.
    # No se presenta como un tokenizador universal ni un conteo exacto.
    return len((compact(messages) + compact(schema)).encode('utf-8'))


def build_prompt(question, candidates, settings):
    selected, omitted, seen = [], [], set()
    if estimate_input(make_messages(question, [])) > settings.input_budget:
        raise ValueError('La pregunta y el contrato no caben en el contexto configurado. Reduce la pregunta o ajusta num_ctx/max_output_tokens.')
    for candidate in candidates:
        if candidate['text'] in seen:
            omitted.append({'chunk_id': candidate['chunk_id'], 'reason': 'duplicate_text'})
            continue
        seen.add(candidate['text'])
        source = {**candidate, 'source_id': f'S{len(selected) + 1}'}
        if estimate_input(make_messages(question, [*selected, source])) > settings.input_budget:
            omitted.append({'chunk_id': candidate['chunk_id'], 'reason': 'context_budget'})
        else:
            selected.append(source)
    if candidates and not selected:
        raise ValueError('Ningún fragmento completo cabe en el contexto; reduce chunk_chars y reindexa o ajusta el presupuesto generativo.')
    messages = make_messages(question, selected)
    return {'messages': messages, 'evidence': selected, 'omitted': omitted, 'estimated_input': estimate_input(messages)}
