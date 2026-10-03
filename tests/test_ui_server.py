"""Smoke opcional del espacio servidor vacío, sin sockets ni servicios de IA."""
from pathlib import Path
from urllib.parse import urlsplit
import pytest
from test_server import server


@pytest.mark.ui
def test_interfaz_servidor_vacia(server):
    playwright = pytest.importorskip('playwright.sync_api')
    client, _ = server
    origin = 'https://arkhe.ejemplo.es'
    with playwright.sync_playwright() as driver:
        if not Path(driver.chromium.executable_path).exists():
            pytest.skip('Chromium opcional no instalado.')
        browser = driver.chromium.launch()
        context = browser.new_context(locale='es-ES')
        context.add_cookies([{'name': cookie.name, 'value': cookie.value, 'url': origin,
                             'secure': True, 'httpOnly': True, 'sameSite': 'Strict'}
                            for cookie in client.cookies.jar])
        external, errors = [], []
        def route(intercept):
            request, url = intercept.request, urlsplit(intercept.request.url)
            if url.netloc != 'arkhe.ejemplo.es':
                external.append(request.url)
                intercept.abort()
                return
            response = client.request(request.method, url.path + ('?' + url.query if url.query else ''),
                                      content=request.post_data_buffer, headers=request.headers,
                                      follow_redirects=False)
            intercept.fulfill(status=response.status_code, body=response.content,
                              headers={k: v for k, v in response.headers.items()
                                       if k not in ('content-length', 'set-cookie')})
        context.route('**/*', route)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
        for view in ('biblioteca', 'asistente', 'propuestas', 'diario', 'ajustes'):
            page.goto(origin + '/#' + view)
            page.wait_for_selector('#main h1')
            for action in ('reveal', 'reveal-diary', 'shutdown', 'shutdown-dialog'):
                assert page.locator('[data-action="' + action + '"]:visible').count() == 0
        assert page.get_by_role('button', name='Cerrar sesión').is_visible()
        assert not external and not errors
        browser.close()
