"""Servidor y proxy usando exclusivamente un espacio temporal vacío."""
import re
import pytest
from starlette.testclient import TestClient
from docente_ai.web.app import create_app
from docente_ai.web.server import ServerSettings


@pytest.fixture
def server(tmp_path):
    from docente_ai.web.auth import create_user
    path = tmp_path / 'auth/user.json'
    create_user(path, 'docente', 'contraseña-de-prueba-segura')
    app = create_app(tmp_path / 'workspace', server=ServerSettings('arkhe.ejemplo.es', auth_file=str(path)))
    with TestClient(app, base_url='https://arkhe.ejemplo.es', client=('172.30.0.2', 123)) as client:
        client.headers.update({'X-Forwarded-Proto': 'https', 'X-Forwarded-For': '203.0.113.4'})
        login(client)
        yield client, app


def login(client, password='contraseña-de-prueba-segura'):
    html = client.get('/login').text
    csrf = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
    return client.post('/login', data={'username': 'docente', 'password': password, 'csrf': csrf},
                       headers={'Origin': 'https://arkhe.ejemplo.es'}, follow_redirects=False)


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


def test_sesion_segura_logout_y_limite(server):
    client, app = server
    client.cookies.clear()
    assert client.get('/api/state').status_code == 401
    assert client.get('/', follow_redirects=False).status_code == 303
    response = login(client)
    cookie = response.headers['set-cookie'].lower()
    assert 'secure' in cookie and 'httponly' in cookie and 'samesite=strict' in cookie
    token(client)
    assert client.get('/api/state').status_code == 200
    assert client.post('/api/logout', json={}).status_code == 200
    assert client.get('/api/state').status_code == 401
    for i in range(5): assert login(client, 'incorrecta-de-prueba').status_code == 401
    assert login(client).status_code == 429


def test_hash_no_conserva_password_y_caducidad(tmp_path):
    from docente_ai.web.auth import AuthStore, create_user
    path = tmp_path / 'user.json'
    create_user(path, 'docente', 'contraseña-de-prueba-segura')
    assert 'contraseña-de-prueba-segura' not in path.read_text()
    clock = [0]
    store = AuthStore(path, clock=lambda: clock[0])
    session, status = store.login('docente', 'contraseña-de-prueba-segura', '1.2.3.4')
    assert status == 200 and store.authenticated(session)
    clock[0] = 8 * 3600 + 1
    assert not store.authenticated(session)


def test_login_no_admite_csrf_y_token_sin_sesion(server):
    client, app = server
    token(client)
    client.cookies.clear()
    assert client.get('/api/state').status_code == 401
    assert client.post('/login', data={'username': 'docente', 'password': 'contraseña-de-prueba-segura',
                                     'csrf': 'inventado'}).status_code == 403
