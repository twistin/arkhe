"""Validar estructura y procedencia; no demuestra suficiencia factual."""

import json
import re
from docente_ai.generation.quotations import passages
from docente_ai.generation.errors import RecoverableGenerationError


class ResponseValidationError(RecoverableGenerationError):
    pass


class JsonFormatError(ResponseValidationError):
    error_type = 'json_format'


class ExtraFieldsError(ResponseValidationError):
    error_type = 'extra_fields'


class InvalidEnumError(ResponseValidationError):
    error_type = 'invalid_enum'


class QuoteResolutionError(ResponseValidationError):
    error_type = 'quote_unresolved'


def fail(message):
    raise ResponseValidationError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail('La respuesta contiene claves JSON duplicadas.')
        result[key] = value
    return result


def whitespace(text):
    return ' '.join(text.split())


def normalize_evidence(value, known=None):
    """Accept deterministic shorthand or raw matched quotes used by JSON providers."""
    if not isinstance(value, list):
        return value
    normalized = []
    for item in value:
        if isinstance(item, str):
            match = re.fullmatch(r'\s*(S\d+)\s*:\s*(quote_\d{3}(?:\s*,\s*quote_\d{3})*)\s*', item)
            if match:
                normalized.extend({'source_id': match.group(1), 'quote': quote.strip()}
                                  for quote in match.group(2).split(','))
            elif known:
                matched_src = None
                for s_id, s_info in known.items():
                    if quote_matches(item, s_info.get('text', '')):
                        matched_src = s_id
                        break
                if matched_src:
                    normalized.append({'source_id': matched_src, 'quote': item.strip()})
                else:
                    normalized.append(item)
            else:
                normalized.append(item)
        elif isinstance(item, dict):
            obj = dict(item)
            if 'text' in obj and 'quote' not in obj:
                obj['quote'] = obj.pop('text')
            if 'quote' in obj and 'source_id' not in obj and known:
                matched_src = next((s_id for s_id, s_info in known.items() if quote_matches(obj['quote'], s_info.get('text', ''))), None)
                if matched_src:
                    obj['source_id'] = matched_src
            normalized.append(obj)
        else:
            normalized.append(item)
    return normalized


def quote_matches(excerpt, source_text):
    """Solo espacios: nunca reconstruir, traducir o aproximar una cita."""
    return isinstance(excerpt, str) and bool(excerpt.strip()) and whitespace(excerpt) in whitespace(source_text)


def validate_evidence(value, known, *, owner):
    quotes = normalize_evidence(value, known)
    if not isinstance(quotes, list) or not 1 <= len(quotes) <= 30:
        fail(f'{owner} necesita entre una y treinta evidencias.')
    for index, quote in enumerate(quotes):
        if not isinstance(quote, dict):
            fail('Evidencia con estructura inválida.')
        if 'quote_id' in quote and 'quote' not in quote:
            quote['quote'] = quote.pop('quote_id')
        elif 'quote_id' in quote:
            quote.pop('quote_id', None)
        if set(quote) != {'source_id', 'quote'}:
            extra = sorted(set(quote) - {'source_id', 'quote'})
            raise ExtraFieldsError(f'{owner}.evidence[{index}] contiene campos no permitidos {extra}; usa solo source_id y quote.')
        source_id, excerpt = quote['source_id'], quote['quote']
        if not isinstance(source_id, str) or source_id not in known:
            raise QuoteResolutionError(f'{owner}.evidence[{index}].source_id no identifica una fuente enviada al modelo.')
        if isinstance(excerpt, str):
            choices = {p['id']: p['text'] for p in passages(known[source_id]['text'])}
            if excerpt in choices:
                excerpt = quote['quote'] = choices[excerpt]
        if not isinstance(excerpt, str) or not 8 <= len(excerpt.strip()) <= 500:
            fail('La cita debe tener entre 8 y 500 caracteres.')
        if not quote_matches(excerpt, known[source_id]['text']):
            raise QuoteResolutionError(f'{owner}.evidence[{index}]: La cita textual no coincide con el fragmento autorizado. Usa un quote_XXX permitido para esa fuente.')
    return quotes


def validate_generated_text(value, *, label, maximum):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        fail(f'{label} vacío o demasiado largo.')
    if any(ord(char) < 32 and char not in '\n\r\t' for char in value):
        fail('La respuesta contiene caracteres de control no permitidos.')
    if re.search(r'https?://|\b10\.\d{4,9}/|\b(?:p|pp|pág|página|páginas)\.?\s*\d+|\[S\d+\]', value, re.I):
        fail('El modelo incluyó referencias libres; debe usar solo evidence/source_id.')


def validate_response(content: str, evidence: list[dict]) -> dict:
    try:
        data = json.loads(content, object_pairs_hook=unique_object,
                          parse_constant=lambda value: fail('Constante JSON inválida.'))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise JsonFormatError('La respuesta del modelo no es JSON válido; devuelve solo un objeto JSON completo.') from exc
    if not isinstance(data, dict):
        fail('La respuesta debe ser un objeto JSON.')
    # Compatibilidad con registros y modelos anteriores a grounded-answer:5.
    data.setdefault('visualizations', [])
    if not {'status', 'claims'}.issubset(data):
        fail('La respuesta no cumple el contrato: faltan status y/o claims.')
    for k in list(data.keys()):
        if k not in {'status', 'claims', 'visualizations'}:
            if k in ('observations', 'reason', 'notes', 'explanation', 'message', 'thinking', 'warnings'):
                data.pop(k, None)
            else:
                raise ExtraFieldsError(f'Campo de respuesta no permitido: {k!r}; usa status, claims y visualizations.')
    if data['status'] not in ('answered', 'insufficient_sources'):
        raise InvalidEnumError('Estado de respuesta no válido; status debe ser answered o insufficient_sources.')
    claims = data['claims']
    if not isinstance(claims, list) or len(claims) > 12:
        fail('claims debe ser una lista con un máximo de doce afirmaciones o secciones.')
    if data['status'] == 'insufficient_sources':
        if claims or data['visualizations']:
            fail('Una abstención no puede incluir afirmaciones ni esquemas.')
        return data
    if not claims:
        fail('Una respuesta debe aportar al menos una afirmación sustentada.')
    known = {item['source_id']: item for item in evidence}
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict) or set(claim) != {'kind', 'text', 'evidence'}:
            raise ExtraFieldsError(f'claims[{index}] tiene campos no permitidos o incompletos; usa kind, text y evidence.')
        if claim['kind'] not in ('summary', 'inference'):
            raise InvalidEnumError(f'claims[{index}].kind no válido; usa summary o inference.')
        text = claim.get('text')
        validate_generated_text(text, label='Texto de afirmación', maximum=4000)
        # La bibliografía y los localizadores se añaden exclusivamente por código.
        claim['evidence'] = validate_evidence(claim['evidence'], known, owner=f'claims[{index}]')
    visuals = data['visualizations']
    if not isinstance(visuals, list) or len(visuals) > 3:
        fail('visualizations debe ser una lista con un máximo de tres esquemas.')
    for visual in visuals:
        if not isinstance(visual, dict) or set(visual) != {'type', 'title', 'items', 'caption', 'evidence'}:
            fail('Esquema con campos no permitidos.')
        if visual['type'] not in ('sequence', 'relationship', 'table'):
            raise InvalidEnumError('Tipo de esquema no permitido; usa sequence, relationship o table.')
        validate_generated_text(visual['title'], label='Título de esquema', maximum=140)
        validate_generated_text(visual['caption'], label='Descripción de esquema', maximum=700)
        items = visual['items']
        if not isinstance(items, list) or not 2 <= len(items) <= 12:
            fail('Cada esquema necesita entre dos y doce elementos.')
        for item in items:
            if not isinstance(item, dict) or set(item) != {'label', 'detail'}:
                fail('Elemento de esquema con campos no permitidos.')
            validate_generated_text(item['label'], label='Etiqueta de esquema', maximum=100)
            validate_generated_text(item['detail'], label='Detalle de esquema', maximum=360)
        visual['evidence'] = validate_evidence(visual['evidence'], known, owner='Cada esquema')
    return data
