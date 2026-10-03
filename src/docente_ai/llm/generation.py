"""Una llamada generativa acotada; respuestas parciales nunca son válidas."""

from docente_ai.generation.prompt import RESPONSE_SCHEMA, estimate_input, response_schema
from docente_ai.llm.local import LocalModelError, LocalOllama
from docente_ai.generation.errors import GenerationLengthError, ContextBudgetError


class OllamaGenerator(LocalOllama):
    capability = 'completion'
    response_schema = RESPONSE_SCHEMA

    def generate(self, messages):
        if not self.digest:
            raise LocalModelError('Inicializa el adaptador generativo antes de usarlo.')
        schema = response_schema(messages, self.response_schema)
        if estimate_input(messages, schema) > self.settings.input_budget:
            raise ContextBudgetError('El prompt excede el presupuesto configurado; no se recortan las fuentes ni las citas.')
        self.verify_identity()
        payload = {
            'model': self.model, 'messages': messages, 'stream': False,
            'format': schema, 'keep_alive': getattr(self, 'keep_alive', 0),
            'options': {'temperature': self.settings.temperature, 'num_ctx': self.settings.num_ctx,
                        'num_predict': self.settings.max_output_tokens, 'num_batch': self.settings.num_batch},
        }
        if 'thinking' in self.capabilities:
            payload['think'] = self.settings.think
        elif self.settings.think:
            raise LocalModelError('Este modelo no anuncia capacidad thinking.')
        data = self.request('POST', '/api/chat', json=payload)
        self.verify_identity()
        message = data.get('message')
        if data.get('done_reason') == 'length':
            raise GenerationLengthError('Generación detenida por límite de tokens; reduce a un máximo de cinco claims y redacta de forma concisa.',
                                        content=message.get('content', '') if isinstance(message, dict) else '',
                                        metrics={key: data[key] for key in ('prompt_eval_count', 'eval_count') if type(data.get(key)) is int})
        if data.get('done') is not True or data.get('done_reason') != 'stop':
            raise LocalModelError('Ollama no completó la generación. Revisa su registro y la memoria disponible; prueba a reducir num_ctx/num_batch. No se acepta la respuesta.')
        if not isinstance(message, dict) or message.get('role') != 'assistant' or message.get('tool_calls'):
            raise LocalModelError('Ollama devolvió un mensaje inválido o intentó utilizar herramientas.')
        content = message.get('content')
        if not isinstance(content, str) or not content.strip() or len(content.encode('utf-8')) > 100_000:
            raise LocalModelError('Respuesta generativa vacía o demasiado grande.')
        prompt_count = data.get('prompt_eval_count')
        output_count = data.get('eval_count')
        if type(prompt_count) is not int or prompt_count < 0 or prompt_count > self.settings.input_budget:
            raise LocalModelError('El consumo real de contexto falta o supera el presupuesto; no se acepta la respuesta.')
        if type(output_count) is not int or not 0 <= output_count <= self.settings.max_output_tokens:
            raise LocalModelError('El consumo de salida falta o supera el límite configurado.')
        metrics = {key: data[key] for key in ('prompt_eval_count', 'eval_count', 'total_duration', 'load_duration') if key in data}
        # No guardar ni renderizar el campo thinking.
        return {'content': content, 'metrics': metrics}
