"""Tests para la vista de Piano Roll vectorial (SVG) generada con music21.

Verifica:
- Generación de SVG a partir de MusicXML y de Humdrum (**kern).
- Representación de una franja de color por voz.
- Eje horizontal en compases y vertical en altura.
- Resaltado distintivo del Tenor (cantus firmus).
- Inclusión del cursor de reproducción sincronizado (playhead).
- Integración con el endpoint seguro /api/scores/render-pianoroll.
"""

from pathlib import Path
import pytest
from starlette.testclient import TestClient

from docente_ai.music import render_pianoroll_svg, get_music21
from docente_ai.web.app import create_app
from docente_ai.web.workspace import Workspace


XML_CORAL_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work>
    <work-title>Chorale Test</work-title>
  </work>
  <part-list>
    <score-part id="P1"><part-name>Soprano</part-name></score-part>
    <score-part id="P2"><part-name>Alto</part-name></score-part>
    <score-part id="P3"><part-name>Tenor</part-name></score-part>
    <score-part id="P4"><part-name>Bass</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note><pitch><step>C</step><octave>5</octave></pitch><duration>2</duration></note>
      <note><pitch><step>B</step><octave>4</octave></pitch><duration>2</duration></note>
    </measure>
  </part>
  <part id="P2">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>4</duration></note>
    </measure>
  </part>
  <part id="P3">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>F</sign><line>4</line></clef>
      </attributes>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>4</duration></note>
    </measure>
  </part>
  <part id="P4">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>F</sign><line>4</line></clef>
      </attributes>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>4</duration></note>
    </measure>
  </part>
</score-partwise>"""

KRN_POLIFONIA_FIXTURE = """!!!OTL: Polifonia Test
!!!COM: Johannes Ockeghem
**kern\t**kern\t**kern\t**kern
*clefG2\t*clefC3\t*clefC4\t*clefF4
*M4/2\t*M4/2\t*M4/2\t*M4/2
=1\t=1\t=1\t=1
2c\t2e\t2g\t2C
2d\t2f\t2a\t2D
=2\t=2\t=2\t=2
1e\t1g\t1b\t1E
*-
"""


def test_pianoroll_svg_desde_musicxml(tmp_path):
    """Comprueba la generación de Piano Roll SVG a partir de un archivo MusicXML."""
    xml_file = tmp_path / "coral.musicxml"
    xml_file.write_text(XML_CORAL_FIXTURE, encoding="utf-8")

    svg = render_pianoroll_svg(xml_file)

    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert 'class="pianoroll-svg"' in svg

    # Eje horizontal: compases
    assert "c.1" in svg
    assert 'class="pianoroll-measure-grid"' in svg

    # Eje vertical: alturas cromáticas
    assert 'class="pianoroll-pitch-grid"' in svg
    assert "C5" in svg or "C4" in svg

    # Franja distintiva por voz en la leyenda
    assert "Soprano" in svg
    assert "Alto" in svg
    assert "Tenor" in svg
    assert "Bass" in svg

    # Tenor resaltado
    assert "is-tenor" in svg
    assert "cantus firmus" in svg
    assert "#f59e0b" in svg  # Color ámbar del Tenor

    # Cursor de reproducción sincronizado (playhead)
    assert 'id="pianoroll-playhead"' in svg
    assert 'class="pianoroll-playhead"' in svg
    assert 'data-total-ql=' in svg


def test_pianoroll_svg_desde_humdrum_krn(tmp_path):
    """Comprueba la generación de Piano Roll SVG a partir de un archivo Humdrum (**kern)."""
    krn_file = tmp_path / "polifonia.krn"
    krn_file.write_text(KRN_POLIFONIA_FIXTURE, encoding="utf-8")

    svg = render_pianoroll_svg(krn_file, highlight_voice="Voz 3")

    assert "<svg" in svg
    assert 'class="pianoroll-svg"' in svg
    assert 'class="pianoroll-notes"' in svg
    assert 'pianoroll-playhead' in svg
    assert "c.1" in svg


def test_pianoroll_recorte_compases():
    """El generador de piano roll debe respetar el recorte de compases [start, end]."""
    m21 = get_music21()
    score = m21.corpus.parse("bach/bwv66.6")

    # Recortar solo compases 1 a 2
    svg_recorte = render_pianoroll_svg(score, start_measure=1, end_measure=2)
    assert "c.1" in svg_recorte
    assert "c.2" in svg_recorte

    # Error si el rango es inválido
    with pytest.raises(ValueError, match="no puede ser menor"):
        render_pianoroll_svg(score, start_measure=5, end_measure=2)


def test_endpoint_scores_render_pianoroll(tmp_path):
    """Comprueba el endpoint seguro /api/scores/render-pianoroll."""
    import re
    from docente_ai.config import load
    from docente_ai.storage import import_config
    from test_generation import EXAMPLE, FakeEmbedder

    db = tmp_path / "data/docente.sqlite3"
    import_config(db, load(EXAMPLE))

    xml_file = tmp_path / "data/ejemplos/ej_coral.musicxml"
    xml_file.parent.mkdir(parents=True, exist_ok=True)
    xml_file.write_text(XML_CORAL_FIXTURE, encoding="utf-8")

    ws = Workspace(tmp_path, embedder_factory=FakeEmbedder)
    app = create_app(tmp_path, workspace=ws)

    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        html = client.get("/").text
        token_m = re.search(r'name="docente-token" content="([^"]+)"', html)
        if token_m:
            client.headers["X-Docente-Token"] = token_m.group(1)

        # 1. Rechazo estricto de rutas directas del cliente
        resp_bad = client.post("/api/scores/render-pianoroll", json={"path": "/etc/passwd"})
        assert resp_bad.status_code == 400
        assert "No se admiten rutas del cliente" in resp_bad.text

        # 2. Rechazo si no se indica identificador
        resp_empty = client.post("/api/scores/render-pianoroll", json={})
        assert resp_empty.status_code == 400

        # 3. Identificador de archivo en corpus de music21
        resp_m21 = client.post(
            "/api/scores/render-pianoroll",
            json={"id": "m21-bwv66-6", "start": 1, "end": 4, "voice": "Tenor"}
        )
        assert resp_m21.status_code == 200
        data = resp_m21.json()
        assert "svg" in data
        assert "<svg" in data["svg"]
        assert "pianoroll-svg" in data["svg"]
        assert "is-tenor" in data["svg"]
        assert "pianoroll-playhead" in data["svg"]
