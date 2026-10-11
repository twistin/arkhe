"""Servicio musical determinista: análisis de partituras con music21 (carga perezosa).

Funcionalidades de análisis:
- Ámbito por voz (nota más grave y más aguda, intervalo total).
- Finalis / nota final de cada voz y del conjunto.
- Intervalos melódicos y armónicos más frecuentes.
- Proporción de duraciones entre dos versiones de una melodía (detección de aumentación/disminución).

Todos los datos se etiquetan explícitamente como "calculado a partir de la partitura" y no requieren cita.
"""

from collections import Counter
from typing import Any

from docente_ai.music.lazy import get_music21


def analyze_ambitus(score) -> dict[str, Any]:
    """Calcula el ámbito de cada voz de la partitura (nota más grave, más aguda e intervalo)."""
    m21 = get_music21()
    partes_res = []

    parts = score.parts if hasattr(score, "parts") and len(score.parts) > 0 else [score]
    for idx, part in enumerate(parts):
        part_name = part.partName or f"Voz {idx + 1}"
        notes = list(part.flatten().notes)
        pitches = []
        for n in notes:
            if n.isNote:
                pitches.append(n.pitch)
            elif n.isChord:
                pitches.extend(n.pitches)

        if not pitches:
            partes_res.append({
                "voz": part_name,
                "grave": None,
                "agudo": None,
                "intervalo": "Sin notas",
                "semitonos": 0,
            })
            continue

        pitches.sort()
        lowest = pitches[0]
        highest = pitches[-1]
        interval = m21.interval.Interval(noteStart=lowest, noteEnd=highest)

        partes_res.append({
            "voz": part_name,
            "grave": lowest.nameWithOctave,
            "agudo": highest.nameWithOctave,
            "intervalo": interval.niceName,
            "semitonos": interval.semitones,
        })

    return {
        "voces": partes_res,
        "origen": "calculado a partir de la partitura",
    }


def analyze_final(score) -> dict[str, Any]:
    """Determina la nota final de cada voz y el acorde final."""
    parts = score.parts if hasattr(score, "parts") and len(score.parts) > 0 else [score]
    finales = []
    
    for idx, part in enumerate(parts):
        part_name = part.partName or f"Voz {idx + 1}"
        notes = list(part.flatten().notes)
        if not notes:
            continue
        last_item = notes[-1]
        if last_item.isNote:
            finales.append({"voz": part_name, "final": last_item.pitch.nameWithOctave})
        elif last_item.isChord:
            finales.append({"voz": part_name, "final": [p.nameWithOctave for p in last_item.pitches]})

    # Nota final de la voz más grave (bajo/tenor inferior)
    nota_principal = finales[-1]["final"] if finales else "Desconocida"
    if isinstance(nota_principal, list) and nota_principal:
        nota_principal = nota_principal[0]

    return {
        "final_por_voz": finales,
        "nota_final_principal": nota_principal,
        "origen": "calculado a partir de la partitura",
    }


def analyze_frequent_intervals(score, limit: int = 5) -> dict[str, Any]:
    """Calcula los intervalos melódicos más frecuentes en la partitura."""
    m21 = get_music21()
    counter = Counter()

    parts = score.parts if hasattr(score, "parts") and len(score.parts) > 0 else [score]
    for part in parts:
        notes = [n for n in part.flatten().notes if n.isNote]
        for i in range(len(notes) - 1):
            n1 = notes[i]
            n2 = notes[i + 1]
            try:
                intv = m21.interval.Interval(noteStart=n1, noteEnd=n2)
                counter[intv.directedNiceName] += 1
            except Exception:
                continue

    top = [{"intervalo": name, "conteo": count} for name, count in counter.most_common(limit)]
    return {
        "intervalos_mas_frecuentes": top,
        "origen": "calculado a partir de la partitura",
    }


def analyze_rhythmic_proportions(melody_a, melody_b) -> dict[str, Any]:
    """Compara las duraciones de dos secuencias melódicas para detectar aumentación o disminución.

    Parámetros:
        melody_a: Primera versión de la melodía (music21 Part o Stream).
        melody_b: Segunda versión de la melodía (ej. tenor en aumentación).

    Devuelve:
        Diccionario con la proporción media de duraciones y si hay aumentación detectada.
    """
    notes_a = [n for n in melody_a.flatten().notes if n.isNote]
    notes_b = [n for n in melody_b.flatten().notes if n.isNote]

    if not notes_a or not notes_b:
        return {
            "proporcion": None,
            "es_aumentacion": False,
            "detalle": "Una de las melodías no contiene notas.",
            "origen": "calculado a partir de la partitura",
        }

    # Comparar duraciones proporcionales en las primeras N notas comunes
    min_len = min(len(notes_a), len(notes_b))
    ratios = []
    for i in range(min_len):
        dur_a = float(notes_a[i].duration.quarterLength)
        dur_b = float(notes_b[i].duration.quarterLength)
        if dur_a > 0:
            ratios.append(dur_b / dur_a)

    if not ratios:
        return {
            "proporcion": None,
            "es_aumentacion": False,
            "origen": "calculado a partir de la partitura",
        }

    avg_ratio = sum(ratios) / len(ratios)
    ratio_redondeado = round(avg_ratio, 2)

    es_aumentacion = False
    descripcion = "Sin cambio proporcional exacto"
    if 1.9 <= ratio_redondeado <= 2.1:
        es_aumentacion = True
        descripcion = "Aumentación al doble (proporción 2:1)"
    elif 2.9 <= ratio_redondeado <= 3.1:
        es_aumentacion = True
        descripcion = "Aumentación al triple (proporción 3:1)"
    elif 3.9 <= ratio_redondeado <= 4.1:
        es_aumentacion = True
        descripcion = "Aumentación al cuádruple (proporción 4:1)"
    elif 0.45 <= ratio_redondeado <= 0.55:
        descripcion = "Disminución a la mitad (proporción 1:2)"

    return {
        "proporcion_media": ratio_redondeado,
        "es_aumentacion": es_aumentacion,
        "descripcion": descripcion,
        "notas_comparadas": min_len,
        "origen": "calculado a partir de la partitura",
    }


def analyze_score(score) -> dict[str, Any]:
    """Genera el conjunto completo de análisis deterministas de una partitura."""
    ambitus = analyze_ambitus(score)
    final_info = analyze_final(score)
    intervalos = analyze_frequent_intervals(score)

    return {
        "ambitus": ambitus,
        "final": final_info,
        "intervalos": intervalos,
        "etiqueta": "calculado a partir de la partitura",
    }
