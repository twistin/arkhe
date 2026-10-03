"""Tipos de fallo para decidir reparaciones sin comparar mensajes."""


class GenerationError(ValueError):
    error_type = 'generation'


class RecoverableGenerationError(GenerationError):
    error_type = 'contract'

    def __init__(self, message, *, content='', metrics=None):
        super().__init__(message)
        self.content = content
        self.metrics = metrics or {}


class NonRecoverableGenerationError(GenerationError):
    error_type = 'provider'


class ProviderError(GenerationError):
    error_type = 'provider'


class GenerationLengthError(RecoverableGenerationError, ProviderError):
    error_type = 'length'


class NetworkError(ProviderError, NonRecoverableGenerationError):
    error_type = 'network'


class AuthorizationError(ProviderError, NonRecoverableGenerationError):
    error_type = 'authorization'


class SourceChangedError(NonRecoverableGenerationError):
    error_type = 'source_changed'


class ContextBudgetError(ProviderError, NonRecoverableGenerationError):
    error_type = 'context_budget'
