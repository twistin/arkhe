"""Transporte y verificación de identidad compartidos por Ollama."""

import httpx
from docente_ai.generation.errors import ProviderError, NetworkError, AuthorizationError


LocalModelError = ProviderError


class LocalOllama:
    capability = None
    context_error_hint = ''

    def __init__(self, settings, *, transport=None):
        self.settings = settings
        self.model = settings.model
        self.digest = None
        self.capabilities = []
        self.client = httpx.Client(base_url=settings.host, timeout=settings.timeout_seconds,
                                   trust_env=False, follow_redirects=False, transport=transport)

    def __enter__(self):
        try:
            self.identify()
        except BaseException:
            self.client.close()
            raise
        return self

    def __exit__(self, *args):
        self.client.close()

    def request(self, method, path, **kwargs):
        try:
            response = self.client.request(method, path, **kwargs)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError
            return data
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                raise AuthorizationError('Ollama rechazó la autorización.') from None
            hint = self.context_error_hint if exc.response.status_code == 400 else ''
            raise LocalModelError(f'Ollama respondió HTTP {exc.response.status_code}.{hint}') from exc
        except httpx.RequestError as exc:
            raise NetworkError('Ollama no responde o agotó el tiempo de espera; no se usa ningún servicio alternativo.') from exc
        except (ValueError, UnicodeError) as exc:
            raise LocalModelError('Respuesta JSON de Ollama inválida.') from exc

    def installed(self):
        models = self.request('GET', '/api/tags').get('models')
        if not isinstance(models, list):
            raise LocalModelError('Listado de modelos inválido.')
        names = {self.model, self.model + ':latest'} if ':' not in self.model.rsplit('/', 1)[-1] else {self.model}
        match = next((item for item in models if isinstance(item, dict) and item.get('name') in names), None)
        if not match:
            raise LocalModelError('El modelo no está instalado. Instálalo explícitamente o cambia la configuración.')
        if match.get('remote_host') or match.get('remote_model') or type(match.get('size')) is not int or match['size'] <= 0:
            raise LocalModelError('El modelo no acredita pesos locales; se rechaza el acceso remoto.')
        if not isinstance(match.get('digest'), str) or not match['digest']:
            raise LocalModelError('El modelo no proporciona un digest verificable.')
        return match

    def identify(self):
        match = self.installed()
        self.model = match['name']
        self.digest = match['digest']
        info = self.request('POST', '/api/show', json={'model': self.model})
        if info.get('remote_host') or info.get('remote_model'):
            raise LocalModelError('El modelo es remoto; no se enviará contenido.')
        self.capabilities = info.get('capabilities')
        if not isinstance(self.capabilities, list) or self.capability not in self.capabilities:
            raise LocalModelError(f'El modelo seleccionado no anuncia la capacidad {self.capability}.')

    def verify_identity(self):
        if self.installed()['digest'] != self.digest:
            raise LocalModelError('El modelo ha cambiado durante la operación. Repite con su nuevo digest y reindexa si es un modelo de embeddings.')
