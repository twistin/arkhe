"""Validar estructura y procedencia; no demuestra suficiencia factual."""

import json
import re
from docente_ai.generation.quotations import passages


class ResponseValidationError(ValueError):
    pass


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


def normalize_text_variants(text):
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'").replace('«', '"').replace('»', '"')
    text = text.replace('–', '-').replace('—', '-')
    var_a = re.sub(r'(\w+)[\xad\u2010\u2013-]\s*[\r\n]+\s*(\w+)', r'\1\2', text)
    var_b = re.sub(r'(\w+)[\xad\u2010\u2013-]\s*[\r\n]+\s*(\w+)', r'\1-\2', text)
    var_c = re.sub(r'(\w+)[\xad\u2010\u2013-]\s*[\r\n]+\s*(\w+)', r'\1 \2', text)
    clean = lambda t: re.sub(r'[\xad\u200b\u200c\u200d\u2060\ufeff]', '', t)
    raw = ' '.join(clean(text).split())
    return [raw, ' '.join(clean(var_a).split()), ' '.join(clean(var_b).split()), ' '.join(clean(var_c).split())]


def quote_matches(excerpt, source_text):
    q_norm = ' '.join(excerpt.split())
    src_vars = normalize_text_variants(source_text)
    if any(q_norm in v for v in src_vars):
        return True
    clean_q = ' '.join(re.sub(r'[^\w\s]', ' ', q_norm).lower().split())
    for v in src_vars:
        clean_v = ' '.join(re.sub(r'[^\w\s]', ' ', v).lower().split())
        if clean_q in clean_v:
            return True
        if re.search(r'\.{2,}|…', excerpt):
            parts = [p.strip() for p in re.split(r'\.{2,}|…', clean_q) if len(p.strip()) > 8]
            if parts and all(p in clean_v for p in parts):
                return True
    compact_q = re.sub(r'\W+', '', excerpt.lower())
    if len(compact_q) >= 12:
        for v in src_vars:
            if compact_q in re.sub(r'\W+', '', v.lower()):
                return True
        if re.search(r'\.{2,}|…', excerpt):
            parts = [re.sub(r'\W+', '', p.lower()) for p in re.split(r'\.{2,}|…', excerpt) if len(re.sub(r'\W+', '', p.lower())) >= 8]
            for v in src_vars:
                compact_v = re.sub(r'\W+', '', v.lower())
                if parts and all(p in compact_v for p in parts):
                    return True
    return False


def validate_evidence(value, known, *, owner):
    quotes = normalize_evidence(value, known)
    if not isinstance(quotes, list) or not 1 <= len(quotes) <= 30:
        fail(f'{owner} necesita entre una y treinta evidencias.')
    for quote in quotes:
        if not isinstance(quote, dict):
            fail('Evidencia con estructura inválida.')
        if 'quote_id' in quote and 'quote' not in quote:
            quote['quote'] = quote.pop('quote_id')
        elif 'quote_id' in quote:
            quote.pop('quote_id', None)
        if set(quote) != {'source_id', 'quote'}:
            fail('Evidencia con campos no permitidos.')
        source_id, excerpt = quote['source_id'], quote['quote']
        if not isinstance(source_id, str) or source_id not in known:
            fail('La respuesta cita una fuente inexistente o que no se envió al modelo.')
        if isinstance(excerpt, str):
            choices = {p['id']: p['text'] for p in passages(known[source_id]['text'])}
            if excerpt in choices:
                excerpt = quote['quote'] = choices[excerpt]
        if not isinstance(excerpt, str) or not 8 <= len(excerpt.strip()) <= 500:
            fail('La cita debe tener entre 8 y 500 caracteres.')
        if not quote_matches(excerpt, known[source_id]['text']):
            fail('La cita textual no coincide con el fragmento autorizado.')
    return quotes


def validate_generated_text(value, *, label, maximum):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        fail(f'{label} vacío o demasiado largo.')
    if any(ord(char) < 32 and char not in '\n\r\t' for char in value):
        fail('La respuesta contiene caracteres de control no permitidos.')
    if re.search(r'https?://|\b10\.\d{4,9}/|\b(?:p|pp|pág|página|páginas)\.?\s*\d+|\[S\d+\]', value, re.I):
        fail('El modelo incluyó referencias libres; debe usar solo evidence/source_id.')


def normalize_visuals(visuals, default_evidence, known=None):
    if not isinstance(visuals, list):
        return []
    normalized = []
    for v in visuals:
        if not isinstance(v, dict):
            continue
        v_type = v.get('type', 'relationship')
        title = v.get('title') or 'Esquema conceptual'
        caption = v.get('caption') or title
        data_block = v.get('data') if isinstance(v.get('data'), dict) else {}
        items = v.get('items')
        steps = v.get('steps') or data_block.get('steps')
        rows = v.get('rows') or data_block.get('rows')

        if not items and steps and isinstance(steps, list):
            items = []
            for idx, s in enumerate(steps):
                if isinstance(s, str):
                    parts = s.split(':', 1) if ':' in s else (f'Paso {idx+1}', s)
                    items.append({'label': parts[0].strip(), 'detail': parts[1].strip()})
                elif isinstance(s, dict):
                    items.append({'label': s.get('label', f'Paso {idx+1}'),
                                  'detail': s.get('description', s.get('detail', s.get('text', '')))})
        elif not items and rows and isinstance(rows, list):
            items = [{'label': str(r[0]), 'detail': ' · '.join(str(c) for c in r[1:])}
                     for r in rows if isinstance(r, list) and len(r) >= 2]
        if not isinstance(items, list) or len(items) < 2:
            continue
        clean_items = []
        for it in items[:12]:
            if isinstance(it, dict):
                l = it.get('label', 'Concepto')[:100]
                d = it.get('detail', it.get('description', ''))[:360]
                if l and d:
                    clean_items.append({'label': l, 'detail': d})
        if len(clean_items) < 2:
            continue
        ev = v.get('evidence')
        if ev:
            ev = normalize_evidence(ev, known)
        if not ev or not isinstance(ev, list):
            ev = default_evidence[:2] if default_evidence else []
        normalized.append({'type': v_type, 'title': title[:140], 'caption': caption[:700],
                           'items': clean_items, 'evidence': ev})
    return normalized[:3]


def validate_response(content: str, evidence: list[dict]) -> dict:
    try:
        data = json.loads(content, object_pairs_hook=unique_object,
                          parse_constant=lambda value: fail('Constante JSON inválida.'))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ResponseValidationError('La respuesta del modelo no es JSON válido; no se publica.') from exc
    if not isinstance(data, dict):
        fail('La respuesta debe ser un objeto JSON.')
    # Compatibilidad con registros y modelos anteriores a grounded-answer:5.
    data.setdefault('visualizations', [])
    for k in list(data.keys()):
        if k not in {'status', 'claims', 'visualizations'}:
            if k in ('observations', 'reason', 'notes', 'explanation', 'message', 'thinking', 'warnings'):
                data.pop(k, None)
            else:
                fail('La respuesta no cumple el contrato: status, claims y visualizations.')
    if data['status'] in ('ok', 'success', 'complete', 'completed'):
        data['status'] = 'answered'
    if data['status'] not in ('answered', 'insufficient_sources'):
        fail('Estado de respuesta no válido.')
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
    all_claim_evidence = []
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {'kind', 'text', 'evidence'}:
            fail('Afirmación con campos no permitidos.')
        if claim['kind'] not in ('summary', 'inference'):
            fail('Tipo de afirmación no permitido.')
        text = claim.get('text')
        validate_generated_text(text, label='Texto de afirmación', maximum=4000)
        # La bibliografía y los localizadores se añaden exclusivamente por código.
        claim['evidence'] = validate_evidence(claim['evidence'], known, owner='Cada afirmación')
        all_claim_evidence.extend(claim['evidence'])
    visuals = normalize_visuals(data['visualizations'], all_claim_evidence)
    data['visualizations'] = visuals
    for visual in visuals:
        if not isinstance(visual, dict) or set(visual) != {'type', 'title', 'items', 'caption', 'evidence'}:
            fail('Esquema con campos no permitidos.')
        if visual['type'] not in ('sequence', 'relationship', 'table'):
            fail('Tipo de esquema no permitido.')
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
