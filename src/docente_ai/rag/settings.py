"""Configuración explícita del modelo y de la fragmentación."""

from dataclasses import asdict, dataclass
import math
from pathlib import Path

import yaml

from docente_ai.config import StrictLoader
from docente_ai.doctor import DEFAULT_HOST, local_url


@dataclass(frozen=True)
class RagSettings:
    model: str
    host: str = DEFAULT_HOST
    timeout_seconds: float = 60
    chunk_chars: int = 1200
    overlap_chars: int = 150
    batch_size: int = 8
    document_prefix: str = ''
    query_prefix: str = ''

    def __post_init__(self):
        if not isinstance(self.model, str) or not self.model.strip() or self.model != self.model.strip():
            raise ValueError('Elige explícitamente un modelo de embeddings instalado en Ollama.')
        if ':cloud' in self.model.lower() or '://' in self.model:
            raise ValueError('Solo se admiten modelos locales instalados, no modelos cloud.')
        object.__setattr__(self, 'host', local_url(self.host))
        if type(self.timeout_seconds) not in (int, float) or not math.isfinite(self.timeout_seconds) or not 0 < self.timeout_seconds <= 300:
            raise ValueError('timeout_seconds debe estar entre 0 y 300 segundos, excluido 0.')
        for key, low, high in [('chunk_chars', 100, 8000), ('overlap_chars', 0, 7999), ('batch_size', 1, 32)]:
            value = getattr(self, key)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'{key} debe ser un entero entre {low} y {high}.')
        if self.overlap_chars >= self.chunk_chars:
            raise ValueError('overlap_chars debe ser menor que chunk_chars.')
        for value in (self.document_prefix, self.query_prefix):
            if not isinstance(value, str) or len(value) > 2000:
                raise ValueError('Los prefijos deben ser texto de hasta 2000 caracteres.')

    def representation(self):
        # Host/timeout/lote no cambian el espacio vectorial; modelo/digest se
        # conservan por separado. No mezclar fragmentaciones ni prefijos.
        return {key: value for key, value in asdict(self).items() if key not in {'host', 'timeout_seconds', 'batch_size', 'model'}} | {'chunker': 'chars-boundaries:1', 'normalization': 'l2-float32:1'}


def load_settings(path: Path) -> RagSettings:
    try:
        if path.stat().st_size > 100_000:
            raise ValueError('La configuración RAG es demasiado grande.')
        data = yaml.load(path.read_text(encoding='utf-8'), Loader=StrictLoader)
    except (OSError, UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise ValueError(f'No se pudo leer la configuración RAG: {exc}') from exc
    if not isinstance(data, dict) or set(data) - {'schema_version', 'embeddings'} or data.get('schema_version') != 1 or type(data.get('schema_version')) is not int:
        raise ValueError('La configuración RAG necesita schema_version: 1 y embeddings.')
    values = data.get('embeddings')
    if not isinstance(values, dict):
        raise ValueError('embeddings debe ser un objeto.')
    try:
        return RagSettings(**values)
    except TypeError as exc:
        raise ValueError('Campos de embeddings desconocidos o falta el campo model.') from exc
