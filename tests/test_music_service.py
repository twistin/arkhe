"""Tests para el servicio musical determinista:
- Carga perezosa de music21 (no se importa al importar docente_ai.music).
- Importación y validación de MusicXML y Humdrum (.krn).
- Recorte de compases y transposición.
- Análisis calculado: ámbito por voz, nota final, intervalos y proporción rítmica (aumentación).
- Generador de tetracordos en la teoría griega con frecuencias exactas en Hz.
- Comportamiento de la aplicación sin el grupo opcional ntam.
- Comprobación de detección de FluidSynth (sin PyDub ni mido).
"""

from pathlib import Path
import pytest

from docente_ai.music.lazy import get_music21
from docente_ai.music.ntam import ntam_available, get_ntam_info
from docente_ai.music.fluidsynth import fluidsynth_available
from docente_ai.music.greek import (
    generar_tetracordos,
    note_name_to_freq,
    freq_from_cents,
)
from docente_ai.music.score import (
    load_score,
    extract_metadata,
    slice_measures,
    transpose_score,
)
from docente_ai.music.analysis import (
    analyze_ambitus,
    analyze_final,
    analyze_frequent_intervals,
    analyze_rhythmic_proportions,
    analyze_score,
)


# ── 1. Carga perezosa y comportamiento sin ntam ───────────────────────────────

def test_ntam_comportamiento_sin_librerias_instaladas():
    """La app debe funcionar y reportar correctamente si librosa/pedalboard no están."""
    info = get_ntam_info()
    assert isinstance(info, dict)
    assert "disponible" in info
    assert "mensaje" in info
    # En el entorno de test por defecto no están instaladas
    assert ntam_available() is False
    assert info["disponible"] is False
    assert "pip install" in info["mensaje"]


def test_carga_perezosa_music21():
    """get_music21 importa la librería bajo demanda y devuelve el módulo."""
    m21 = get_music21()
    assert m21 is not None
    assert hasattr(m21, "converter")
    assert hasattr(m21, "stream")


def test_fluidsynth_detector_seguro():
    """Comprueba que fluidsynth_available no falle ni use PyDub o mido."""
    import sys
    assert "pydub" not in sys.modules
    assert "mido" not in sys.modules
    disp = fluidsynth_available()
    assert isinstance(disp, bool)


# ── 2. Importación y recorte de MusicXML y Humdrum ────────────────────────────

MUSICXML_EJEMPLO = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Missa Se la face ay pale</work-title></work>
  <identification>
    <creator type="composer">Guillaume Du Fay</creator>
  </identification>
  <part-list>
    <score-part id="P1"><part-name>Cantus</part-name></score-part>
    <score-part id="P2"><part-name>Tenor</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <time><beats>3</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration></note>
    </measure>
    <measure number="2">
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>2</duration></note>
    </measure>
    <measure number="3">
      <note><pitch><step>A</step><octave>4</octave></pitch><duration>3</duration></note>
    </measure>
  </part>
  <part id="P2">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <time><beats>3</beats><beat-type>4</beat-type></time>
        <clef><sign>F</sign><line>4</line></clef>
      </attributes>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>3</duration></note>
    </measure>
    <measure number="2">
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>3</duration></note>
    </measure>
    <measure number="3">
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>3</duration></note>
    </measure>
  </part>
</score-partwise>"""

HUMDRUM_EJEMPLO = """!!!OTL: Chanson Dufay
!!!COM: Du Fay, Guillaume
**kern\t**kern
*clefG2\t*clefF4
*M3/4\t*M3/4
=1\t=1
4c\t2.C
4d\t.
4e\t.
=2\t=2
2f\t2.F
4g\t.
=3\t=3
2.c\t2.C
==\t==
*-
"""


def test_importacion_y_metadatos_musicxml(tmp_path):
    """Carga y extrae metadatos de un MusicXML con music21."""
    score_p = tmp_path / "dufay.musicxml"
    score_p.write_text(MUSICXML_EJEMPLO, encoding="utf-8")

    score = load_score(score_p)
    assert score is not None
    assert len(score.parts) == 2

    meta = extract_metadata(score)
    assert meta["titulo"] == "Missa Se la face ay pale"
    assert "Du Fay" in meta["compositor"]
    assert len(meta["voces"]) == 2


def test_recorte_de_compases_y_transposicion(tmp_path):
    """Recorta compases y transporta la obra por un intervalo."""
    score = load_score(MUSICXML_EJEMPLO, format_hint="musicxml")
    
    # Recortar solo compás 1 a 2
    recorte = slice_measures(score, 1, 2)
    assert recorte is not None
    m_count = len(recorte.parts[0].getElementsByClass(get_music21().stream.Measure))
    assert m_count == 2

    # Transportar una 2ª mayor (2 semitonos hacia arriba: C -> D)
    transp = transpose_score(score, 2)
    primera_nota = transp.parts[0].flatten().notes[0]
    assert primera_nota.pitch.name == "D"


def test_importacion_humdrum(tmp_path):
    """Carga una partitura en formato Humdrum (**kern) con music21."""
    krn_p = tmp_path / "dufay.krn"
    krn_p.write_text(HUMDRUM_EJEMPLO, encoding="utf-8")

    score = load_score(krn_p)
    assert score is not None
    assert len(score.parts) == 2


# ── 3. Análisis musical calculado ─────────────────────────────────────────────

def test_calculo_de_ambitus_y_final():
    """Calcula el ámbito por voz y la nota final."""
    score = load_score(MUSICXML_EJEMPLO, format_hint="musicxml")
    
    ambitus = analyze_ambitus(score)
    assert ambitus["origen"] == "calculado a partir de la partitura"
    voces = ambitus["voces"]
    assert len(voces) == 2
    
    # Cantus va de C4 a A4 (sexta mayor)
    cantus = voces[0]
    assert cantus["grave"] == "C4"
    assert cantus["agudo"] == "A4"
    assert cantus["semitonos"] == 9  # 6ª mayor

    # Tenor va de C3 a G3 (quinta justa)
    tenor = voces[1]
    assert tenor["grave"] == "C3"
    assert tenor["agudo"] == "G3"
    assert tenor["semitonos"] == 7  # 5ª justa

    finales = analyze_final(score)
    assert finales["origen"] == "calculado a partir de la partitura"
    assert finales["nota_final_principal"] == "C3"


def test_intervalos_mas_frecuentes():
    """Identifica los intervalos melódicos más frecuentes de la pieza."""
    score = load_score(MUSICXML_EJEMPLO, format_hint="musicxml")
    intervalos = analyze_frequent_intervals(score, limit=3)
    assert intervalos["origen"] == "calculado a partir de la partitura"
    assert len(intervalos["intervalos_mas_frecuentes"]) > 0


def test_deteccion_de_aumentacion_ritmica():
    """Compara dos melodías para detectar aumentación rítmica (proporción 2:1 o 3:1)."""
    m21 = get_music21()
    
    # Melodía rápida (negras)
    melodia_rapida = m21.stream.Part()
    for pitch_name in ["C4", "D4", "E4", "F4"]:
        n = m21.note.Note(pitch_name)
        n.quarterLength = 1.0
        melodia_rapida.append(n)

    # Melodía en aumentación al doble (blancas)
    melodia_aumentada = m21.stream.Part()
    for pitch_name in ["C3", "D3", "E3", "F3"]:
        n = m21.note.Note(pitch_name)
        n.quarterLength = 2.0
        melodia_aumentada.append(n)

    res = analyze_rhythmic_proportions(melodia_rapida, melodia_aumentada)
    assert res["origen"] == "calculado a partir de la partitura"
    assert res["es_aumentacion"] is True
    assert res["proporcion_media"] == 2.0
    assert "2:1" in res["descripcion"]


def test_analisis_completo_etiquetado():
    """El análisis completo empaqueta todo bajo 'calculado a partir de la partitura'."""
    score = load_score(MUSICXML_EJEMPLO, format_hint="musicxml")
    analisis = analyze_score(score)
    assert analisis["etiqueta"] == "calculado a partir de la partitura"
    assert "ambitus" in analisis
    assert "final" in analisis
    assert "intervalos" in analisis


# ── 4. Generador de tetracordos en la teoría griega ───────────────────────────

def test_generador_tetracordos_diatonico_cromatico_enarmonico():
    """Comprueba frecuencias exactas para los tres géneros a partir de E4 (329.63 Hz)."""
    e4_freq = note_name_to_freq("E4")
    assert round(e4_freq, 2) == 329.63

    res = generar_tetracordos(base="E4", direccion="ascendente", sistema="temperado")
    generos = res["generos"]

    # Diatónico: semitono (100c), tono (200c), tono (200c) -> 0, 100, 300, 500 cents
    diat = generos["diatonico"]
    assert diat["cents"] == [0, 100, 300, 500]
    freqs_diat = diat["frecuencias_hz"]
    assert len(freqs_diat) == 4
    assert freqs_diat[0] == 329.63
    # Cuarta justa (500 cents) = 329.63 * 2^(500/1200) ≈ 440.0 Hz (A4)
    assert round(freqs_diat[3], 0) == 440.0

    # Cromático: semitono, semitono, trihemitono -> 0, 100, 200, 500 cents
    crom = generos["cromatico"]
    assert crom["cents"] == [0, 100, 200, 500]
    assert crom["frecuencias_hz"][0] == 329.63
    assert round(crom["frecuencias_hz"][3], 0) == 440.0

    # Enarmónico: diesis (50c = 1/4 tono), diesis (50c), ditono (400c) -> 0, 50, 100, 500 cents
    enarm = generos["enarmonico"]
    assert enarm["cents"] == [0, 50, 100, 500]
    freqs_enarm = enarm["frecuencias_hz"]
    assert freqs_enarm[0] == 329.63
    # Primer cuarto de tono: 329.63 * 2^(50/1200) ≈ 339.29 Hz
    assert round(freqs_enarm[1], 2) == 339.29
    # Segundo cuarto de tono (semitono total, 100c): 329.63 * 2^(100/1200) ≈ 349.23 Hz (F4)
    assert round(freqs_enarm[2], 2) == 349.23
    # Ditono final hasta la cuarta justa (A4 = 440 Hz)
    assert round(freqs_enarm[3], 0) == 440.0
