"""Reparación acotada; nunca sustituye la validación documental."""

from docente_ai.generation.live import generate_live, emit_live
from copy import deepcopy
import json

from docente_ai.generation.errors import RecoverableGenerationError, GenerationLengthError
from docente_ai.generation.prompt import compact
from docente_ai.generation.validation import unique_object, fail, ResponseValidationError, EvidenceCardinalityError


def sanitize(content):
    """Retira solo campos desconocidos de evidencias y esquemas; conserva textos."""
    try:
        data = json.loads(content, object_pairs_hook=unique_object,
                          parse_constant=lambda _: fail('Constante JSON inválida.'))
    except (ValueError, RecursionError):
        return content, []
    removed = []

    def clean(obj, allowed, path):
        if isinstance(obj, dict):
            for key in list(obj):
                if key not in allowed:
                    removed.append(path + '.' + key)
                    del obj[key]

    def evidence(owner, path):
        values = owner.get('evidence') if isinstance(owner, dict) else None
        if isinstance(values, list):
            for i, value in enumerate(values):
                clean(value, {'source_id', 'quote'}, f'{path}.evidence[{i}]')

    if isinstance(data, dict):
        if isinstance(data.get('claims'), list):
            for i, claim in enumerate(data['claims']):
                evidence(claim, f'claims[{i}]')
        if isinstance(data.get('visualizations'), list):
            for i, visual in enumerate(data['visualizations']):
                path = f'visualizations[{i}]'
                clean(visual, {'type', 'title', 'items', 'caption', 'evidence'}, path)
                evidence(visual, path)
                if isinstance(visual, dict) and isinstance(visual.get('items'), list):
                    for j, item in enumerate(visual['items']):
                        clean(item, {'label', 'detail'}, f'{path}.items[{j}]')
    return (compact(data) if removed else content), removed


def generate_validated(generator, messages, validator, metrics, *, check, report, sanitize_response=False, on_dialogue=None):
    dialogue = deepcopy(messages)
    attempts = metrics.setdefault('attempts', [])
    reduced = False
    for attempt in range(3):
        raw, response_metrics, removed = '', {}, []
        try:
            check()
            if on_dialogue:
                on_dialogue(dialogue)
            emit_live('attempt', attempt=attempt + 1, total=3)
            response = generate_live(generator, dialogue,
                                     lambda text: emit_live('token', text=text, attempt=attempt + 1))
            emit_live('usage', attempt=attempt + 1, tokens=response['metrics'].get('eval_count'))
            raw, response_metrics = response['content'], response['metrics']
            check()
            candidate, removed = sanitize(raw) if sanitize_response else (raw, [])
            report('Comprobando el contrato y las citas exactas')
            result = validator(candidate)
            if reduced and len(result['claims']) > 5:
                raise ResponseValidationError('La reparación exige un máximo de cinco claims; ajusta también los vínculos del plan.')
            check()
        except RecoverableGenerationError as exc:
            if isinstance(exc, GenerationLengthError):
                raw, response_metrics = exc.content, exc.metrics
                reduced = True
            exc.content, exc.metrics = raw, response_metrics
            attempts.append({'error_type': exc.error_type,
                             'tokens': {'input': response_metrics.get('prompt_eval_count'), 'output': response_metrics.get('eval_count')},
                             'sanitized_fields': removed})
            if attempt == 2:
                raise
            check()
            emit_live('repair', attempt=attempt + 2, total=3, error_type=exc.error_type)
            report(f'Reparando respuesta · intento {attempt + 2} de 3')
            instruction = {'repair': True, 'error_type': exc.error_type,
                           'instruction': 'Corrige el error: ' + str(exc) + ' Devuelve de nuevo el objeto JSON completo. Usa solo las fuentes y quote_XXX originales; no inventes citas.'}
            if isinstance(exc, EvidenceCardinalityError):
                instruction['instruction'] += (
                    ' Revisa evidence en todos los claims y esquemas: debe ser una lista de 1 a 30 objetos'
                    ' {"source_id":"S1","quote":"quote_001"} con respaldo real para el texto.'
                    ' Si un bloque no tiene respaldo, elimínalo; no le asignes citas de otro bloque por defecto.'
                    ' Si hay plan, actualiza todos los claim_ids tras eliminar bloques, usando índices desde 1,'
                    ' y conserva la duración solicitada. Las actividades propuestas van en plan.activities;'
                    ' los claims contienen únicamente contenido documental sustentado.'
                    ' Si no queda contenido sustentado, devuelve status="insufficient_sources", claims=[],'
                    ' visualizations=[] y, si hay plan, plan=null.'
                )
            if reduced:
                instruction['max_claims'] = 5
                instruction['instruction'] += ' Máximo cinco claims breves; no aumentes tokens. Conserva el contrato y, si hay plan, la duración solicitada.'
            dialogue.extend([{'role': 'assistant', 'content': raw},
                             {'role': 'user', 'content': compact(instruction)}])
            continue
        except Exception as exc:
            attempts.append({'error_type': getattr(exc, 'error_type', 'internal'),
                             'tokens': {'input': response_metrics.get('prompt_eval_count'), 'output': response_metrics.get('eval_count')}})
            raise
        except KeyboardInterrupt:
            attempts.append({'error_type': 'cancelled',
                             'tokens': {'input': response_metrics.get('prompt_eval_count'), 'output': response_metrics.get('eval_count')}})
            raise
        attempts.append({'error_type': None,
                         'tokens': {'input': response_metrics.get('prompt_eval_count'), 'output': response_metrics.get('eval_count')},
                         'sanitized_fields': removed})
        metrics.update(response_metrics)
        return result, raw
