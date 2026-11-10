"""Pruebas de la generación de presentaciones para proyectar en el aula."""

import re
import pytest
from starlette.testclient import TestClient

from docente_ai.config import load
from docente_ai.generation.render import (
    render_presentation_md,
    render_presentation_html,
    _build_presentation_slides,
)
from docente_ai.generation.service import ask
from docente_ai.storage import import_config
from docente_ai.web.app import create_app
from docente_ai.web.workspace import Workspace
from test_generation import FakeEmbedder, FakeGenerator, EXAMPLE
from test_material_alumnado import _make_dummy_polyphony_run


def test_build_presentation_slides_estructura_completa():
    run = _make_dummy_polyphony_run()
    slides = _build_presentation_slides(run)

    tipos = [s['tipo'] for s in slides]
    assert 'portada' in tipos
    assert 'objetivos' in tipos
    assert 'concepto' in tipos
    assert 'actividad' in tipos
    assert 'cierre' in tipos

    portada = next(s for s in slides if s['tipo'] == 'portada')
    assert portada['titulo'] == 'Polifonía del siglo XV'
    assert any('Historia de la Música' in m for m in portada['metadatos'])
    assert any('60 min' in m for m in portada['metadatos'])

    objetivos = next(s for s in slides if s['tipo'] == 'objetivos')
    assert len(objetivos['items']) >= 2
    assert any('cantus firmus' in o.lower() for o in objetivos['items'])

    conceptos = [s for s in slides if s['tipo'] == 'concepto']
    assert len(conceptos) >= 2
    # Comprobar que no quedan identificadores de fuentes crudos como "S1"
    for c in conceptos:
        assert not re.search(r'\bS\d+\b', c['resumen'])


def test_render_presentation_md_formato_y_limpieza():
    run = _make_dummy_polyphony_run()
    md = render_presentation_md(run)

    assert isinstance(md, str)
    slides = md.split('\n\n---\n\n')
    assert len(slides) >= 5, f"Se esperaban al menos 5 diapositivas, se obtuvieron {len(slides)}"

    # Portada
    assert '# Polifonía del siglo XV' in slides[0]
    assert 'Presentación pedagógica · Arkhé' in slides[0]

    # Objetivos
    assert '## ¿Qué vamos a trabajar hoy?' in slides[1]

    # Actividades
    act_slides = [s for s in slides if '## Actividad' in s]
    assert len(act_slides) == 2
    assert '⏱️ 20 min' in act_slides[0]

    # Cierre
    assert 'Cierre de la sesión' in slides[-1]

    # Sin filtración de fuentes crudas ni etiquetas de estado
    assert 'quote_' not in md
    assert 'verificado: false' not in md


def test_render_presentation_html_autocontrol_y_marca():
    run = _make_dummy_polyphony_run()
    html_output = render_presentation_html(run)

    assert html_output.startswith('<!doctype html>')
    assert '<title>Polifonía del siglo XV · Presentación Arkhé</title>' in html_output
    assert 'Arkhé' in html_output
    assert 'Enjambre' not in html_output
    assert 'enjambre' not in html_output

    # Elementos interactivos del visor de proyección
    assert 'class="slide active"' in html_output
    assert 'id="btn-prev"' in html_output
    assert 'id="btn-next"' in html_output
    assert 'id="btn-fs"' in html_output
    assert 'id="btn-print"' in html_output

    # Script de navegación por teclado integrado
    assert "ArrowRight" in html_output
    assert "requestFullscreen" in html_output
    assert "@media print" in html_output


@pytest.fixture
def web_with_run(tmp_path):
    import_config(tmp_path / 'data/docente.sqlite3', load(EXAMPLE))
    config = tmp_path / 'config'
    config.mkdir()
    (config / 'rag.yaml').write_text('schema_version: 1\nembeddings:\n  model: embed:1\n')
    for name in ('generation', 'pedagogy'):
        (config / f'{name}.yaml').write_text('schema_version: 1\ngeneration:\n  model: gen:1\n  num_ctx: 6144\n  max_output_tokens: 1536\n')

    def fake_ask(*args, **kwargs):
        return ask(*args, **kwargs, embedder_factory=FakeEmbedder, generator_factory=FakeGenerator)

    ws = Workspace(tmp_path, embedder_factory=FakeEmbedder, ask_function=fake_ask)
    app = create_app(tmp_path, workspace=ws)
    with TestClient(app, base_url='http://127.0.0.1:8765') as client:
        html = client.get('/').text
        token = re.search(r'name="docente-token" content="([^"]+)"', html).group(1)
        client.headers['X-Docente-Token'] = token
        yield client, ws


def test_api_endpoint_presentation_html_y_markdown(web_with_run):
    client, ws = web_with_run

    # Insertar una propuesta sintética directamente en base de datos
    run = _make_dummy_polyphony_run()
    run_id = run['id']
    import json
    import sqlite3
    req = dict(run['request'])
    req.update({'subject': 'historia-i', 'category': 'bibliografia', 'document_ids': []})
    with sqlite3.connect(ws.db) as conn:
        conn.execute(
            """INSERT INTO generation_runs (
                id, created_at, status, request_json, prompt_version,
                result_json, evidence_json, display_title, original_topic
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                '2026-09-07T10:00:00',
                'draft',
                json.dumps(req),
                'v1',
                json.dumps(run['result']),
                '[]',
                run['display_title'],
                run['original_topic'],
            ),
        )
        conn.commit()

    # Petición formato HTML (predeterminado para proyección)
    res_html = client.get(f'/api/runs/{run_id}?presentation=1')
    assert res_html.status_code == 200
    assert 'text/html' in res_html.headers['Content-Type']
    assert '<!doctype html>' in res_html.text
    assert 'Polifonía del siglo' in res_html.text
    assert 'inline; filename="presentacion-polifonia-del-siglo-xv.html"' in res_html.headers['Content-Disposition']

    # Petición formato Markdown
    res_md = client.get(f'/api/runs/{run_id}?presentation=1&format=md')
    assert res_md.status_code == 200
    assert 'text/markdown' in res_md.headers['Content-Type']
    assert 'Polifonía del siglo' in res_md.text
    assert '---' in res_md.text
    assert 'attachment; filename="presentacion-polifonia-del-siglo-xv.md"' in res_md.headers['Content-Disposition']
