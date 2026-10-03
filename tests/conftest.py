import socket
import warnings
import subprocess

import pytest


@pytest.fixture(autouse=True)
def simulated_ocr(monkeypatch):
    """Las pruebas nunca ejecutan el OCR instalado en el equipo."""
    monkeypatch.setattr('docente_ai.library.ocr.find_ocr', lambda: None)


# TODO: migrar a httpx2 cuando starlette>=1.6 lo adopte plenamente.
# Mientras tanto, suprimir el aviso para mantener el output limpio.
warnings.filterwarnings(
    'ignore',
    message='Using `httpx` with `starlette.testclient` is deprecated',
    category=DeprecationWarning,
)


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Las pruebas no pueden realizar conexiones de red reales")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture(autouse=True)
def simulated_keychain(monkeypatch):
    """Ningún test consulta ni modifica el Llavero real o credenciales del entorno."""
    from docente_ai import secrets
    monkeypatch.delenv('DOCENTE_AI_DEEPSEEK_API_KEY', raising=False)
    monkeypatch.delenv('DOCENTE_AI_MISTRAL_API_KEY', raising=False)
    monkeypatch.delenv('DOCENTE_AI_CUSTOM_API_KEY', raising=False)
    values = {}
    original_run = subprocess.run
    original_which = secrets.shutil.which

    def run(command, **kwargs):
        if command[0] != '/simulado/security':
            return original_run(command, **kwargs)
        action = command[1]
        account = command[command.index('-a') + 1]
        if action == 'add-generic-password':
            values[account] = command[command.index('-w') + 1]
        elif action == 'find-generic-password':
            return subprocess.CompletedProcess(command, 0 if account in values else 44, values.get(account, '') + '\n', '')
        elif action == 'delete-generic-password':
            values.pop(account, None)
        else:
            raise AssertionError('Operación de Llavero inesperada.')
        return subprocess.CompletedProcess(command, 0, '', '')

    monkeypatch.setattr(secrets.shutil, 'which', lambda name: '/simulado/security' if name == 'security' else original_which(name))
    monkeypatch.setattr(secrets.subprocess, 'run', run)
    return values
