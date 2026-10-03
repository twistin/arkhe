"""Servidor y proxy usando exclusivamente un espacio temporal vacío."""
import re
import pytest
from starlette.testclient import TestClient
from docente_ai.web.app import create_app
from docente_ai.web.server import ServerSettings


@pytest.fixture
def server(tmp_path):
    app = create_app(tmp_path, server=ServerSettings('arkhe.ejemplo.es'))
    with TestClient(app, base_url='https://arkhe.ejemplo.es', client=('172.30.0.2', 123)) as client:
        client.headers.update({'X-Forwarded-Proto': 'https', 'X-Forwarded-For': '203.0.113.4'})
        yield client, app


def token(client):
    html = client.get('/').text
    value = re.search(r'name="docente-token" content="([^"]+)"', html).group(1)
    client.headers['X-Docente-Token'] = value


def test_host_y_acciones_locales(server):
    client, app = server
    assert client.get('/', headers={'Host': 'localhost'}).status_code == 403
    assert client.get('/', headers={'Host': 'arkhe.ejemplo.es:80'}).status_code == 403
    assert client.get('/', headers={'X-Forwarded-Proto': 'http'}).status_code == 403
    assert client.get('/', headers={'X-Forwarded-For': '203.0.113.4, 1.2.3.4'}).status_code == 403
    token(client)
    state = client.get('/api/state')
    assert state.json()['server_mode'] is True
    assert str(app.state.workspace.root) not in state.text
    assert state.json()['config']['groups'] == []
    for path in ('shutdown', 'reveal', 'reveal-diary', 'records/123/reveal'):
        assert client.post('/api/' + path, json={}).status_code == 403


def test_proxy_no_configurado_no_puede_falsificar_cabeceras(tmp_path):
    with TestClient(create_app(tmp_path, server=ServerSettings('arkhe.ejemplo.es')),
                    base_url='https://arkhe.ejemplo.es', client=('172.30.0.9', 1)) as client:
        assert client.get('/', headers={'X-Forwarded-Proto': 'https', 'X-Forwarded-For': '1.2.3.4'}).status_code == 403


def test_configuracion_servidor_rechaza_escucha_publica():
    for bind in ('0.0.0.0', '127.0.0.1', '8.8.8.8'):
        with pytest.raises(ValueError): ServerSettings('arkhe.ejemplo.es', bind=bind)
