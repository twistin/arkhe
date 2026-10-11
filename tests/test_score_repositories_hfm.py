"""Tests para el repositorio de partituras 'HfM Weimar – Computergestützte Musikanalyse'.

Verifica:
- Metadatos del repositorio en REPOSITORIOS_METADATOS.
- Filtrado estricto: solo archivos .xml (MusicXML), rechazo absoluto de archivos .sv.
- Atributos obligatorios: URL, fecha, atribución, licencia no especificada, exportable: False.
- Prioridad JRP: detección de archivos coincidentes con JRP y precedencia de JRP.
- Bloqueo de exportación fuera del material de clase (WAV y MusicXML).
"""

from pathlib import Path
import pytest
from starlette.testclient import TestClient

from docente_ai.teaching.score_repositories import (
    REPOSITORIOS_METADATOS,
    buscar_en_hfm_weimar,
    coincide_con_jrp,
    buscar_en_repositorios,
)
from docente_ai.web.app import create_app
from docente_ai.web.workspace import Workspace


HTML_HFM_WEIMAR_FIXTURE = """
<!DOCTYPE html>
<html>
<body>
  <h1>Notendatenbank</h1>
  <table class="table">
    <!-- Fila 1: Obra renacentista procedente de JRP (base de datos 002) -->
    <tr class="row1">
      <td class="col0">Duf1004</td>
      <td class="col5">
        <a href="https://analyse.hfm-weimar.de/database/02/DuGui_Duf1004_COM_1-5_MissaLhomm_002_00956.xml">Missa L'homme arme - Kyrie</a>
      </td>
      <td class="col6">
        <a href="https://analyse.hfm-weimar.de/database/sv/DuGui_Duf1004_COM_1-5_MissaLhomm_002_00956.sv">Download Sonic Visualiser</a>
      </td>
    </tr>
    <!-- Fila 2: Archivo solo con enlace Sonic Visualiser .sv (debe ser ignorado) -->
    <tr class="row2">
      <td class="col0">SVOnly</td>
      <td class="col5">
        <a href="https://analyse.hfm-weimar.de/database/sv/SoloAudio_001.sv">Solo Archivo SV</a>
      </td>
      <td class="col6">
        <a href="https://analyse.hfm-weimar.de/database/sv/SoloAudio_001.sv">Download SV</a>
      </td>
    </tr>
    <!-- Fila 3: Coral de Sethus Calvisius (base de datos 005, no JRP) -->
    <tr class="row3">
      <td class="col0">Cal001</td>
      <td class="col5">
        <a href="https://analyse.hfm-weimar.de/database/05/CalSet_Kantional_005_00123.xml">Sethus Calvisius - Mein Seel erhebt den Herren</a>
      </td>
      <td class="col6">
        <a href="https://analyse.hfm-weimar.de/database/sv/CalSet_Kantional_005_00123.sv">Download SV</a>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def test_metadatos_repositorio_hfm_weimar():
    """Comprueba que HfM Weimar esté registrado con sus metadatos reglamentarios."""
    assert "hfm_weimar" in REPOSITORIOS_METADATOS
    meta = REPOSITORIOS_METADATOS["hfm_weimar"]

    assert meta["nombre"] == "HfM Weimar – Computergestützte Musikanalyse"
    assert meta["url_base"] == "https://analyse.hfm-weimar.de"
    assert meta["formatos"] == ["musicxml"]
    assert meta["licencia"] == "licencia no especificada: uso docente con atribución"
    assert meta["atribucion"] == "HfM Weimar – Computergestützte Musikanalyse"
    assert meta["exportable"] is False
    assert meta["disponible"] is True


def test_hfm_weimar_filtra_solo_xml_y_rechaza_sv(tmp_path):
    """La búsqueda en HfM Weimar debe aceptar únicamente archivos .xml y rechazar .sv."""
    cache_dir = tmp_path / "cache_hfm"
    candidatos = buscar_en_hfm_weimar(
        {"work": ""},
        destino_cache=cache_dir,
        html_fuente=HTML_HFM_WEIMAR_FIXTURE
    )

    assert len(candidatos) == 2
    for cand in candidatos:
        # Formato estrictamente musicxml / .xml
        assert cand["archivo"].endswith(".xml")
        assert not cand["archivo"].endswith(".sv")
        assert cand["formato"] == "musicxml"
        assert not cand["url"].endswith(".sv")

        # Metadatos obligatorios
        assert cand["fuente"] == "HfM Weimar – Computergestützte Musikanalyse"
        assert cand["atribucion"] == "HfM Weimar – Computergestützte Musikanalyse"
        assert cand["licencia"] == "licencia no especificada: uso docente con atribución"
        assert cand["exportable"] is False
        assert "fecha" in cand and len(cand["fecha"]) == 10  # YYYY-MM-DD


def test_deteccion_coincidencia_con_jrp():
    """Detecta si un archivo de HfM Weimar procede del JRP o de su corpus renacentista."""
    # Archivo con ID de base de datos 002 (JRP)
    assert coincide_con_jrp("DuGui_Duf1004_COM_1-5_MissaLhomm_002_00956.xml") is True
    # Opus prefijo de JRP
    assert coincide_con_jrp("Jos2721_AveMaria.xml", composer="Josquin des Prez") is True
    # Compositor renacentista JRP
    assert coincide_con_jrp("Pieza_Polifonica.xml", composer="Johannes Ockeghem") is True

    # Archivo no perteneciente a JRP (ej. Sethus Calvisius, Bach, Beethoven)
    assert coincide_con_jrp("CalSet_Kantional_005_00123.xml", composer="Sethus Calvisius") is False
    assert coincide_con_jrp("Bach_Chorale_BWV66.xml", composer="J.S. Bach") is False


def test_prioridad_jrp_en_busqueda_repositorios(tmp_path):
    """Si una obra del Renacimiento coincide con JRP, se da prioridad al JRP frente a HfM Weimar."""
    # Búsqueda de una obra renacentista presente en la fixture de HfM Weimar pero coincidente con JRP
    req = {"composer": "Guillaume Du Fay", "work": "Missa L'homme arme"}

    # Llamada directa con filtrado de coincidentes JRP
    cands_hfm = buscar_en_hfm_weimar(
        req,
        destino_cache=tmp_path,
        html_fuente=HTML_HFM_WEIMAR_FIXTURE,
        filtrar_coincidentes_jrp=True
    )
    # Al coincidir con JRP (Duf1004 / base de datos 002), se descarta a favor de JRP
    assert len(cands_hfm) == 0

    # En cambio, para una obra no renacentista de HfM Weimar (Calvisius), se devuelve el candidato
    req_cal = {"composer": "Sethus Calvisius", "work": "Mein Seel"}
    cands_cal = buscar_en_hfm_weimar(
        req_cal,
        destino_cache=tmp_path,
        html_fuente=HTML_HFM_WEIMAR_FIXTURE,
        filtrar_coincidentes_jrp=True
    )
    assert len(cands_cal) == 1
    assert cands_cal[0]["archivo"] == "CalSet_Kantional_005_00123.xml"
    assert cands_cal[0]["exportable"] is False


def test_bloqueo_exportacion_partituras_no_exportables(tmp_path):
    """Partituras con 'licencia no especificada' no pueden exportarse fuera del aula (WAV ni MusicXML)."""
    import yaml
    cat_dir = tmp_path / "data/ejemplos"
    cat_dir.mkdir(parents=True, exist_ok=True)

    fake_xml = cat_dir / "obra_restringida.xml"
    fake_xml.write_text("<score-partwise><part id='P1'></part></score-partwise>", encoding="utf-8")

    ejemplo_restringido = [{
        "id": "ej-restringido-01",
        "titulo": "Pieza con licencia no especificada",
        "compositor": "Compositor",
        "archivo": "obra_restringida.xml",
        "archivo_path": str(fake_xml),
        "fuente": "HfM Weimar – Computergestützte Musikanalyse",
        "licencia": "licencia no especificada: uso docente con atribución",
        "exportable": False,
        "verificado": True,
    }]
    (cat_dir / "ejemplos.yaml").write_text(yaml.safe_dump(ejemplo_restringido), encoding="utf-8")

    import re
    from docente_ai.config import load
    from docente_ai.storage import import_config
    from test_generation import EXAMPLE, FakeEmbedder

    db = tmp_path / "data/docente.sqlite3"
    import_config(db, load(EXAMPLE))

    ws = Workspace(tmp_path, embedder_factory=FakeEmbedder)
    app = create_app(tmp_path, workspace=ws)

    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        html = client.get("/").text
        token_m = re.search(r'name="docente-token" content="([^"]+)"', html)
        if token_m:
            client.headers["X-Docente-Token"] = token_m.group(1)

        # 1. Intento de exportar audio WAV
        with pytest.raises(ValueError, match="no puede exportarse fuera del material de clase"):
            ws.export_score_wav("ej-restringido-01")

        # 2. Intento de descargar el archivo MusicXML crudo
        resp = client.get("/api/ejemplos/ej-restringido-01?musicxml=1")
        assert resp.status_code == 400 or resp.status_code == 500
        assert "no puede exportarse fuera del material de clase" in resp.text
