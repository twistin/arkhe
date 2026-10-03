"""Panel provisional y sustitución por el resultado validado, sin red real."""

from pathlib import Path
from urllib.parse import urlsplit

import pytest

from test_ui_smoke import synthetic_ui, ORIGIN


def test_panel_streaming_sin_html_y_sustitucion_validada(synthetic_ui):
    playwright = pytest.importorskip('playwright.sync_api', reason='Grupo ui opcional.')
    client, _, answer_id, _ = synthetic_ui
    with playwright.sync_playwright() as driver:
        if not Path(driver.chromium.executable_path).exists():
            pytest.skip('Chromium opcional no instalado.')
        browser = driver.chromium.launch()
        context = browser.new_context()
        def route(intercept):
            request = intercept.request
            url = urlsplit(request.url)
            if url.scheme + '://' + url.netloc != ORIGIN:
                intercept.abort()
                return
            response = client.request(request.method, url.path + ('?' + url.query if url.query else ''),
                                      content=request.post_data_buffer, headers=request.headers)
            intercept.fulfill(status=response.status_code, body=response.content,
                              headers={k: v for k, v in response.headers.items() if k != 'content-length'})
        context.route('**/*', route)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(ORIGIN + '/#asistente')
        page.wait_for_selector('#main h1')
        page.evaluate('''() => {
          const original = window.fetch;
          window.liveDone = false;
          window.cancelReceived = false;
          window.fetch = (url, options) => {
            if (url === '/api/jobs') return Promise.resolve(new Response(JSON.stringify([{
              id: 'live-test', title: 'Redactando', status: window.liveDone ? 'done' : 'running',
              cancellable: true, result: window.liveDone ? {run_id: window.answerId} : null
            }]), {headers: {'Content-Type': 'application/json'}}));
            if (url === '/api/jobs/live-test/events') {
              if (!options.headers['X-Docente-Token']) throw new Error('SSE sin token');
              return Promise.resolve(new Response(new ReadableStream({
                start(controller) { window.liveStream = controller; }
              }), {headers: {'Content-Type': 'text/event-stream'}}));
            }
            if (url === '/api/jobs/live-test/cancel') {
              window.cancelReceived = true;
              return Promise.resolve(new Response('{"accepted":true}'));
            }
            return original(url, options);
          };
        }''')
        page.evaluate('(id) => { window.answerId = id; }', answer_id)
        page.evaluate("async () => (await import('/assets/js/componentes/trabajos.js')).monitor()")
        page.wait_for_function('() => !!window.liveStream')
        def emit(event, data, identifier):
            page.evaluate('''([event, data, id]) => window.liveStream.enqueue(new TextEncoder().encode(
              'id: ' + id + '\\nevent: ' + event + '\\ndata: ' + JSON.stringify(data) + '\\n\\n'))''',
                          [event, data, identifier])
        emit('attempt', {'attempt': 1, 'total': 3}, 1)
        emit('token', {'text': '{"claims":[{"text":"Texto <img src=x onerror=alert(1)> provisional'}, 2)
        panel = page.locator('#live-panel')
        assert panel.get_by_role('heading', name='Borrador sin verificar').is_visible()
        page.wait_for_function("() => document.querySelector('.live-text').textContent.includes('provisional')")
        assert panel.locator('img').count() == 0
        assert '<img' in panel.inner_text()
        emit('repair', {'attempt': 2, 'total': 3, 'error_type': 'quote'}, 3)
        page.wait_for_function("() => !document.querySelector('.live-text').textContent.includes('provisional')")
        panel.get_by_role('button', name='Cancelar consulta').click()
        page.wait_for_function('() => window.cancelReceived')
        assert panel.get_by_role('button', name='Cancelar consulta').is_disabled()
        emit('terminal', {'status': 'cancelled', 'error': 'Consulta cancelada.'}, 4)
        assert panel.get_by_role('heading', name='Consulta cancelada').is_visible()
        assert panel.locator('.live-text').is_hidden()
        assert panel.locator('.live-text').text_content() == ''
        # Otra consulta puede terminar normalmente: la versión documentada sustituye el panel.
        emit('attempt', {'attempt': 1, 'total': 3}, 5)
        page.evaluate('() => { window.liveDone = true; }')
        emit('terminal', {'status': 'done', 'result': {'run_id': answer_id}}, 6)
        page.evaluate("async () => (await import('/assets/js/componentes/trabajos.js')).monitor()")
        page.wait_for_function("() => !document.querySelector('#live-panel') && document.querySelector('.result')")
        assert not errors
        browser.close()
