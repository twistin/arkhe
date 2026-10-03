"""Configuración generativa independiente del modelo de embeddings."""

from dataclasses import dataclass
import math
from pathlib import Path

import yaml

from docente_ai.config import StrictLoader
from docente_ai.doctor import DEFAULT_HOST, local_url


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
    # Clave de API para proveedores externos. Vacío = local.
    api_key: str = ''

    def __post_init__(self):
        if self.provider not in ('ollama', 'deepseek'):
            raise ValueError("provider debe ser 'ollama' o 'deepseek'.")
        if self.provider == 'deepseek':
            if not isinstance(self.model, str) or not self.model.strip():
                raise ValueError('Elige un modelo de DeepSeek (p.ej. deepseek-chat o deepseek-reasoner).')
            if not isinstance(self.api_key, str):
                raise ValueError('api_key debe ser una cadena de texto.')
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
    def input_budget(self):
        return self.num_ctx - self.max_output_tokens - self.context_margin


def load_settings(path: Path) -> GenerationSettings:
    try:
        if path.stat().st_size > 100_000:
            raise ValueError('Configuración generativa demasiado grande.')
        data = yaml.load(path.read_text(encoding='utf-8'), Loader=StrictLoader)
    except (OSError, UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise ValueError(f'No se pudo leer la configuración generativa: {exc}') from exc
    if not isinstance(data, dict) or set(data) != {'schema_version', 'generation'} or type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('Se necesitan schema_version: 1 y generation.')
    if not isinstance(data['generation'], dict):
        raise ValueError('generation debe ser un objeto.')
    try:
        return GenerationSettings(**data['generation'])
    except TypeError as exc:
        raise ValueError('Campos generativos desconocidos o falta el campo model.') from exc
