"""Generación de Piano Roll en formato SVG para partituras polifónicas.

Genera una representación visual de piano roll a partir de cualquier archivo de partitura
soportado por music21 (MusicXML, Humdrum **kern, MEI, ABC), sin dependencias externas:
- Eje horizontal: compases y pulsos con líneas de división y numeración.
- Eje vertical: altura cromática (notas MIDI) con carriles diferenciados.
- Franja de color distintiva por voz.
- Resaltado visual del Tenor / cantus firmus con mayor opacidad y contorno dorado.
- Cursor vertical (playhead) preparado para sincronización con la reproducción de audio.
"""

from pathlib import Path
from typing import Any
import html

from docente_ai.music.lazy import get_music21
from docente_ai.music.score import slice_measures

# Paleta armónica para voces polifónicas
PALETA_VOCES = [
    {"nombre": "Superius / Soprano", "color": "#3b82f6", "borde": "#1d4ed8"},   # Azul
    {"nombre": "Altus / Contratenor", "color": "#10b981", "borde": "#047857"},  # Esmeralda
    {"nombre": "Tenor (cantus firmus)", "color": "#f59e0b", "borde": "#b45309"},# Ámbar / Oro
    {"nombre": "Bassus / Bajo", "color": "#8b5cf6", "borde": "#6d28d9"},        # Púrpura
    {"nombre": "Quintus", "color": "#ec4899", "borde": "#be185d"},              # Rosa
    {"nombre": "Sextus", "color": "#06b6d4", "borde": "#0e7490"},               # Cian
]

# Nombres de notas para el eje de alturas
NOMBRES_NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_a_nombre_nota(midi_num: int) -> str:
    """Convierte un número MIDI en notación científica (ej. 60 -> C4)."""
    octava = (midi_num // 12) - 1
    nombre = NOMBRES_NOTAS[midi_num % 12]
    return f"{nombre}{octava}"


def extraer_datos_notas(score) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, list[dict[str, Any]]]:
    """Extrae notas, partes, compases y duración total en quarterLength de un Score de music21.

    Devuelve:
        (notas, partes_info, duracion_total, compases_info)
    """
    m21 = get_music21()
    parts = list(score.parts) if hasattr(score, "parts") and len(score.parts) > 0 else [score]

    partes_info = []
    todas_notas = []
    compases_info = []

    # Determinar si alguna voz es explícitamente Tenor
    num_parts = len(parts)
    for idx, p in enumerate(parts):
        nombre_voz = str(p.partName or getattr(p, "id", None) or f"Voz {idx + 1}")
        es_tenor = (
            "tenor" in nombre_voz.lower()
            or (num_parts == 4 and idx == 2)  # En polifonía clásica a 4 voces, la 3ª suele ser el Tenor
        )
        paleta = PALETA_VOCES[idx % len(PALETA_VOCES)]
        partes_info.append({
            "idx": idx,
            "nombre": nombre_voz,
            "es_tenor": es_tenor,
            "color": paleta["color"] if not es_tenor else "#f59e0b",
            "borde": paleta["borde"] if not es_tenor else "#b45309",
        })

    # Extraer información de compases a partir de la primera parte
    primera_parte = parts[0]
    measures = list(primera_parte.getElementsByClass(m21.stream.Measure))
    if not measures and hasattr(score, "getElementsByClass"):
        measures = list(score.getElementsByClass(m21.stream.Measure))

    for m in measures:
        compases_info.append({
            "numero": m.number,
            "offset": float(m.offset),
            "duracion": float(m.quarterLength),
        })

    duracion_total = float(score.highestTime) if score.highestTime else 16.0
    if duracion_total <= 0:
        duracion_total = 16.0

    # Extraer notas de cada parte
    for idx, p in enumerate(parts):
        p_info = partes_info[idx]
        flat_notes = list(p.flatten().notes)
        for n in flat_notes:
            offset = float(n.offset)
            ql = float(n.quarterLength)
            if ql <= 0:
                continue

            if n.isChord:
                for pitch in n.pitches:
                    todas_notas.append({
                        "part_idx": idx,
                        "part_nombre": p_info["nombre"],
                        "es_tenor": p_info["es_tenor"],
                        "midi": pitch.midi,
                        "nombre_nota": pitch.nameWithOctave,
                        "offset": offset,
                        "duracion": ql,
                    })
            else:
                todas_notas.append({
                    "part_idx": idx,
                    "part_nombre": p_info["nombre"],
                    "es_tenor": p_info["es_tenor"],
                    "midi": n.pitch.midi,
                    "nombre_nota": n.pitch.nameWithOctave,
                    "offset": offset,
                    "duracion": ql,
                })

    return todas_notas, partes_info, duracion_total, compases_info


def render_pianoroll_svg(
    score_or_path: Any,
    start_measure: int | None = None,
    end_measure: int | None = None,
    highlight_voice: str | None = None,
    width: int = 960,
    height: int = 380,
) -> str:
    """Genera una vista de piano roll vectorial (SVG) para una partitura.

    Parámetros:
        score_or_path: Objeto music21.stream.Score o ruta (str/Path) al archivo.
        start_measure: Compás de inicio opcional (1-indexado).
        end_measure: Compás final opcional.
        highlight_voice: Nombre o identificador de la voz a resaltar (o 'tenor').
        width: Ancho en píxeles del SVG.
        height: Alto en píxeles del SVG.

    Devuelve:
        Cadena con el SVG completo estructurado y responsive.
    """
    m21 = get_music21()

    if isinstance(score_or_path, (str, Path)):
        p = Path(score_or_path)
        if not p.is_file():
            raise FileNotFoundError(f"Partitura no encontrada: {score_or_path}")
        score = m21.converter.parse(str(p))
    else:
        score = score_or_path

    # Aplicar recorte de compases si se especifica
    if start_measure is not None and end_measure is not None:
        score = slice_measures(score, start_measure, end_measure)

    notas, partes_info, duracion_total, compases_info = extraer_datos_notas(score)

    if not notas:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 120" class="pianoroll-svg">'
            f'<rect width="100%" height="100%" fill="#0f172a" rx="8"/>'
            f'<text x="50%" y="60" text-anchor="middle" fill="#94a3b8" font-size="14">'
            f'No se detectaron notas analizables en el rango de compases indicado.</text></svg>'
        )

    # Si se especificó highlight_voice, ajustar qué voz se resalta
    if highlight_voice:
        hl_lower = highlight_voice.lower()
        for p in partes_info:
            p["es_tenor"] = hl_lower in p["nombre"].lower() or (hl_lower == "tenor" and p["es_tenor"])

    # Rango de alturas (pitch range)
    midis = [n["midi"] for n in notas]
    min_midi = max(36, min(midis) - 2)
    max_midi = min(84, max(midis) + 2)
    total_semitonos = max(12, max_midi - min_midi + 1)

    # Geometría del lienzo
    margin_left = 64
    margin_right = 24
    margin_top = 44
    margin_bottom = 36

    plot_width = max(200, width - margin_left - margin_right)
    plot_height = max(150, height - margin_top - margin_bottom)
    lane_height = plot_height / total_semitonos

    # Generar fragmentos SVG
    svg_elements = []

    # Fondo general
    svg_elements.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0f172a" rx="10" />'
    )

    # Cabecera con leyenda de voces
    legend_x = margin_left
    legend_y = 26
    svg_elements.append('<g class="pianoroll-legend" font-family="system-ui, sans-serif" font-size="11">')
    for p in partes_info:
        badge_fill = "#f59e0b" if p["es_tenor"] else p["color"]
        badge_border = "#fbbf24" if p["es_tenor"] else p["borde"]
        tenor_tag = " ★ cantus firmus" if p["es_tenor"] else ""
        nombre_safe = html.escape(f"{p['nombre']}{tenor_tag}")

        svg_elements.append(
            f'<rect x="{legend_x}" y="{legend_y - 11}" width="12" height="12" fill="{badge_fill}" '
            f'stroke="{badge_border}" stroke-width="1.5" rx="3" />'
            f'<text x="{legend_x + 18}" y="{legend_y}" fill="#e2e8f0" font-weight="{"bold" if p["es_tenor"] else "normal"}">'
            f'{nombre_safe}</text>'
        )
        legend_x += len(nombre_safe) * 7 + 36
    svg_elements.append('</g>')

    # Carriles de fondo por semitono (fondo tipo DAW / piano roll)
    svg_elements.append('<g class="pianoroll-pitch-grid">')
    for semitono_idx in range(total_semitonos):
        pitch = max_midi - semitono_idx
        y_lane = margin_top + semitono_idx * lane_height
        nombre_nota = midi_a_nombre_nota(pitch)
        es_tecla_negra = "#" in nombre_nota

        bg_color = "#1e293b" if es_tecla_negra else "#0f172a"
        svg_elements.append(
            f'<rect x="{margin_left}" y="{y_lane:.2f}" width="{plot_width}" height="{lane_height:.2f}" '
            f'fill="{bg_color}" />'
        )

        # Línea divisoria suave
        svg_elements.append(
            f'<line x1="{margin_left}" y1="{y_lane:.2f}" x2="{margin_left + plot_width}" y2="{y_lane:.2f}" '
            f'stroke="#334155" stroke-width="0.5" stroke-opacity="0.4" />'
        )

        # Etiqueta de nota a la izquierda (notas C y F siempre, o cada dos semitonos)
        if nombre_nota.startswith("C") and not es_tecla_negra:
            svg_elements.append(
                f'<text x="{margin_left - 8}" y="{y_lane + lane_height * 0.75:.2f}" text-anchor="end" '
                f'fill="#38bdf8" font-family="monospace" font-size="11" font-weight="bold">{nombre_nota}</text>'
            )
            # Línea guía más marcada en los C
            svg_elements.append(
                f'<line x1="{margin_left}" y1="{y_lane:.2f}" x2="{margin_left + plot_width}" y2="{y_lane:.2f}" '
                f'stroke="#0284c7" stroke-width="1" stroke-opacity="0.5" />'
            )
        elif not es_tecla_negra and pitch % 2 == 0:
            svg_elements.append(
                f'<text x="{margin_left - 8}" y="{y_lane + lane_height * 0.75:.2f}" text-anchor="end" '
                f'fill="#64748b" font-family="monospace" font-size="10">{nombre_nota}</text>'
            )
    svg_elements.append('</g>')

    # Líneas verticales y etiquetas de compases
    svg_elements.append('<g class="pianoroll-measure-grid" font-family="system-ui, sans-serif" font-size="11">')
    if compases_info:
        for c in compases_info:
            c_offset = c["offset"]
            x_measure = margin_left + (c_offset / duracion_total) * plot_width
            svg_elements.append(
                f'<line x1="{x_measure:.2f}" y1="{margin_top}" x2="{x_measure:.2f}" y2="{margin_top + plot_height}" '
                f'stroke="#475569" stroke-width="1.2" />'
                f'<text x="{x_measure + 4:.2f}" y="{margin_top + plot_height + 20}" fill="#94a3b8" '
                f'font-weight="bold">c.{c["numero"]}</text>'
            )
    else:
        # Si no hay compases explícitos, dibujar cuartos regulares
        num_divs = max(4, int(duracion_total / 4))
        for step in range(num_divs + 1):
            x_div = margin_left + (step / num_divs) * plot_width
            svg_elements.append(
                f'<line x1="{x_div:.2f}" y1="{margin_top}" x2="{x_div:.2f}" y2="{margin_top + plot_height}" '
                f'stroke="#334155" stroke-width="1" />'
                f'<text x="{x_div + 4:.2f}" y="{margin_top + plot_height + 20}" fill="#94a3b8">c.{step + 1}</text>'
            )
    svg_elements.append('</g>')

    # Borde exterior del área de notas
    svg_elements.append(
        f'<rect x="{margin_left}" y="{margin_top}" width="{plot_width}" height="{plot_height}" '
        f'fill="none" stroke="#475569" stroke-width="1.5" />'
    )

    # Renderizado de notas (primero las voces secundarias, luego el Tenor para que quede en primer plano)
    notas_ordenadas = sorted(notas, key=lambda n: 1 if n["es_tenor"] else 0)

    hay_tenor = any(p["es_tenor"] for p in partes_info)

    svg_elements.append('<g class="pianoroll-notes">')
    for n in notas_ordenadas:
        n_x = margin_left + (n["offset"] / duracion_total) * plot_width
        n_w = max(4.0, (n["duracion"] / duracion_total) * plot_width - 1.0)
        n_y = margin_top + (max_midi - n["midi"]) * lane_height + 1.0
        n_h = max(3.0, lane_height - 2.0)

        p_info = partes_info[n["part_idx"]]
        es_tenor = n["es_tenor"]

        # Estilo de resaltado del Tenor
        if es_tenor:
            fill_color = "#f59e0b"
            stroke_color = "#fbbf24"
            stroke_width = "2"
            opacity = "1.0"
            filter_attr = 'filter="drop-shadow(0 0 3px rgba(245, 158, 11, 0.7))"'
        else:
            fill_color = p_info["color"]
            stroke_color = p_info["borde"]
            stroke_width = "1"
            # Si hay tenor resaltado, suavizar ligeramente las otras voces para que destaque
            opacity = "0.7" if hay_tenor else "0.9"
            filter_attr = ""

        title_tip = html.escape(f"{n['part_nombre']}: {n['nombre_nota']} (dur: {n['duracion']} pulso(s))")

        svg_elements.append(
            f'<rect class="pianoroll-note {"is-tenor" if es_tenor else ""}" '
            f'x="{n_x:.2f}" y="{n_y:.2f}" width="{n_w:.2f}" height="{n_h:.2f}" '
            f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" '
            f'rx="3" ry="3" opacity="{opacity}" {filter_attr} data-midi="{n["midi"]}" '
            f'data-voice="{html.escape(n["part_nombre"])}">'
            f'<title>{title_tip}</title>'
            f'</rect>'
        )

        # Si el bloque de la nota es suficientemente ancho, inscribir el nombre de la nota
        if n_w >= 28 and n_h >= 11:
            svg_elements.append(
                f'<text x="{n_x + 4:.2f}" y="{n_y + n_h * 0.75:.2f}" fill="#ffffff" '
                f'font-family="system-ui, sans-serif" font-size="9" font-weight="bold" '
                f'pointer-events="none">{html.escape(n["nombre_nota"])}</text>'
            )

    svg_elements.append('</g>')

    # Cursor vertical sincronizado con reproducción (playhead)
    svg_elements.append(
        f'<line class="pianoroll-playhead" id="pianoroll-playhead" '
        f'x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" '
        f'stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" '
        f'data-left="{margin_left}" data-width="{plot_width}" '
        f'data-total-ql="{duracion_total}" style="display: none;" />'
    )

    svg_open = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'class="pianoroll-svg" width="100%" height="auto" preserveAspectRatio="xMidYMid meet" '
        f'data-total-ql="{duracion_total}" data-left-margin="{margin_left}" data-plot-width="{plot_width}">'
    )
    svg_close = '</svg>'

    return svg_open + "".join(svg_elements) + svg_close
