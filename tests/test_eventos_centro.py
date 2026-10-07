"""Calendario del centro con eventos ficticios y sin conexiones reales."""

import json

import pytest

from docente_ai.teaching.eventos_centro import cargar_eventos, calendario_eventos
from test_web import web
from test_ui_smoke import synthetic_ui


def evento(**cambios):
    return {'id': 'evento-ficticio', 'titulo': 'Audición ficticia',
            'inicio': '2027-03-03T17:30:00+01:00', 'lugar': 'Aula de prueba',
            'prioritario': True, 'fuente': 'Documento ficticio', **cambios}


def guardar(root, datos):
    (root / 'config').mkdir(exist_ok=True)
    (root / 'config/eventos-centro.json').write_text(json.dumps(datos), encoding='utf-8')


def test_eventos_ordenados_y_sin_configuracion(tmp_path):
    assert cargar_eventos(tmp_path) == []
    guardar(tmp_path, [evento(), evento(id='anterior', inicio='2026-12-14T19:00:00+01:00')])
    assert [e['id'] for e in cargar_eventos(tmp_path)] == ['anterior', 'evento-ficticio']


@pytest.mark.parametrize('datos', [
    [evento(), evento()], [evento(inicio='2027-03-03T17:30:00')],
    [evento(prioritario='sí')], [evento(titulo='Texto\r\nBEGIN:VEVENT')],
])
def test_eventos_invalidos_no_se_publican(tmp_path, datos):
    guardar(tmp_path, datos)
    with pytest.raises(ValueError):
        cargar_eventos(tmp_path)


def test_exportacion_prioritaria_con_avisos_zona_y_uid_estable():
    datos = [evento(titulo='Guitarra ' + 'á' * 100),
             evento(id='no-prioritario', prioritario=False)]
    ics = calendario_eventos(datos, solo_prioritarios=True)
    assert ics.count('BEGIN:VEVENT') == 1
    assert 'DTSTART:20270303T163000Z' in ics
    assert 'TRIGGER:-PT1440M' in ics and 'TRIGGER:-PT60M' in ics
    assert 'DTEND' not in ics
    assert 'UID:evento-ficticio@arkhe.local' in ics
    assert all(len(linea.encode('utf-8')) <= 75 for linea in ics.split('\r\n'))
    assert '\r\n ' in ics
    assert 'DTSTART:20270518T170000Z' in calendario_eventos([evento(inicio='2027-05-18T19:00:00+02:00')])


def test_api_eventos_separados_de_clases_y_protegidos(web):
    client, ws = web
    guardar(ws.root, [evento(), evento(id='secundario', prioritario=False)])
    estado = client.get('/api/state').json()
    assert len(estado['eventos_centro']) == 2
    assert all(s.get('id') != 'evento-ficticio' for s in estado['agenda']['sessions'])
    assert client.get('/api/eventos-centro.ics?prioritarios=1').text.count('BEGIN:VEVENT') == 1
    assert client.get('/api/eventos-centro.ics').text.count('BEGIN:VEVENT') == 2
    assert client.get('/api/eventos-centro.ics', headers={'X-Docente-Token': 'incorrecto'}).status_code == 403


@pytest.mark.ui
@pytest.mark.parametrize('ancho', [1440, 390])
def test_panel_eventos_en_navegador(synthetic_ui, tmp_path, ancho):
    from datetime import datetime, timezone
    from urllib.parse import urlsplit
    playwright = pytest.importorskip('playwright.sync_api')
    client = synthetic_ui[0]
    with playwright.sync_playwright() as driver:
        from pathlib import Path
        if not Path(driver.chromium.executable_path).exists():
            pytest.skip('Chromium opcional no instalado.')
        browser = driver.chromium.launch()
        contexto = browser.new_context(viewport={'width': ancho, 'height': 1000},
                                       locale='es-ES', timezone_id='Europe/Madrid')
        def interceptar(ruta):
            peticion = ruta.request
            url = urlsplit(peticion.url)
            assert url.netloc == '127.0.0.1:8765'
            respuesta = client.request(peticion.method, url.path + ('?' + url.query if url.query else ''),
                                       content=peticion.post_data_buffer, headers=peticion.headers)
            contenido = respuesta.content
            if url.path == '/api/state':
                estado = respuesta.json()
                estado['eventos_centro'] = [
                    evento(id='general', titulo='Evento general', inicio='2026-11-03T17:00:00+01:00',
                           prioritario=False),
                    evento(titulo='Audición · Guitarra', inicio='2026-12-14T19:00:00+01:00',
                           lugar='Aula Polivalente'),
                    evento(id='hostil', titulo='<img src=x onerror="alert(1)">', prioritario=False),
                ]
                contenido = json.dumps(estado).encode()
            ruta.fulfill(status=respuesta.status_code, body=contenido,
                         headers={k: v for k, v in respuesta.headers.items() if k != 'content-length'})
        contexto.route('**/*', interceptar)
        pagina = contexto.new_page()
        errores = []
        pagina.on('pageerror', lambda error: errores.append(str(error)))
        pagina.clock.set_fixed_time(datetime(2026, 10, 6, tzinfo=timezone.utc))
        pagina.goto('http://127.0.0.1:8765')
        pagina.locator('.daily-agenda').wait_for()
        assert pagina.locator('.evento-destacado h2').inner_text() == 'Audición · Guitarra'
        assert '19:00' in pagina.locator('.evento-destacado p').inner_text()
        pagina.locator('.eventos-centro summary').click()
        assert pagina.locator('.evento-centro').count() == 3
        assert pagina.locator('.eventos-centro img').count() == 0
        assert pagina.locator('.eventos-centro').evaluate('(n) => n.scrollWidth <= n.clientWidth')
        pagina.locator('.eventos-centro').screenshot(path=str(tmp_path / f'eventos-{ancho}.png'))
        assert not errores
        browser.close()
