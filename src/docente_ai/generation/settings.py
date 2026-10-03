"""Configuración generativa independiente del modelo de embeddings."""

from dataclasses import dataclass
import math
from pathlib import Path
import logging
import os
from uuid import uuid4
from urllib.parse import urlsplit
import hashlib

import yaml

from docente_ai.config import StrictLoader
from docente_ai.doctor import DEFAULT_HOST, local_url
from docente_ai.secrets import set_secret
from docente_ai.llm.presets import PRESETS, RESIDENCY_LABELS
from docente_ai.generation.errors import NonRecoverableGenerationError


class ConsentRequiredError(NonRecoverableGenerationError):
    error_type = 'consent_required'


@dataclass(frozen=True)
class GenerationSettings:
    model: str
    host: str = DEFAULT_HOST
    timeout_seconds: float = 180
    temperature: float = 0.0
    num_ctx: int = 4096
    max_output_tokens: int = 512
    context_margin: int = 256
    think: bool = False
    num_batch: int = 128
    # Proveedor externo: 'ollama' (por defecto, local) o 'deepseek' (API en la nube).
    provider: str = 'ollama'
    base_url: str = ''
    data_residency: str = ''
    response_format: str = ''
    remote_consent: str = ''

    def __post_init__(self):
        if self.provider not in PRESETS:
            raise ValueError('provider debe ser un preset conocido: ' + ', '.join(PRESETS))
        preset = PRESETS[self.provider]
        if self.data_residency and self.data_residency != preset['data_residency']:
            raise ValueError('La residencia debe coincidir con la declarada por el preset.')
        object.__setattr__(self, 'data_residency', preset['data_residency'])
        if not isinstance(self.remote_consent, str):
            raise ValueError('remote_consent debe ser texto.')
        if self.is_remote:
            endpoint = self.base_url or preset['base_url']
            if preset['base_url'] and endpoint.rstrip('/') != preset['base_url']:
                raise ValueError('Para cambiar el destino utiliza el preset personalizado.')
            parsed = urlsplit(endpoint)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError('El endpoint debe ser HTTPS sin credenciales, parámetros ni fragmentos.')
            object.__setattr__(self, 'base_url', endpoint.rstrip('/'))
            capability = self.response_format or preset['models'].get(self.model, preset['response_format'])
            if capability not in ('none', 'json_object', 'json_schema'):
                raise ValueError('response_format debe ser none, json_object o json_schema.')
            object.__setattr__(self, 'response_format', capability)
            if not isinstance(self.model, str) or not self.model.strip():
                raise ValueError('Elige un modelo del proveedor generativo.')
            # Para deepseek, input_budget es ilimitado en la práctica (128k); usamos num_ctx como referencia.
            if type(self.num_ctx) is not int or not 2048 <= self.num_ctx <= 131072:
                raise ValueError('num_ctx debe ser un entero entre 2048 y 131072.')
        else:
            if not isinstance(self.model, str) or not self.model.strip() or self.model != self.model.strip():
                raise ValueError('Elige explícitamente un modelo generativo instalado en Ollama.')
            if ':cloud' in self.model.lower() or '://' in self.model:
                raise ValueError('Solo se admiten modelos locales instalados.')
            object.__setattr__(self, 'host', local_url(self.host))
            for key, low, high in [('num_batch', 1, 512), ('num_ctx', 2048, 32768),
                                    ('max_output_tokens', 64, 8192), ('context_margin', 128, 4096)]:
                value = getattr(self, key)
                if type(value) is not int or not low <= value <= high:
                    raise ValueError(f'{key} debe ser un entero entre {low} y {high}.')
            if self.max_output_tokens + self.context_margin >= self.num_ctx:
                raise ValueError('El contexto debe reservar espacio para entrada, margen y salida.')
        for key, low, high in [('timeout_seconds', 1, 600), ('temperature', 0, 2)]:
            value = getattr(self, key)
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'{key} debe ser un número entre {low} y {high}.')
        if type(self.think) is not bool:
            raise ValueError('think debe ser true o false.')

    @property
    def is_remote(self):
        return PRESETS[self.provider]['transport'] != 'ollama'

    @property
    def secret_name(self):
        return PRESETS[self.provider]['secret_name']

    @property
    def consent_scope(self):
        return hashlib.sha256(repr(('remote:1', self.provider, self.base_url, self.model, self.data_residency, self.response_format)).encode()).hexdigest()

    @property
    def remote_confirmed(self):
        return self.is_remote and self.remote_consent == self.consent_scope

    def require_consent(self):
        if self.is_remote and not self.remote_confirmed:
            raise ConsentRequiredError('Confirma explícitamente el envío de pregunta y fragmentos al proveedor en Ajustes antes de consultar.')

    @property
    def indicator(self):
        return ('Fragmentos enviados a ' + PRESETS[self.provider]['name'] + ' (' + RESIDENCY_LABELS[self.data_residency] + ')') if self.is_remote else 'Generación local'

    @property
    def input_budget(self):
        return self.num_ctx - self.max_output_tokens - self.context_margin


def load_settings(path: Path) -> GenerationSettings:
    try:
        if path.stat().st_size > 100_000:
            raise ValueError('Configuración generativa demasiado grande.')
        data = yaml.load(path.read_text(encoding='utf-8'), Loader=StrictLoader)
    except (OSError, UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise ValueError('No se pudo leer la configuración generativa.') from None
    if not isinstance(data, dict) or set(data) != {'schema_version', 'generation'} or type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('Se necesitan schema_version: 1 y generation.')
    if not isinstance(data['generation'], dict):
        raise ValueError('generation debe ser un objeto.')
    has_legacy_key = 'api_key' in data['generation']
    legacy_key = data['generation'].pop('api_key', '')
    try:
        settings = GenerationSettings(**data['generation'])
    except TypeError as exc:
        raise ValueError('Campos generativos desconocidos o falta el campo model.') from exc
    if has_legacy_key:
        if not isinstance(legacy_key, str):
            raise ValueError('La clave antigua debe ser texto.')
        if legacy_key.strip():
            set_secret(settings.secret_name or 'deepseek_api_key', legacy_key)
        temporary = path.with_name('.' + path.name + '.' + uuid4().hex)
        try:
            temporary.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding='utf-8')
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        logging.getLogger(__name__).warning('Configuración antigua migrada: credencial retirada del YAML y guardada en el Llavero cuando existía.')
    return settings
