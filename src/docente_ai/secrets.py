"""Credenciales fuera de los archivos y del historial de la aplicación."""

import logging
import os
import re
import shutil
import subprocess
import traceback


def _variable(name):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
        raise ValueError('Nombre de credencial inválido.')
    return 'DOCENTE_AI_' + name.upper()


def _security(arguments):
    variable = _variable(arguments[arguments.index('-a') + 1])
    executable = shutil.which('security')
    if not executable:
        raise ValueError(f'El Llavero no está disponible; utiliza la variable de entorno {variable}.')
    try:
        return subprocess.run([executable, *arguments], capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError):
        raise ValueError(f'No se pudo acceder al Llavero; utiliza la variable de entorno {variable}.') from None


def get_secret(name):
    """Resuelve primero el entorno y después el servicio docente-ai del Llavero."""
    variable = _variable(name)
    if os.environ.get(variable):
        return os.environ[variable].strip()
    result = _security(['find-generic-password', '-s', 'docente-ai', '-a', name.lower(), '-w'])
    if result.returncode == 44:
        return None
    if result.returncode:
        raise ValueError('No se pudo consultar la credencial en el Llavero.')
    return result.stdout.strip() or None


def set_secret(name, value):
    """Guarda una credencial en el Llavero sin mostrar la salida del comando."""
    _variable(name)
    if not isinstance(value, str) or not value.strip() or '\x00' in value:
        raise ValueError('La credencial debe ser un texto no vacío.')
    result = _security(['add-generic-password', '-U', '-s', 'docente-ai', '-a', name.lower(), '-w', value.strip()])
    if result.returncode:
        raise ValueError('No se pudo guardar la credencial en el Llavero.')


def delete_secret(name):
    """Elimina la entrada del Llavero; una variable de entorno sigue teniendo prioridad."""
    _variable(name)
    result = _security(['delete-generic-password', '-s', 'docente-ai', '-a', name.lower()])
    if result.returncode not in (0, 44):
        raise ValueError('No se pudo borrar la credencial del Llavero.')


def secret_configured(name):
    try:
        return bool(get_secret(name))
    except ValueError:
        return False


def redact(value):
    return re.sub(r'sk-[A-Za-z0-9]{16,}', '[CLAVE OCULTA]', value)


class SecretFilter(logging.Filter):
    def filter(self, record):
        record.msg = redact(record.getMessage())
        record.args = ()
        if record.exc_text:
            record.exc_text = redact(record.exc_text)
        if record.exc_info:
            record.exc_text = redact(''.join(traceback.format_exception(*record.exc_info)))
            record.exc_info = None
        if record.stack_info:
            record.stack_info = redact(record.stack_info)
        return True


def install_log_filter():
    """Protege handlers existentes y futuros, incluidos los de Uvicorn."""
    if getattr(logging.Handler, '_docente_secret_filter', False):
        return
    original_handle = logging.Handler.handle
    original_format = logging.Formatter.format
    filter_instance = SecretFilter()

    def handle(handler, record):
        if filter_instance not in handler.filters:
            handler.addFilter(filter_instance)
        return original_handle(handler, record)

    def format_record(formatter, record):
        return redact(original_format(formatter, record))

    logging.Handler.handle = handle
    logging.Formatter.format = format_record
    logging.Handler._docente_secret_filter = True
    for logger in [logging.getLogger(), *logging.Logger.manager.loggerDict.values()]:
        if isinstance(logger, logging.Logger):
            for handler in logger.handlers:
                handler.addFilter(filter_instance)
