"""Generador usando la API de DeepSeek (compatible con OpenAI)."""

import httpx

DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_MODELS = {
    'deepseek-chat': 'DeepSeek-V3 — rápido, preciso, económico',
    'deepseek-reasoner': 'DeepSeek-R1 — razonamiento profundo, más lento',
}


class DeepSeekError(ValueError):
    pass


class DeepSeekGenerator:
    """Generador usando la API OpenAI-compatible de DeepSeek.

    El embedder siempre es local (bge-m3); solo la generación va a la nube.
    Los documentos nunca se envían — solo los fragmentos relevantes recuperados.
    """

    def __init__(self, settings):
        self.settings = settings
        self.client = None

    def __enter__(self):
        if not self.settings.api_key or not self.settings.api_key.strip():
            raise DeepSeekError('Falta la clave de API de DeepSeek. Configúrala en Ajustes.')
        self.client = httpx.Client(
            base_url=DEEPSEEK_BASE_URL,
            headers={
                'Authorization': f'Bearer {self.settings.api_key.strip()}',
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
            raise DeepSeekError('Generador de DeepSeek no inicializado.')
        try:
            resp = self.client.request(method, path, json=body)
            if resp.status_code in (401, 403):
                try:
                    err_data = resp.json()
                    err_msg = err_data.get('error', {}).get('message', resp.text)
                except Exception:
                    err_msg = resp.text
                raise DeepSeekError(f'Error de autorización con DeepSeek ({resp.status_code}): {err_msg}. Comprueba tu clave API y saldo en Ajustes.')
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            try:
                err_msg = exc.response.json().get('error', {}).get('message', str(exc))
            except Exception:
                err_msg = str(exc)
            raise DeepSeekError(f'DeepSeek API error {exc.response.status_code}: {err_msg}') from exc
        except (httpx.RequestError, OSError) as exc:
            raise DeepSeekError(f'Error de red o conexión con DeepSeek: {exc}') from exc

    def generate(self, messages) -> dict:
        """Genera una respuesta JSON usando DeepSeek.

        No aplica structured output (JSON mode) porque DeepSeek-R1 no lo admite
        en modo reasoner. Se usa instrucción en el system prompt para asegurar JSON.
        El servicio valida el JSON antes de guardarlo.
        """
        model = self.settings.model
        body = {
            'model': model,
            'messages': messages,
            'temperature': self.settings.temperature,
            'max_tokens': self.settings.max_output_tokens,
            'stream': False,
        }
        # deepseek-chat admite response_format JSON; deepseek-reasoner no.
        if model == 'deepseek-chat':
            body['response_format'] = {'type': 'json_object'}

        data = self._request('POST', '/chat/completions', body)

        choices = data.get('choices', [])
        if not choices:
            raise DeepSeekError('DeepSeek no devolvió ninguna opción de respuesta.')
        choice = choices[0]
        finish = choice.get('finish_reason')
        if finish == 'length':
            raise DeepSeekError('Generación detenida por límite de tokens; no se acepta como respuesta.')
        if finish != 'stop':
            raise DeepSeekError(f'DeepSeek terminó con motivo inesperado: {finish!r}.')

        message = choice.get('message', {})
        # deepseek-reasoner devuelve reasoning_content separado; lo ignoramos.
        content = message.get('content', '')
        if not isinstance(content, str) or not content.strip():
            raise DeepSeekError('DeepSeek devolvió contenido vacío.')
        if len(content.encode('utf-8')) > 100_000:
            raise DeepSeekError('Respuesta de DeepSeek demasiado grande.')

        usage = data.get('usage', {})
        metrics = {
            'prompt_eval_count': usage.get('prompt_tokens', 0),
            'eval_count': usage.get('completion_tokens', 0),
            'provider': 'deepseek',
            'model': model,
        }
        return {'content': content, 'metrics': metrics}
