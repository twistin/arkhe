import socket
import warnings

import pytest


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
