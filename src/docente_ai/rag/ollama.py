"""Embeddings locales, normalizados y sin truncamiento."""

import math

from docente_ai.llm.local import LocalModelError, LocalOllama

EmbeddingError = LocalModelError


def normalize(vector):
    if not isinstance(vector, list) or not vector or any(type(n) not in (int, float) or not math.isfinite(n) for n in vector):
        raise EmbeddingError('Ollama devolvió un vector vacío, no numérico o no finito.')
    norm = math.hypot(*vector)
    if not math.isfinite(norm) or norm == 0:
        raise EmbeddingError('El embedding tiene norma nula o inválida.')
    return [n / norm for n in vector]


class OllamaEmbedder(LocalOllama):
    capability = 'embedding'
    context_error_hint = ' Reduce chunk_chars; no se trunca texto.'

    def __init__(self, settings, *, transport=None):
        super().__init__(settings, transport=transport)
        self.dimensions = None
        self.keep_alive = 0

    def embed(self, texts: list[str], *, query: bool = False):
        if not self.digest:
            raise EmbeddingError('Inicializa el adaptador antes de solicitar embeddings.')
        self.verify_identity()
        prefix = self.settings.query_prefix if query else self.settings.document_prefix
        data = self.request('POST', '/api/embed', json={
            'model': self.model, 'input': [prefix + text for text in texts],
            'truncate': False, 'keep_alive': self.keep_alive,
        })
        vectors = data.get('embeddings')
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise EmbeddingError('El número de embeddings no coincide con las entradas.')
        normalized = [normalize(vector) for vector in vectors]
        dimensions = {len(vector) for vector in normalized}
        if len(dimensions) != 1 or (self.dimensions is not None and dimensions != {self.dimensions}):
            raise EmbeddingError('Dimensiones de embeddings incompatibles.')
        self.dimensions = len(normalized[0])
        self.verify_identity()
        return normalized

    def __exit__(self, *args):
        try:
            if self.keep_alive and self.digest:
                self.request('POST', '/api/embed', json={'model': self.model, 'input': [], 'keep_alive': 0})
        finally:
            super().__exit__(*args)
