"""Navegador opcional: aplicación ASGI sintética, sin sockets ni datos personales."""

from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

import pytest
from starlette.testclient import TestClient

from docente_ai.agents.pedagogy import context_for
from docente_ai.config import load
from docente_ai.generation.service import ask
from docente_ai.generation.settings import GenerationSettings
from docente_ai.library.service import import_document, authorize_document
from docente_ai.rag.service import index_library
from docente_ai.rag.settings import RagSettings
from docente_ai.storage import import_config
from docente_ai.web.app import create_app
from docente_ai.web.workspace import Workspace, daily_agenda
from test_generation import FakeEmbedder, FakeGenerator, TEXT, EXAMPLE
from test_pedagogy import proposal

BASELINE = Path(__file__).parent / 'ui_baseline'
VIEWS = ('biblioteca', 'asistente', 'propuestas', 'diario', 'ajustes')
ORIGIN = 'http://127.0.0.1:8765'
FIXED_TIME = datetime(2026, 9, 7, 10, 15, tzinfo=timezone.utc)


@pytest.fixture
def synthetic_ui(tmp_path, monkeypatch):
    """Cada API usa el servidor real en memoria, con modelos de prueba."""
    db = tmp_path / 'data/docente.sqlite3'
    import_config(db, load(EXAMPLE))
    config = tmp_path / 'config'
    config.mkdir()
    (config / 'rag.yaml').write_text('schema_version: 1\nembeddings:\n  model: embed:1\n')
    for name in ('generation', 'pedagogy'):
        (config / f'{name}.yaml').write_text('schema_version: 1\ngeneration:\n  model: gen:1\n  num_ctx: 8192\n  max_output_tokens: 1536\n')
    path = tmp_path / 'fuente-sintetica.txt'
    path.write_text(TEXT)
    doc = import_document(db, path, category='documental', subjects=['historia-i'],
                          values={'title': 'El pulso musical · Fuente sintética', 'authors': ['Autora de prueba']})
    authorize_document(db, doc['document_id'], enabled=True)
    rag, generation = RagSettings(model='embed:1'), GenerationSettings(model='gen:1', num_ctx=8192, max_output_tokens=1536)
    index_library(db, rag, FakeEmbedder())
    run = ask(db, rag, generation, 'La música en el Antiguo Egipto', subject='historia-i',
              pedagogy_context=context_for(db, 'historia-3gp', 30), embedder_factory=FakeEmbedder,
              generator_factory=lambda settings: FakeGenerator(settings, response=proposal()))
    answer = ask(db, rag, generation, '¿Qué es el pulso?', subject='historia-i',
                 embedder_factory=FakeEmbedder, generator_factory=FakeGenerator)
    # Solo normalizar fechas en esta base temporal para las capturas repetibles.
    from docente_ai.storage import connect
    with connect(db) as connection, connection:
        connection.execute('UPDATE generation_runs SET created_at=?', (FIXED_TIME.isoformat(),))
    monkeypatch.setattr('docente_ai.web.workspace.daily_agenda', lambda raw: daily_agenda(raw, date(2026, 9, 7)))
    ws = Workspace(tmp_path, embedder_factory=FakeEmbedder)
    ws.model_status = lambda: {'connected': True, 'models': ['gen:1'], 'ollama_models': ['gen:1'],
                              'embedding_models': ['embed:1'], 'generation': 'gen:1', 'embeddings': 'embed:1',
                              'provider': 'ollama', 'message': '', 'api_key_configured': False}
    original_state = ws.state
    def state():
        value = original_state()
        value['knowledge_path'] = '/espacio-sintetico/Conocimiento'
        value['records'] = [{'id': 'sesion-sintetica', 'group_id': 'historia-3gp', 'session_date': '2026-09-07',
                             'duration_minutes': 30, 'topic': 'El pulso musical',
                             'feedback': {'what_worked': 'Las palmas mantuvieron el pulso.',
                                          'next_session_note': 'Practicar los silencios.'}}]
        return value
    ws.state = state
    with TestClient(create_app(tmp_path, workspace=ws), base_url=ORIGIN) as client:
        yield client, run['id'], answer['id'], doc['document_id']


def compare_capture(image_path, baseline_path):
    from PIL import Image, ImageChops
    current, baseline = Image.open(image_path).convert('RGB'), Image.open(baseline_path).convert('RGB')
    if current.size != baseline.size:
        return {'size': list(current.size), 'baseline_size': list(baseline.size), 'changed_pixels': None}
    difference = ImageChops.difference(current, baseline)
    channels = difference.split()
    mask = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    changed = sum(mask.histogram()[1:])
    if changed:
        difference.save(image_path.with_name(image_path.stem + '-diff.png'))
    return {'size': list(current.size), 'changed_pixels': changed,
            'changed_percent': round(changed * 100 / (current.width * current.height), 6)}


@pytest.mark.ui
@pytest.mark.parametrize(('profile', 'viewport'), [('escritorio', {'width': 1440, 'height': 1000}),
                                                  ('movil', {'width': 390, 'height': 844})])
def test_ui_smoke(synthetic_ui, tmp_path, profile, viewport):
    playwright = pytest.importorskip('playwright.sync_api', reason='Instala el grupo opcional ui.')
    pytest.importorskip('PIL', reason='Pillow es opcional para comparar capturas.')
    client, proposal_id, answer_id, document_id = synthetic_ui
    update = os.environ.get('DOCENTE_UI_UPDATE_BASELINE') == '1'
    update_views = set(os.environ.get('DOCENTE_UI_UPDATE_VIEWS', '').split(',')) - {''}
    capture_dir = Path(os.environ.get('DOCENTE_UI_CAPTURE_DIR', str(tmp_path / 'capturas')))
    capture_dir.mkdir(parents=True, exist_ok=True)
    report = {'profile': profile, 'console_errors': [], 'page_errors': [], 'external_requests': [], 'captures': {}}
    print_html = None
    with playwright.sync_playwright() as driver:
        if not Path(driver.chromium.executable_path).exists():
            pytest.skip('Chromium opcional no instalado: playwright install chromium.')
        browser = driver.chromium.launch(args=['--disable-gpu', '--disable-skia-runtime-opts'])
        report['browser'] = browser.version
        environment = {'platform': sys.platform, 'browser': browser.version, 'viewport': viewport}
        metadata = BASELINE / (profile + '.json')
        comparable = update or (metadata.exists() and json.loads(metadata.read_text()) == environment)
        context = browser.new_context(viewport=viewport, device_scale_factor=1, locale='es-ES', timezone_id='Europe/Madrid',
                                      color_scheme='light', service_workers='block')
        def route(request_route):
            request = request_route.request
            url = urlsplit(request.url)
            if url.scheme + '://' + url.netloc != ORIGIN:
                report['external_requests'].append(request.url)
                request_route.abort()
                return
            if url.path == '/__impresion__':
                request_route.fulfill(status=200, body=print_html, content_type='text/html',
                                      headers={'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"})
                return
            # Intercepción completa: ni Python ni Chromium abren conexiones HTTP.
            response = client.request(request.method, url.path + ('?' + url.query if url.query else ''),
                                      content=request.post_data_buffer, headers=request.headers)
            request_route.fulfill(status=response.status_code, body=response.content,
                                  headers={k: v for k, v in response.headers.items() if k != 'content-length'})
        context.route('**/*', route)
        page = context.new_page()
        def observe(page):
            page.on('console', lambda message: report['console_errors'].append(message.text) if message.type == 'error' else None)
            page.on('pageerror', lambda error: report['page_errors'].append(str(error)))
        observe(page)
        page.clock.set_fixed_time(FIXED_TIME)
        def capture(target, name):
            target.evaluate('() => document.fonts.ready')
            # Calentar el rasterizador SVG tras cambiar el viewport de captura
            # completa; evita variaciones de un nivel RGB en tres píxeles.
            target.screenshot(full_page=True, animations='disabled', caret='hide')
            path = capture_dir / f'{profile}-{name}.png'
            target.screenshot(path=str(path), full_page=True, animations='disabled', caret='hide')
            baseline_path = BASELINE / path.name
            if update and (not update_views or name in update_views):
                BASELINE.mkdir(exist_ok=True)
                baseline_path.write_bytes(path.read_bytes())
                report['captures'][name] = {'changed_pixels': 0, 'baseline_created': True}
            elif comparable:
                assert baseline_path.exists(), f'Falta la referencia {baseline_path.name}'
                report['captures'][name] = compare_capture(path, baseline_path)
            else:
                report['captures'][name] = {'comparison_skipped': 'Entorno distinto al de referencia.'}
        for view in VIEWS:
            page.goto(ORIGIN + '/#' + view)
            page.wait_for_function("() => document.querySelector('#main h1') && document.querySelector('#connection').textContent.includes('conectado')")
            assert page.locator(f'[data-nav="{view}"]').get_attribute('aria-current') == 'page'
            capture(page, view)
        page.goto(ORIGIN + '/#ajustes')
        assert page.get_by_text('Lunes · 17:00–18:00 · Aula 1', exact=True).is_visible()
        assert page.get_by_text('2026-10-12 · Clase cancelada', exact=True).is_visible()
        assert page.get_by_text('2026-10-19 · 18:00–19:00 · Aula 2', exact=True).is_visible()
        empty_html = page.evaluate("""async () => {
            const {store} = await import('/assets/js/state.js');
            const {schedulePanel} = await import('/assets/js/vistas/ajustes.js');
            const previous = store.state.config;
            try {
                store.state.config = {groups: [], schedule_rules: [], calendar_exceptions: []};
                return schedulePanel();
            } finally { store.state.config = previous; }
        }""")
        assert 'Crea grupos y horarios' in empty_html
        assert 'Historia 5' not in empty_html
        # Abrir respuesta y fuente real del espacio temporal: acciones cruzadas.
        if profile == 'escritorio':  # El contexto lateral se oculta en móvil por diseño.
            page.goto(ORIGIN + '/#asistente')
            page.locator(f'[data-run="{answer_id}"]').click()
            page.locator('.result').wait_for()
        page.goto(ORIGIN + '/#biblioteca')
        page.locator(f'[data-document="{document_id}"]').click()
        page.locator('dialog .text-preview').wait_for()
        page.locator('[data-action="close-dialog"]').click()
        page.goto(ORIGIN + '/#propuestas')
        page.locator(f'[data-run="{proposal_id}"]').click()
        page.locator('[data-student-run]').click()
        page.locator('.student-handout').wait_for()
        # Cubrir los dos controles inline que se retirarán en el tercer commit.
        tabs = page.locator('.student-dialog .egypt-tab-btn')
        tabs.nth(1).click()
        assert page.locator('.student-dialog #egypt-page-2').is_visible()
        tabs.nth(0).click()
        page.locator('[data-action="print-student"]').click()
        frame = page.frame_locator('#student-print-frame')
        frame.locator('.student-handout').wait_for(state='attached')
        print_html = frame.locator('html').evaluate('(element) => element.outerHTML')
        printed = context.new_page()
        observe(printed)
        printed.emulate_media(media='print')
        printed.goto(ORIGIN + '/__impresion__')
        printed.locator('.student-handout').wait_for()
        capture(printed, 'impresion')
        if update:
            metadata.write_text(json.dumps(environment, ensure_ascii=False, indent=2) + '\n')
        browser.close()
    (capture_dir / f'{profile}-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    assert not report['external_requests'], report
    assert not report['console_errors'] and not report['page_errors'], report
    assert all(item.get('changed_pixels', 0) == 0 for item in report['captures'].values()), report
