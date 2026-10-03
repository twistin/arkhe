"""Adaptador genérico de chat para APIs compatibles con OpenAI."""

import httpx
import time
from copy import deepcopy
from docente_ai.secrets import get_secret
from docente_ai.generation.errors import ProviderError, NetworkError, AuthorizationError, GenerationLengthError
from docente_ai.generation.prompt import response_schema, compact

class OpenAICompatibleGenerator:
    """Generador con destino, modelo y capacidades declarados en los ajustes.

    El embedder siempre es local (bge-m3); solo la generación va a la nube.
    Los documentos nunca se envían — solo los fragmentos relevantes recuperados.
    """

    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.transport_retries = 0

    def __enter__(self):
        self.settings.require_consent()
        api_key = get_secret(self.settings.secret_name)
        if not api_key:
            raise ProviderError('Falta la clave de API del proveedor. Configúrala en Ajustes.')
        self.client = httpx.Client(
            base_url=self.settings.base_url + '/',
            trust_env=False, follow_redirects=False,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            timeout=float(self.settings.timeout_seconds),
        )
        return self

    def __exit__(self, *_):
        if self.client is not None:
            self.client.close()
            self.client = None

    def _request(self, method: str, path: str, body=None) -> dict:
        if self.client is None:
            raise ProviderError('Generador remoto no inicializado.')
        for attempt in range(2):
            try:
                resp = self.client.request(method, path, json=body)
                if resp.status_code in (401, 403):
                    raise AuthorizationError(f'Error de autorización con el proveedor ({resp.status_code}). Comprueba tu clave API y saldo en Ajustes.')
                transient = resp.status_code == 429 or 500 <= resp.status_code <= 599
                if transient and attempt == 0:
                    self.transport_retries += 1
                    time.sleep(0.5)
                    continue
                if transient:
                    raise NetworkError(f'El proveedor no está disponible (HTTP {resp.status_code}) tras un reintento.')
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise ValueError
                return data
            except httpx.TimeoutException:
                if attempt == 0:
                    self.transport_retries += 1
                    time.sleep(0.5)
                    continue
                raise NetworkError('El proveedor agotó el tiempo de espera tras un reintento.') from None
            except httpx.HTTPStatusError as exc:
                raise ProviderError(f'Error de API del proveedor ({exc.response.status_code}).') from None
            except (httpx.RequestError, OSError):
                raise NetworkError('Error de red o conexión con el proveedor.') from None
            except ProviderError:
                raise
            except ValueError:
                raise ProviderError('El proveedor devolvió una respuesta HTTP que no es JSON válido.') from None

    def generate(self, messages) -> dict:
        """Genera una respuesta JSON usando el proveedor.

        La capacidad declarada del preset determina el formato solicitado.
        El contrato compacto acompaña siempre al mensaje de sistema.
        El servicio valida el JSON antes de guardarlo.
        """
        model = self.settings.model
        messages = deepcopy(messages)
        schema = response_schema(messages, getattr(self, 'response_schema', None))
        instruction = 'Devuelve solo JSON válido. Esquema JSON obligatorio: ' + compact(schema)
        system = next((message for message in messages if message.get('role') == 'system'), None)
        if system is None:
            messages.insert(0, {'role': 'system', 'content': instruction})
        else:
            system['content'] += '\n' + instruction
        body = {
            'model': model,
            'messages': messages,
            'temperature': self.settings.temperature,
            'max_tokens': self.settings.max_output_tokens,
            'stream': False,
        }
        # El formato depende de la capacidad declarada, no del nombre del proveedor.
        if self.settings.response_format == 'json_object':
            body['response_format'] = {'type': 'json_object'}

        if self.settings.response_format == 'json_schema':
            body['response_format'] = {'type': 'json_schema', 'json_schema': {'name': 'docente_response', 'strict': True, 'schema': schema}}

        data = self._request('POST', 'chat/completions', body)

        choices = data.get('choices', [])
        if not choices:
            raise ProviderError('El proveedor no devolvió ninguna opción de respuesta.')
        choice = choices[0]
        finish = choice.get('finish_reason')
        usage = data.get('usage', {})
        metrics = {
            'prompt_eval_count': usage.get('prompt_tokens', 0),
            'eval_count': usage.get('completion_tokens', 0),
            'provider': self.settings.provider, 'model': model,
            'transport_retries': self.transport_retries,
        }
        if finish == 'length':
            message = choice.get('message', {})
            raise GenerationLengthError('Generación detenida por límite de tokens; reduce a un máximo de cinco claims y redacta de forma concisa.',
                                        content=message.get('content', '') if isinstance(message, dict) else '', metrics=metrics)
        if finish != 'stop':
            raise ProviderError(f'El proveedor terminó con motivo inesperado: {finish!r}.')

        message = choice.get('message', {})
        if not isinstance(message, dict) or message.get('tool_calls'):
            raise ProviderError('Mensaje remoto inválido o petición de herramientas no permitida.')
        # No almacenar el razonamiento interno del proveedor.
        content = message.get('content', '')
        if not isinstance(content, str) or not content.strip():
            raise ProviderError('El proveedor devolvió contenido vacío.')
        if len(content.encode('utf-8')) > 100_000:
            raise ProviderError('Respuesta remota demasiado grande.')

        return {'content': content, 'metrics': metrics}
