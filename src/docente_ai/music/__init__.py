"""Módulo de servicio musical determinista y utilidades analíticas.

Incluye:
- Detección de bibliotecas opcionales de audio y DSP (ntam: librosa, pedalboard).
- Detección y renderizado con FluidSynth (opcional en el sistema, sin dependencia Python).
- Análisis musical determinista (ámbito, final, intervalos, aumentación).
- Teoría musical de la Grecia Antigua: generador de tetracordos con frecuencias exactas.
- Importación, recorte y transposición de partituras mediante music21 (carga perezosa).
"""

from docente_ai.music.ntam import ntam_available, get_ntam_info
from docente_ai.music.fluidsynth import fluidsynth_available, export_midi_to_wav
from docente_ai.music.greek import generar_tetracordos, note_name_to_freq
from docente_ai.music.lazy import get_music21
from docente_ai.music.score import (
    load_score,
    extract_metadata,
    slice_measures,
    transpose_score,
    export_score_to_musicxml,
)
from docente_ai.music.analysis import (
    analyze_ambitus,
    analyze_final,
    analyze_frequent_intervals,
    analyze_rhythmic_proportions,
    analyze_score,
)
from docente_ai.music.pianoroll import render_pianoroll_svg

__all__ = [
    "ntam_available",
    "get_ntam_info",
    "fluidsynth_available",
    "export_midi_to_wav",
    "generar_tetracordos",
    "note_name_to_freq",
    "get_music21",
    "load_score",
    "extract_metadata",
    "slice_measures",
    "transpose_score",
    "export_score_to_musicxml",
    "render_pianoroll_svg",
    "analyze_ambitus",
    "analyze_final",
    "analyze_frequent_intervals",
    "analyze_rhythmic_proportions",
    "analyze_score",
]
