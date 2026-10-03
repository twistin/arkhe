"""Compatibilidad de importación; DeepSeek utiliza el adaptador genérico."""
import time
from docente_ai.llm.openai_compatible import OpenAICompatibleGenerator
from docente_ai.generation.errors import ProviderError

DeepSeekGenerator = OpenAICompatibleGenerator
DeepSeekError = ProviderError
