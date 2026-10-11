"""Manipulación de partituras con music21: importación, recorte y transposición.

Soporta: MusicXML, MXL, MEI, Humdrum (**kern) y ABC.
Todas las operaciones usan carga perezosa de music21.
"""

from pathlib import Path
from typing import Any

from docente_ai.music.lazy import get_music21
from docente_ai.teaching.score_parser import parse_score_file, parse_musicxml_content


def load_score(data_or_path: str | Path, format_hint: str | None = None):
    """Carga una partitura en un objeto music21.stream.Score.

    Parámetros:
        data_or_path: Ruta a un archivo o cadena con el contenido en notación musical.
        format_hint: Formato opcional ('musicxml', 'mxl', 'humdrum', 'mei', 'abc').
    """
    m21 = get_music21()
    
    if isinstance(data_or_path, Path) or (isinstance(data_or_path, str) and "\n" not in data_or_path and Path(data_or_path).is_file()):
        p = Path(data_or_path)
        return m21.converter.parse(str(p), format=format_hint)

    # Contenido en memoria
    return m21.converter.parse(data_or_path, format=format_hint)


def extract_metadata(score_or_path: Any) -> dict[str, Any]:
    """Extrae metadatos musicales (título, compositor, voces, claves, compases, mensuración).

    Si se pasa una ruta de archivo, utiliza el parser rápido sin cargar music21 si es posible.
    Si se pasa un objeto Score de music21, extrae sus propiedades directamente.
    """
    if isinstance(score_or_path, (str, Path)) and Path(str(score_or_path)).is_file():
        return parse_score_file(Path(str(score_or_path)))

    # Extraer desde objeto music21 Score
    score = score_or_path
    title = score.metadata.title if score.metadata and score.metadata.title else "Sin título"
    composer = score.metadata.composer if score.metadata and score.metadata.composer else "Anónimo"

    voces = []
    claves = []
    mensuracion = "No especificada"
    
    parts = score.parts if hasattr(score, "parts") and len(score.parts) > 0 else [score]
    for idx, part in enumerate(parts):
        v_name = part.partName or f"Voz {idx + 1}"
        voces.append({"id": f"P{idx + 1}", "nombre": v_name})
        
        # Claves en la primera medida
        for c in part.flatten().getElementsByClass("Clef"):
            c_desc = f"{c.sign}{c.line}" if hasattr(c, "sign") and hasattr(c, "line") else str(c)
            if c_desc not in claves:
                claves.append(c_desc)

        # Mensuración
        if mensuracion == "No especificada":
            ts = part.flatten().getElementsByClass("TimeSignature")
            if ts:
                mensuracion = f"{ts[0].numerator}/{ts[0].denominator}"

    # Compases aproximados
    measures = score.parts[0].getElementsByClass("Measure") if score.parts else score.getElementsByClass("Measure")
    compases_count = len(measures)

    return {
        "titulo": title,
        "compositor": composer,
        "voces": voces,
        "compases": compases_count,
        "claves": claves,
        "mensuracion": mensuracion,
    }


def slice_measures(score, start_measure: int, end_measure: int):
    """Recorta un rango de compases inclusivo [start_measure, end_measure].

    Parámetros:
        score: music21.stream.Score.
        start_measure: Número del primer compás (1-indexado).
        end_measure: Número del último compás.

    Devuelve:
        Nuevo objeto Score recortado.
    """
    if start_measure < 1:
        raise ValueError(f"El compás inicial debe ser mayor o igual a 1 (recibido: {start_measure}).")
    if end_measure < start_measure:
        raise ValueError(f"El compás final ({end_measure}) no puede ser menor que el inicial ({start_measure}).")

    try:
        sliced = score.measures(start_measure, end_measure)
    except Exception as exc:
        raise ValueError(f"Error al recortar compases {start_measure}–{end_measure}: {exc}") from exc

    measures_count = 0
    if hasattr(sliced, "parts") and len(sliced.parts) > 0:
        measures_count = len(sliced.parts[0].getElementsByClass("Measure"))
    elif hasattr(sliced, "getElementsByClass"):
        measures_count = len(sliced.getElementsByClass("Measure"))

    if measures_count == 0:
        raise ValueError(
            f"El rango solicitado ({start_measure}–{end_measure}) no contiene compases en la partitura "
            "o excede su extensión."
        )

    return sliced


def transpose_score(score, semitones_or_interval: int | str):
    """Transporta una partitura por un intervalo o número de semitonos.

    Parámetros:
        score: music21.stream.Score.
        semitones_or_interval: Número entero de semitonos (ej. 2, -3) o intervalo (ej. 'M2', 'P5').

    Devuelve:
        Nuevo objeto Score transportado.
    """
    m21 = get_music21()
    if isinstance(semitones_or_interval, int):
        intv = m21.interval.Interval(semitones_or_interval)
    else:
        intv = m21.interval.Interval(semitones_or_interval)
    return score.transpose(intv)


def export_score_to_musicxml(score, output_path: Path | str) -> Path:
    """Exporta el Score a formato MusicXML en disco."""
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(out_p))
    return out_p
