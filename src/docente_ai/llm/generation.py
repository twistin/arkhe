"""Una llamada generativa acotada; respuestas parciales nunca son válidas."""

import json
import httpx
from docente_ai.generation.live import live_transport, current_execution, transport_extensions
from docente_ai.generation.prompt import RESPONSE_SCHEMA, estimate_input, response_schema
from docente_ai.llm.local import LocalModelError, LocalOllama
from docente_ai.generation.errors import GenerationLengthError, ContextBudgetError, AuthorizationError


class OllamaGenerator(LocalOllama):
    capability = 'completion'
    response_schema = RESPONSE_SCHEMA

    def _payload(self, messages):
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
        return payload

    def generate(self, messages):
        return self._validate(self.request('POST', '/api/chat', json=self._payload(messages)))

    def generate_stream(self, messages, on_chunk):
        payload = self._payload(messages)
        payload['stream'] = True
        chunks, final, size = [], None, 0
        try:
            with live_transport(self.client), self.client.stream('POST', '/api/chat', json=payload,
                                                                       extensions=transport_extensions()) as response:
                response.raise_for_status()
                with live_transport(response):
                    for line in response.iter_lines():
                        if current_execution(): current_execution().check()
                        if not line: continue
                        data = json.loads(line)
                        if not isinstance(data, dict) or data.get('error'):
                            raise LocalModelError('Evento generativo de Ollama inválido.')
                        message = data.get('message', {})
                        if not isinstance(message, dict) or message.get('tool_calls') or message.get('role') != 'assistant':
                            raise LocalModelError('Mensaje generativo de Ollama inválido.')
                        text = message.get('content', '')
                        if not isinstance(text, str):
                            raise LocalModelError('Texto generativo de Ollama inválido.')
                        size += len(text.encode('utf-8'))
                        if size > 100_000: raise LocalModelError('Respuesta generativa demasiado grande.')
                        if text:
                            chunks.append(text)
                            on_chunk(text)
                        if data.get('done') is True:
                            final = data
                            break
            if final is None: raise LocalModelError('Ollama interrumpió la generación sin completarla.')
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                raise AuthorizationError('Ollama rechazó la autorización.') from None
            raise LocalModelError(f'Ollama respondió HTTP {exc.response.status_code}.') from exc
        except httpx.RequestError as exc:
            from docente_ai.generation.errors import NetworkError
            raise NetworkError('Ollama interrumpió la conexión generativa.') from exc
        except (ValueError, UnicodeError) as exc:
            if isinstance(exc, LocalModelError): raise
            raise LocalModelError('Evento JSON de Ollama inválido.') from exc
        final['message'] = {**final.get('message', {}), 'content': ''.join(chunks)}
        return self._validate(final)

    def _validate(self, data):
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
