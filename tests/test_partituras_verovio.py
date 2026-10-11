"""Tests para la resolución de partituras con Verovio, extracción de metadatos,
rechazo de notación inventada por LLM y control de verificación para el alumnado.
"""

from pathlib import Path
import pytest

from docente_ai.generation.validation import (
    check_no_musical_notation,
    MUSICAL_NOTATION_REGEX,
)
from docente_ai.teaching.score_parser import parse_score_file
from docente_ai.teaching.score_repositories import (
    buscar_en_repositorios,
    REPOSITORIOS_METADATOS,
)
from docente_ai.teaching.score_resolver import (
    resolver_peticion_musical,
    resolver_todas_las_peticiones,
    usar_candidato_como_ejemplo,
)
from docente_ai.generation.render import render_pedagogy, render_student


# ── 1. Contrato del modelo: Prohibición de notación musical inventada ─────────

def test_validador_rechaza_notacion_musical_inventada():
    """El validador debe rechazar cualquier bloque de notación en texto del LLM."""
    # MusicXML inventado
    bad_musicxml = "Aquí está la partitura: <score-partwise version='3.1'><part id='P1'></part></score-partwise>"
    with pytest.raises(ValueError, match="notación musical"):
        check_no_musical_notation(bad_musicxml)

    # LilyPond inventado
    bad_lilypond = "Ejemplo en LilyPond:\n\\relative c' { c4 d e f | g1 }"
    with pytest.raises(ValueError, match="notación musical"):
        check_no_musical_notation(bad_lilypond)

    # ABC inventado
    bad_abc = "Toca esta melodía:\nX: 1\nT: Test\nK: C\n|: C D E F | G A B c :|"
    with pytest.raises(ValueError, match="notación musical"):
        check_no_musical_notation(bad_abc)

    # Humdrum inventado
    bad_humdrum = "**kern\t**kern\n*clefG2\t*clefF4\n4c\t4C\n*-"
    with pytest.raises(ValueError, match="notación musical"):
        check_no_musical_notation(bad_humdrum)

    # Texto pedagógico legítimo sin notación no debe fallar
    legit_text = (
        "Analizar el inicio del Gloria de la Missa Se la face ay pale de Guillaume Du Fay, "
        "observando la aumentación del Tenor en relación con las voces superiores."
    )
    check_no_musical_notation(legit_text)


# ── 2. Extracción de metadatos desde archivos locales ────────────────────────

def test_extraccion_metadatos_musicxml(tmp_path):
    """Comprueba que parse_score_file extraiga metadatos de un archivo MusicXML."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work>
    <work-title>Missa L'homme armé</work-title>
  </work>
  <identification>
    <creator type="composer">Johannes Ockeghem</creator>
  </identification>
  <part-list>
    <score-part id="P1"><part-name>Superius</part-name></score-part>
    <score-part id="P2"><part-name>Contratenor</part-name></score-part>
    <score-part id="P3"><part-name>Tenor</part-name></score-part>
    <score-part id="P4"><part-name>Bassus</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <time><beats>3</beats><beat-type>2</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration></note>
    </measure>
    <measure number="2">
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration></note>
    </measure>
  </part>
</score-partwise>"""
    score_file = tmp_path / "ockeghem_lhomme_arme.musicxml"
    score_file.write_text(xml_content, encoding="utf-8")

    meta = parse_score_file(score_file)
    assert meta["titulo"] == "Missa L'homme armé"
    assert meta["compositor"] == "Johannes Ockeghem"
    assert len(meta["voces"]) == 4
    assert meta["voces"][2]["nombre"] == "Tenor"
    assert meta["compases"] == 2
    assert meta["mensuracion"] == "3/2"
    assert "G2" in meta["claves"]
    assert meta["formato"] == "musicxml"


def test_extraccion_metadatos_humdrum_krn(tmp_path):
    """Comprueba que parse_score_file extraiga metadatos de un archivo Humdrum (.krn)."""
    krn_content = """!!!OTL: Ave Maria ... Virgo serena
!!!COM: Desprez, Josquin
**kern\t**kern\t**kern\t**kern
*clefG2\t*clefC3\t*clefC4\t*clefF4
*M4/2\t*M4/2\t*M4/2\t*M4/2
=1\t=1\t=1\t=1
2c\t2r\t2r\t2r
=2\t=2\t=2\t=2
2e\t2r\t2r\t2r
=3\t=3\t=3\t=3
2g\t2c\t2r\t2r
*-
"""
    krn_file = tmp_path / "josquin_ave_maria.krn"
    krn_file.write_text(krn_content, encoding="utf-8")

    meta = parse_score_file(krn_file)
    assert meta["titulo"] == "Ave Maria ... Virgo serena"
    assert "Josquin" in meta["compositor"]
    assert len(meta["voces"]) == 4
    assert meta["compases"] == 3
    assert meta["mensuracion"] == "4/2"
    assert "G2" in meta["claves"]
    assert meta["formato"] == "humdrum"


# ── 3. Resolución en cascada: Catálogo -> Local -> Repositorios ──────────────

def test_resolucion_desde_catalogo_local(tmp_path):
    """Una petición con obra en el catálogo local se resuelve inmediatamente."""
    import yaml
    cat_dir = tmp_path / "ejemplos"
    cat_dir.mkdir()
    catalogo = [{
        "id": "ej-dufay-cf",
        "titulo": "Missa Se la face ay pale",
        "compositor": "Guillaume Du Fay",
        "obra": "Missa Se la face ay pale",
        "seccion": "Gloria",
        "compases": "1-8",
        "tecnica": "cantus_firmus",
        "archivo": "dufay.musicxml",
        "verificado": True,
        "fuente": "CPDL",
        "licencia": "Dominio público"
    }]
    (cat_dir / "ejemplos.yaml").write_text(yaml.safe_dump(catalogo), encoding="utf-8")

    req = {
        "id": "MR1",
        "work": "Missa Se la face ay pale",
        "composer": "Guillaume Du Fay",
        "section": "Gloria",
        "technique": "cantus_firmus",
        "activity_title": "Análisis formal"
    }

    resultado = resolver_peticion_musical(req, directorio_ejemplos=cat_dir)
    assert resultado["status"] == "resuelto_catalogo"
    assert resultado["verificado"] is True
    assert resultado["ejemplo"]["id"] == "ej-dufay-cf"


def test_resolucion_desde_carpeta_profesor(tmp_path):
    """Si no está en el catálogo, busca en la carpeta de partituras del profesor."""
    cat_dir = tmp_path / "ejemplos"
    cat_dir.mkdir()
    prof_dir = tmp_path / "partituras_prof"
    prof_dir.mkdir()

    # Partitura en carpeta del profesor
    krn_content = """!!!OTL: De plus en plus
!!!COM: Gilles Binchois
**kern\t**kern\t**kern
*clefG2\t*clefC3\t*clefF4
=1\t=1\t=1
2c\t2e\t2g
*-
"""
    (prof_dir / "binchois.krn").write_text(krn_content, encoding="utf-8")

    req = {
        "id": "MR2",
        "work": "De plus en plus",
        "composer": "Binchois",
        "technique": "chanson",
    }

    resultado = resolver_peticion_musical(
        req,
        directorio_ejemplos=cat_dir,
        directorio_partituras=prof_dir,
        con_repositorios_abiertos=False
    )
    assert resultado["status"] == "candidatos_pendientes"
    assert resultado["origen"] == "partituras_profesor"
    assert len(resultado["candidatos"]) == 1
    cand = resultado["candidatos"][0]
    assert cand["titulo"] == "De plus en plus"
    assert cand["verificado"] is False


def test_busqueda_repositorios_abiertos_simulada():
    """El proveedor simulado solo se admite mediante inyección explícita en tests."""
    req = {
        "id": "MR3",
        "work": "Missa L'homme armé",
        "composer": "Johannes Ockeghem",
        "technique": "cantus_firmus",
    }

    def proveedor_fixture(q):
        return [{
            "id": "cand-fixture-01",
            "titulo": f"Ejemplo de {q.get('work')}",
            "compositor": q.get("composer"),
            "fuente": "Josquin Research Project",
            "licencia": "CC BY-NC 4.0",
            "verificado": False,
        }]

    candidatos = buscar_en_repositorios(req, proveedor_test=proveedor_fixture)
    assert len(candidatos) == 1
    cand = candidatos[0]
    assert cand["compositor"] == "Johannes Ockeghem"
    assert cand["verificado"] is False
    assert cand["licencia"] == "CC BY-NC 4.0"
    assert cand["fuente"] == "Josquin Research Project"


def test_busqueda_corpus_music21_real():
    """Busca en el corpus local de music21 sin red y devuelve archivos reales existentes."""
    req = {
        "id": "MR-BACH",
        "work": "bwv10.7",
        "composer": "Bach",
    }
    candidatos = buscar_en_repositorios(req)
    assert len(candidatos) >= 1
    cand = candidatos[0]
    assert "bwv10.7" in cand["archivo"] or "bach" in cand["path"].lower()
    assert cand["fuente"] == "Corpus de music21"
    # Comprobar que la ruta existe físicamente en el disco
    assert Path(cand["path"]).is_file()
    assert len(cand["voces"]) >= 1
    assert cand["verificado"] is False


def test_produccion_no_devuelve_candidatos_simulados():
    """El código de producción nunca inventa candidatos y marca repositorios no implementados."""
    # Repositorios no implementados tienen disponible=False y mensaje claro
    assert REPOSITORIOS_METADATOS["kernscores"]["disponible"] is False
    assert REPOSITORIOS_METADATOS["kernscores"]["mensaje"] == "Repositorio no disponible todavía"
    assert REPOSITORIOS_METADATOS["cpdl"]["disponible"] is False
    assert REPOSITORIOS_METADATOS["cpdl"]["mensaje"] == "Repositorio no disponible todavía"

    # Si una obra no existe en local ni en JRP, devuelve lista vacía, jamás candidatos simulados
    cands = buscar_en_repositorios({"composer": "CompositorInexistente123", "work": "ObraFicticia999"})
    assert cands == []


# ── 4. Adopción, descarte y persistencia como verificado ──────────────────────

def test_adopcion_y_descarte_de_candidatos(tmp_path):
    """Al pulsar 'Usar', el candidato se guarda en data/ejemplos/ con verificado: true."""
    cat_dir = tmp_path / "ejemplos"
    cat_dir.mkdir()

    candidato = {
        "id": "cand-jrp-01",
        "titulo": "Kyrie de la Missa L'homme armé",
        "compositor": "Johannes Ockeghem",
        "fuente": "Josquin Research Project",
        "licencia": "CC BY-NC 4.0",
        "voces": [
            {"id": "V1", "nombre": "Superius"},
            {"id": "V2", "nombre": "Altus"},
            {"id": "V3", "nombre": "Tenor"},
            {"id": "V4", "nombre": "Bassus"},
        ]
    }
    req = {
        "id": "MR1",
        "work": "Missa L'homme armé",
        "composer": "Johannes Ockeghem",
        "section": "Kyrie",
        "technique": "cantus_firmus",
        "voice": "Tenor",
        "description": "Cantus firmus en el tenor en valores largos"
    }

    nuevo_ej = usar_candidato_como_ejemplo(
        req,
        candidato,
        rango_compases="1-12",
        voz_resaltar="Tenor",
        directorio_destino=cat_dir
    )

    assert nuevo_ej["verificado"] is True
    assert nuevo_ej["compases"] == "1-12"
    assert nuevo_ej["voz_resaltada"] == "Tenor"
    assert (cat_dir / "ejemplos.yaml").is_file()

    # Comprobar que ahora la resolución desde ese catálogo lo encuentra verificado
    res = resolver_peticion_musical(req, directorio_ejemplos=cat_dir)
    assert res["status"] == "resuelto_catalogo"
    assert res["verificado"] is True


# ── 5. Material del alumnado: Exclusión estricta de no verificados ────────────

def test_exclusion_ejemplos_no_verificados_en_material_alumnado():
    """El material del alumnado nunca debe contener pentagramas ni ejemplos sin verificar."""
    mock_run = {
        "id": "run-test-score",
        "status": "draft",
        "request": {
            "question": "polifonía del siglo xv",
            "display_title": "Polifonía del siglo XV",
            "pedagogy": {
                "duration_minutes": 60,
                "group": {"name": "Historia de la Música", "level": "1º Bachillerato"},
            }
        },
        "result": {
            "status": "answered",
            "plan": {
                "objectives": ["Comprender la misa de cantus firmus"],
                "difficulty": "Medio",
                "activities": [{
                    "title": "Audición y análisis de la misa",
                    "minutes": 60,
                    "student_task": "Escuchar y seguir la textura.",
                    "deliverable": "Cuestionario de aula."
                }],
                "resources": ["Partitura de estudio"],
            },
            "claims": [{
                "text": "El cantus firmus actúa como eje de la misa cíclica.",
                "student_summary": "Eje estructural de la misa.",
                "evidence": []
            }],
            "music_requests": [{
                "id": "MR1",
                "work": "Missa L'homme armé",
                "composer": "Johannes Ockeghem",
                "technique": "cantus_firmus",
                "activity_title": "Audición y análisis de la misa",
            }],
            "resolved_music_requests": [{
                "request_id": "MR1",
                "status": "candidatos_pendientes",
                "verificado": False,
                "ejemplo": None,
                "candidatos": [{"id": "c1", "titulo": "Candidato no verificado"}]
            }]
        }
    }

    # Guía docente: debe advertir que está pendiente
    docente_md = render_pedagogy(mock_run)
    assert "Pendiente de revisión" in docente_md or "ejemplo pendiente" in docente_md

    # Material del alumnado: no debe mostrar ningún pentagrama, notación ni candidatos crudos
    student_md = render_student(mock_run)
    assert "score-partwise" not in student_md
    assert "\\relative" not in student_md
    assert "**kern" not in student_md
    assert "Candidato no verificado" not in student_md
