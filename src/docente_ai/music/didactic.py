"""Módulo de componentes didácticos musicales deterministas.

Genera representaciones visuales SVG y datos matemáticos/acústicos exactos
a partir de la teoría musical clásica (Antigua Grecia, acústica pitagórica),
separando estrictamente el contenido calculado (intervalos, frecuencias, cents)
del contenido factual (autores, fechas, tratados procedentes de las fuentes).
"""

from dataclasses import dataclass
from pathlib import Path
import math
import re
from typing import Any
import yaml


# ============================================================================
# 1. GRAN SISTEMA PERFECTO (Systema Teleion Meizon)
# ============================================================================

SUBTITULO_GSP = (
    "dos pares de tetracordos conjuntos separados por una disyunción, "
    "más el proslambanómenos; synemmenon como tetracordo conjunto alternativo"
)

# Las 15 notas del Gran Sistema Perfecto diatónico (La2 a La4)
# Con sus frecuencias teóricas calculadas por proporciones pitagóricas puras
# y por el sistema temperado moderno (12-EDO).
NOTAS_GRAN_SISTEMA_PERFECTO = [
    {
        'id': 'proslambanomenos',
        'nombre_griego': 'Proslambanómenos',
        'transliteracion': 'Proslambanomenos',
        'nota_moderna': 'La2',
        'pitch': 'A2',
        'freq_pitagorica': 110.0,
        'freq_temperada': 110.0,
        'freq_hz': 110.0,
        'tetracordo': None,
        'descripcion': 'Sonido grave añadido en la base del sistema; no forma parte de ningún tetracordo.'
    },
    {
        'id': 'hypate_hypaton',
        'nombre_griego': 'Hypate hypaton',
        'transliteracion': 'Hypate hypaton',
        'nota_moderna': 'Si2',
        'pitch': 'B2',
        'freq_pitagorica': 123.75,
        'freq_temperada': 123.47,
        'freq_hz': 123.75,
        'tetracordo': 'hypaton',
        'descripcion': 'Principal o más grave de las más graves.'
    },
    {
        'id': 'parhypate_hypaton',
        'nombre_griego': 'Parhypate hypaton',
        'transliteracion': 'Parhypate hypaton',
        'nota_moderna': 'Do3',
        'pitch': 'C3',
        'freq_pitagorica': 130.37,
        'freq_temperada': 130.81,
        'freq_hz': 130.37,
        'tetracordo': 'hypaton',
        'descripcion': 'Junto a la más grave de las más graves.'
    },
    {
        'id': 'lichanos_hypaton',
        'nombre_griego': 'Lichanos hypaton',
        'transliteracion': 'Lichanos hypaton',
        'nota_moderna': 'Re3',
        'pitch': 'D3',
        'freq_pitagorica': 146.67,
        'freq_temperada': 146.83,
        'freq_hz': 146.67,
        'tetracordo': 'hypaton',
        'descripcion': 'Nota del dedo índice de las más graves.'
    },
    {
        'id': 'hypate_meson',
        'nombre_griego': 'Hypate meson',
        'transliteracion': 'Hypate meson',
        'nota_moderna': 'Mi3',
        'pitch': 'E3',
        'freq_pitagorica': 165.0,
        'freq_temperada': 164.81,
        'freq_hz': 165.0,
        'tetracordo': 'hypaton_y_meson',  # Nexo conjunto o sinaphe
        'descripcion': 'Más grave de las medias; nexo de conjunción entre Hypaton y Meson.'
    },
    {
        'id': 'parhypate_meson',
        'nombre_griego': 'Parhypate meson',
        'transliteracion': 'Parhypate meson',
        'nota_moderna': 'Fa3',
        'pitch': 'F3',
        'freq_pitagorica': 173.83,
        'freq_temperada': 174.61,
        'freq_hz': 173.83,
        'tetracordo': 'meson',
        'descripcion': 'Junto a la más grave de las medias.'
    },
    {
        'id': 'lichanos_meson',
        'nombre_griego': 'Lichanos meson',
        'transliteracion': 'Lichanos meson',
        'nota_moderna': 'Sol3',
        'pitch': 'G3',
        'freq_pitagorica': 195.56,
        'freq_temperada': 196.0,
        'freq_hz': 195.56,
        'tetracordo': 'meson',
        'descripcion': 'Dedo índice de las medias.'
    },
    {
        'id': 'mese',
        'nombre_griego': 'Mese',
        'transliteracion': 'Mese',
        'nota_moderna': 'La3',
        'pitch': 'A3',
        'freq_pitagorica': 220.0,
        'freq_temperada': 220.0,
        'freq_hz': 220.0,
        'tetracordo': 'meson',
        'descripcion': 'Nota central y eje gravitatorio y tonal de todo el sistema.'
    },
    {
        'id': 'paramese',
        'nombre_griego': 'Paramese',
        'transliteracion': 'Paramese',
        'nota_moderna': 'Si3',
        'pitch': 'B3',
        'freq_pitagorica': 247.5,
        'freq_temperada': 246.94,
        'freq_hz': 247.5,
        'tetracordo': 'diezeugmenon',
        'descripcion': 'Junto a la central; separada de Mese por el tono de disyunción (diazeuxis).'
    },
    {
        'id': 'trite_diezeugmenon',
        'nombre_griego': 'Trite diezeugmenon',
        'transliteracion': 'Trite diezeugmenon',
        'nota_moderna': 'Do4',
        'pitch': 'C4',
        'freq_pitagorica': 260.74,
        'freq_temperada': 261.63,
        'freq_hz': 260.74,
        'tetracordo': 'diezeugmenon',
        'descripcion': 'Tercera nota de las disjuntas.'
    },
    {
        'id': 'paranete_diezeugmenon',
        'nombre_griego': 'Paranete diezeugmenon',
        'transliteracion': 'Paranete diezeugmenon',
        'nota_moderna': 'Re4',
        'pitch': 'D4',
        'freq_pitagorica': 293.33,
        'freq_temperada': 293.66,
        'freq_hz': 293.33,
        'tetracordo': 'diezeugmenon',
        'descripcion': 'Junto a la última de las disjuntas.'
    },
    {
        'id': 'nete_diezeugmenon',
        'nombre_griego': 'Nete diezeugmenon',
        'transliteracion': 'Nete diezeugmenon',
        'nota_moderna': 'Mi4',
        'pitch': 'E4',
        'freq_pitagorica': 330.0,
        'freq_temperada': 329.63,
        'freq_hz': 330.0,
        'tetracordo': 'diezeugmenon_y_hyperbolaion',  # Nexo conjunto
        'descripcion': 'Última de las disjuntas; nexo de conjunción con Hyperbolaion.'
    },
    {
        'id': 'trite_hyperbolaion',
        'nombre_griego': 'Trite hyperbolaion',
        'transliteracion': 'Trite hyperbolaion',
        'nota_moderna': 'Fa4',
        'pitch': 'F4',
        'freq_pitagorica': 347.65,
        'freq_temperada': 349.23,
        'freq_hz': 347.65,
        'tetracordo': 'hyperbolaion',
        'descripcion': 'Tercera de las supremas o más altas.'
    },
    {
        'id': 'paranete_hyperbolaion',
        'nombre_griego': 'Paranete hyperbolaion',
        'transliteracion': 'Paranete hyperbolaion',
        'nota_moderna': 'Sol4',
        'pitch': 'G4',
        'freq_pitagorica': 391.11,
        'freq_temperada': 392.0,
        'freq_hz': 391.11,
        'tetracordo': 'hyperbolaion',
        'descripcion': 'Junto a la última de las supremas.'
    },
    {
        'id': 'nete_hyperbolaion',
        'nombre_griego': 'Nete hyperbolaion',
        'transliteracion': 'Nete hyperbolaion',
        'nota_moderna': 'La4',
        'pitch': 'A4',
        'freq_pitagorica': 440.0,
        'freq_temperada': 440.0,
        'freq_hz': 440.0,
        'tetracordo': 'hyperbolaion',
        'descripcion': 'Última de las supremas; extremo agudo (doble octava de Proslambanomenos).'
    },
]

# Tetracordo Synemmenon (alternativa modulante / conjunta desde Mese La3)
NOTAS_TETRACORDO_SYNEMMENON = [
    {'id': 'mese_syn', 'nombre_griego': 'Mese', 'nota_moderna': 'La3', 'pitch': 'A3', 'freq_pitagorica': 220.0, 'freq_temperada': 220.0},
    {'id': 'trite_syn', 'nombre_griego': 'Trite synemmenon', 'nota_moderna': 'Si♭3', 'pitch': 'Bb3', 'freq_pitagorica': 231.77, 'freq_temperada': 233.08},
    {'id': 'paranete_syn', 'nombre_griego': 'Paranete synemmenon', 'nota_moderna': 'Do4', 'pitch': 'C4', 'freq_pitagorica': 260.74, 'freq_temperada': 261.63},
    {'id': 'nete_syn', 'nombre_griego': 'Nete synemmenon', 'nota_moderna': 'Re4', 'pitch': 'D4', 'freq_pitagorica': 293.33, 'freq_temperada': 293.66},
]


def generar_svg_gran_sistema_perfecto(ancho: int = 980, alto: int = 370) -> str:
    """Genera un SVG determinista del diagrama de alturas del Gran Sistema Perfecto,
    sin líneas de falso pentagrama, sin título duplicado, y con corchetes claros."""
    notas = NOTAS_GRAN_SISTEMA_PERFECTO
    n = len(notas)
    margen_x = 65
    espacio_x = (ancho - 2 * margen_x) / (n - 1)

    # Coordenadas X de cada nota (0 a 14)
    p_x = [margen_x + i * espacio_x for i in range(n)]

    # Altura Y en diagrama acústico (base La2 = 240, La4 = 90)
    y_min = 90
    y_max = 240
    # La escala musical asciende de La2 (110 Hz) a La4 (440 Hz)
    p_y = [y_max - (i / (n - 1)) * (y_max - y_min) for i in range(n)]

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" class="didactic-svg didactic-gsp">',
        '<style>',
        '.gsp-bg { fill: #fcfcfd; rx: 8px; }',
        '.gsp-grid-line { stroke: #e2e8f0; stroke-width: 1; stroke-dasharray: 4,4; }',
        '.gsp-bracket { stroke: #0284c7; stroke-width: 2; fill: none; }',
        '.gsp-bracket-syn { stroke: #7c3aed; stroke-width: 2; fill: none; }',
        '.gsp-bracket-disj { stroke: #ea580c; stroke-width: 2; stroke-dasharray: 3,3; fill: none; }',
        '.gsp-bracket-label { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 700; text-anchor: middle; }',
        '.gsp-note-stem { stroke: #94a3b8; stroke-width: 1.5; stroke-dasharray: 2,2; }',
        '.gsp-note-head { fill: #0f172a; stroke: #38bdf8; stroke-width: 2; cursor: pointer; transition: r 0.15s, fill 0.15s; }',
        '.gsp-note-head:hover { fill: #0284c7; r: 8; }',
        '.gsp-mese-head { fill: #d97706; stroke: #fef08a; stroke-width: 2.5; cursor: pointer; }',
        '.gsp-prosl-head { fill: #475569; stroke: #cbd5e1; stroke-width: 2; }',
        '.gsp-note-text { font-family: system-ui, sans-serif; font-size: 12px; font-weight: 700; fill: #0f172a; text-anchor: middle; }',
        '.gsp-note-hz { font-family: system-ui, sans-serif; font-size: 10px; font-weight: 600; fill: #0284c7; text-anchor: middle; }',
        '.gsp-sub-label { font-family: system-ui, sans-serif; font-size: 10.5px; fill: #64748b; text-anchor: middle; }',
        '</style>',
        f'<rect width="{ancho}" height="{alto}" class="gsp-bg"/>',
    ]

    # Líneas de referencia de altura en el fondo
    for h_y, h_label in [(y_max, "La2 (110 Hz)"), (y_max - 75, "La3 (220 Hz · Mese)"), (y_min, "La4 (440 Hz)")]:
        svg.append(f'<line x1="{margen_x - 20}" y1="{h_y}" x2="{ancho - margen_x + 20}" y2="{h_y}" class="gsp-grid-line"/>')
        svg.append(f'<text x="{margen_x - 25}" y="{h_y + 4}" class="gsp-sub-label" style="text-anchor:end; font-size:9.5px;">{h_label}</text>')

    # 1. Corchete Proslambanómenos (La2, nota 0)
    svg.append(f'<line x1="{p_x[0]}" y1="288" x2="{p_x[0]}" y2="298" class="gsp-note-stem"/>')
    svg.append(f'<text x="{p_x[0]}" y="308" class="gsp-bracket-label" style="fill:#475569; font-size:10px;">Proslambanómenos</text>')
    svg.append(f'<text x="{p_x[0]}" y="320" class="gsp-sub-label" style="font-size:9px;">(Nota añadida)</text>')

    # 2. Corchete Tetracordo Hypaton (Si2 [1] a Mi3 [4])
    y_b1 = 65
    svg.append(f'<path d="M {p_x[1]} {y_b1+8} L {p_x[1]} {y_b1} L {p_x[4]} {y_b1} L {p_x[4]} {y_b1+8}" class="gsp-bracket"/>')
    svg.append(f'<text x="{(p_x[1] + p_x[4])/2}" y="{y_b1 - 6}" class="gsp-bracket-label" style="fill:#0284c7;">T. Hypaton (Si2–Mi3)</text>')

    # 3. Corchete Tetracordo Meson (Mi3 [4] a La3 [7]) - CONJUNTO con Hypaton en Mi3
    svg.append(f'<path d="M {p_x[4]} {y_b1+8} L {p_x[4]} {y_b1} L {p_x[7]} {y_b1} L {p_x[7]} {y_b1+8}" class="gsp-bracket"/>')
    svg.append(f'<text x="{(p_x[4] + p_x[7])/2}" y="{y_b1 - 6}" class="gsp-bracket-label" style="fill:#0284c7;">T. Meson (Mi3–La3)</text>')

    # Marca de sinaphe en Mi3
    svg.append(f'<circle cx="{p_x[4]}" cy="{y_b1}" r="3.5" fill="#0284c7"/>')
    svg.append(f'<text x="{p_x[4]}" y="{y_b1 + 20}" class="gsp-sub-label" style="fill:#0284c7; font-weight:700;">Conjunción (Mi3)</text>')

    # 4. Tono de disyunción (diazeuxis) entre La3 (Mese [7]) y Si3 (Paramese [8])
    y_disj = 45
    svg.append(f'<path d="M {p_x[7]} {y_disj+8} L {p_x[7]} {y_disj} L {p_x[8]} {y_disj} L {p_x[8]} {y_disj+8}" class="gsp-bracket-disj"/>')
    svg.append(f'<text x="{(p_x[7] + p_x[8])/2}" y="{y_disj - 5}" class="gsp-bracket-label" style="fill:#ea580c;">Disyunción (9:8)</text>')

    # 5. Corchete Tetracordo Diezeugmenon (Si3 [8] a Mi4 [11])
    svg.append(f'<path d="M {p_x[8]} {y_b1+8} L {p_x[8]} {y_b1} L {p_x[11]} {y_b1} L {p_x[11]} {y_b1+8}" class="gsp-bracket"/>')
    svg.append(f'<text x="{(p_x[8] + p_x[11])/2}" y="{y_b1 - 6}" class="gsp-bracket-label" style="fill:#0284c7;">T. Diezeugmenon (Si3–Mi4)</text>')

    # 6. Corchete Tetracordo Hyperbolaion (Mi4 [11] a La4 [14]) - CONJUNTO con Diezeugmenon en Mi4
    svg.append(f'<path d="M {p_x[11]} {y_b1+8} L {p_x[11]} {y_b1} L {p_x[14]} {y_b1} L {p_x[14]} {y_b1+8}" class="gsp-bracket"/>')
    svg.append(f'<text x="{(p_x[11] + p_x[14])/2}" y="{y_b1 - 6}" class="gsp-bracket-label" style="fill:#0284c7;">T. Hyperbolaion (Mi4–La4)</text>')

    # Marca de sinaphe en Mi4
    svg.append(f'<circle cx="{p_x[11]}" cy="{y_b1}" r="3.5" fill="#0284c7"/>')
    svg.append(f'<text x="{p_x[11]}" y="{y_b1 + 20}" class="gsp-sub-label" style="fill:#0284c7; font-weight:700;">Conjunción (Mi4)</text>')

    # 7. Tetracordo Synemmenon (abajo, desde Mese La3 [7] a Re4 [10])
    y_syn = 315
    svg.append(f'<path d="M {p_x[7]} {y_syn-8} L {p_x[7]} {y_syn} L {p_x[10]} {y_syn} L {p_x[10]} {y_syn-8}" class="gsp-bracket-syn"/>')
    svg.append(f'<text x="{(p_x[7] + p_x[10])/2}" y="{y_syn + 18}" class="gsp-bracket-label" style="fill:#7c3aed;">T. Synemmenon (La3–Sib3–Do4–Re4) · Conjunto Modulante</text>')

    # Dibujar las 15 notas
    for i, item in enumerate(notas):
        x, y = p_x[i], p_y[i]
        is_mese = (item['id'] == 'mese')
        is_prosl = (item['id'] == 'proslambanomenos')

        cls_head = 'gsp-mese-head' if is_mese else ('gsp-prosl-head' if is_prosl else 'gsp-note-head')
        r_head = 7.5 if is_mese else 6.0

        # Línea guía vertical
        svg.append(f'<line x1="{x}" y1="{y + r_head}" x2="{x}" y2="255" class="gsp-note-stem"/>')

        # Cabeza de nota interactiva
        svg.append(
            f'<circle cx="{x}" cy="{y}" r="{r_head}" class="{cls_head}" '
            f'data-index="{i}" data-pitch="{item["pitch"]}" '
            f'data-freq-pit="{item["freq_pitagorica"]}" data-freq-temp="{item["freq_temperada"]}"/>'
        )

        # Nombre moderno (ej. La2, Si2...)
        weight = 'font-weight:700; fill:#d97706;' if is_mese else ''
        svg.append(f'<text x="{x}" y="270" class="gsp-note-text" style="{weight}">{item["nota_moderna"]}</text>')

        # Frecuencia pitagórica por defecto
        freq_txt = f'{item["freq_pitagorica"]:.1f}' if item['freq_pitagorica'] != round(item['freq_pitagorica']) else f'{int(item["freq_pitagorica"])}'
        svg.append(f'<text x="{x}" y="283" class="gsp-note-hz" data-gsp-hz-idx="{i}">{freq_txt} Hz</text>')

    svg.append('</svg>')
    return '\n'.join(svg)


# ============================================================================
# 2. MONOCORDIO PITAGÓRICO (División acústica de la cuerda)
# ============================================================================

@dataclass
class MonocordioDivision:
    fraccion: str
    ratio_numerico: float
    intervalo_griego: str
    intervalo_moderno: str
    nombre_proporcion: str
    proporcion_frecuencia: str
    freq_pitagorica: float
    freq_temperada: float
    pos_x_norm: float
    descripcion: str


DIVISIONES_MONOCORDIO = [
    MonocordioDivision(
        fraccion='1/1',
        ratio_numerico=1.0,
        intervalo_griego='Unísono',
        intervalo_moderno='Unísono',
        nombre_proporcion='Unísono (1:1)',
        proporcion_frecuencia='1:1',
        freq_pitagorica=220.0,
        freq_temperada=220.0,
        pos_x_norm=1.0,
        descripcion='Cuerda entera vibrante al aire (tono base de referencia).'
    ),
    MonocordioDivision(
        fraccion='3/4',
        ratio_numerico=0.75,
        intervalo_griego='Diatessaron (διὰ τεσσάρων)',
        intervalo_moderno='Cuarta justa',
        nombre_proporcion='epítriton (4:3)',
        proporcion_frecuencia='4:3',
        freq_pitagorica=round(220.0 * 4.0 / 3.0, 2),  # 293.33 Hz exacto
        freq_temperada=round(220.0 * (2.0 ** (5.0 / 12.0)), 2),  # 293.66 Hz
        pos_x_norm=0.75,
        descripcion='3/4 de la cuerda vibrante; proporción epítriton (4:3 de frecuencia).'
    ),
    MonocordioDivision(
        fraccion='2/3',
        ratio_numerico=0.6667,
        intervalo_griego='Diapente (διὰ πέντε)',
        intervalo_moderno='Quinta justa',
        nombre_proporcion='hemiólion (3:2)',
        proporcion_frecuencia='3:2',
        freq_pitagorica=round(220.0 * 3.0 / 2.0, 2),  # 330.0 Hz exacto
        freq_temperada=round(220.0 * (2.0 ** (7.0 / 12.0)), 2),  # 329.63 Hz
        pos_x_norm=0.6667,
        descripcion='2/3 de la cuerda vibrante; proporción hemiólion (3:2 de frecuencia).'
    ),
    MonocordioDivision(
        fraccion='1/2',
        ratio_numerico=0.5,
        intervalo_griego='Diapason (διὰ πασῶν)',
        intervalo_moderno='Octava justa',
        nombre_proporcion='diplásion (2:1)',
        proporcion_frecuencia='2:1',
        freq_pitagorica=round(220.0 * 2.0, 2),  # 440.0 Hz exacto
        freq_temperada=440.0,
        pos_x_norm=0.5,
        descripcion='1/2 de la cuerda vibrante; proporción diplásion (2:1 de frecuencia).'
    ),
]


def generar_svg_monocordio(ancho: int = 900, alto: int = 310) -> str:
    """Genera un SVG determinista del monocordio pitagórico con puentes móviles,
    divisiones marcadas (1/2, 2/3, 3/4), proporciones y frecuencias exactas."""
    x_inicio = 80
    x_fin = ancho - 80
    longitud = x_fin - x_inicio
    y_cuerda = 135

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" class="didactic-svg didactic-monochord">',
        '<style>',
        '.mc-bg { fill: #fdfbf7; rx: 8px; }',
        '.mc-box { fill: #f1f5f9; stroke: #94a3b8; stroke-width: 2; rx: 6px; }',
        '.mc-string { stroke: #d97706; stroke-width: 4; stroke-linecap: round; }',
        '.mc-bridge-fixed { fill: #475569; stroke: #0f172a; stroke-width: 1.5; }',
        '.mc-bridge-mobile { fill: #2563eb; stroke: #1d4ed8; stroke-width: 1.5; cursor: pointer; transition: fill 0.15s; }',
        '.mc-bridge-mobile:hover { fill: #1d4ed8; filter: drop-shadow(0 2px 4px rgba(37,99,235,0.3)); }',
        '.mc-text-frac { font-family: system-ui, sans-serif; font-size: 14px; font-weight: 700; fill: #0f172a; text-anchor: middle; }',
        '.mc-text-name { font-family: system-ui, sans-serif; font-size: 11.5px; font-weight: 700; fill: #1d4ed8; text-anchor: middle; }',
        '.mc-text-prop { font-family: system-ui, sans-serif; font-size: 10px; font-weight: 600; fill: #475569; text-anchor: middle; }',
        '.mc-text-hz { font-family: system-ui, sans-serif; font-size: 10.5px; font-weight: 700; fill: #0284c7; text-anchor: middle; }',
        '.mc-rule-line { stroke: #cbd5e1; stroke-width: 1.2; stroke-dasharray: 2,2; }',
        '.mc-footer { font-family: system-ui, sans-serif; font-size: 11px; fill: #64748b; font-style: italic; text-anchor: middle; }',
        '</style>',
        f'<rect width="{ancho}" height="{alto}" class="mc-bg"/>',
        # Caja armónica resonadora
        f'<rect x="{x_inicio - 25}" y="115" width="{longitud + 50}" height="40" class="mc-box"/>',
        # Cuerda completa
        f'<line x1="{x_inicio}" y1="{y_cuerda}" x2="{x_fin}" y2="{y_cuerda}" class="mc-string"/>',
        # Puente fijo extremo izquierdo
        f'<polygon points="{x_inicio-8},{y_cuerda+18} {x_inicio},{y_cuerda-6} {x_inicio+8},{y_cuerda+18}" class="mc-bridge-fixed"/>',
        # Puente fijo extremo derecho
        f'<polygon points="{x_fin-8},{y_cuerda+18} {x_fin},{y_cuerda-6} {x_fin+8},{y_cuerda+18}" class="mc-bridge-fixed"/>',
    ]

    for i, div in enumerate(DIVISIONES_MONOCORDIO):
        x_puente = x_inicio + longitud * div.pos_x_norm

        # Línea de regla hacia arriba
        svg.append(f'<line x1="{x_puente}" y1="55" x2="{x_puente}" y2="{y_cuerda-8}" class="mc-rule-line"/>')

        # Puente móvil en la cuerda
        svg.append(
            f'<polygon points="{x_puente-7},{y_cuerda+16} {x_puente},{y_cuerda-5} {x_puente+7},{y_cuerda+16}" '
            f'class="mc-bridge-mobile" data-div-idx="{i}" '
            f'data-freq-pit="{div.freq_pitagorica}" data-freq-temp="{div.freq_temperada}"/>'
        )

        # Fracción (1/2, 2/3, 3/4, 1/1)
        svg.append(f'<text x="{x_puente}" y="70" class="mc-text-frac">{div.fraccion}</text>')

        # Intervalo y nombre de proporción exacto escalonados verticalmente
        if div.pos_x_norm == 0.6667:
            label_y = 212
        elif div.pos_x_norm == 0.75:
            label_y = 168
        else:
            label_y = 175
        svg.append(f'<text x="{x_puente}" y="{label_y}" class="mc-text-name">{div.intervalo_moderno}</text>')
        svg.append(f'<text x="{x_puente}" y="{label_y + 13}" class="mc-text-prop">{div.nombre_proporcion}</text>')
        svg.append(f'<text x="{x_puente}" y="{label_y + 26}" class="mc-text-hz" data-mc-hz-idx="{i}">{div.freq_pitagorica:.2f} Hz</text>')

    # Nota interactiva al pie
    svg.append(
        f'<text x="{ancho // 2}" y="{alto - 14}" class="mc-footer">'
        'Haz clic en cualquier puente móvil para escuchar la afinación calculada en Web Audio.'
        '</text>'
    )
    svg.append('</svg>')
    return '\n'.join(svg)


# ============================================================================
# 3. ESCALERA DE INTERVALOS EN CENTS (Comparativa de los 3 géneros)
# ============================================================================

@dataclass
class IntervaloEscalera:
    nombre: str
    cents: float
    nota_inicio: str
    nota_fin: str
    color: str


GENEROS_ESCALERA = {
    'diatonico': {
        'titulo': 'Género Diatónico',
        'subtitulo': 'Semitono + Tono + Tono (Aristóxeno: 100c + 200c + 200c | Pitagórico: 90.2c + 203.9c + 203.9c)',
        'intervalos': [
            IntervaloEscalera('Semitono (hemitonion)', 100.0, 'Si3', 'Do4', '#3b82f6'),
            IntervaloEscalera('Tono (tonos)', 200.0, 'Do4', 'Re4', '#0284c7'),
            IntervaloEscalera('Tono (tonos)', 200.0, 'Re4', 'Mi4', '#0369a1'),
        ]
    },
    'cromatico': {
        'titulo': 'Género Cromático',
        'subtitulo': 'Semitono + Semitono + Trihemitono (100c + 100c + 300c = tono y medio)',
        'intervalos': [
            IntervaloEscalera('Semitono', 100.0, 'Si3', 'Do4', '#8b5cf6'),
            IntervaloEscalera('Semitono', 100.0, 'Do4', 'Do#4', '#7c3aed'),
            IntervaloEscalera('Trihemitono (3 semitonos)', 300.0, 'Do#4', 'Mi4', '#6d28d9'),
        ]
    },
    'enarmonico': {
        'titulo': 'Género Enarmónico (Microtonal)',
        'subtitulo': 'Díesis (cuarto de tono) + Díesis + Ditono (50c + 50c + 400c = dos tonos completos)',
        'intervalos': [
            IntervaloEscalera('Díesis (¼ tono)', 50.0, 'Si3', 'Si+¼', '#ec4899'),
            IntervaloEscalera('Díesis (¼ tono)', 50.0, 'Si+¼', 'Do4', '#db2777'),
            IntervaloEscalera('Ditono (2 tonos)', 400.0, 'Do4', 'Mi4', '#be185d'),
        ]
    }
}


def generar_svg_escalera_intervalos(ancho: int = 920, alto: int = 340) -> str:
    """Genera un SVG determinista comparando a escala en cents los tres géneros de tetracordos."""
    margen_izq = 175
    margen_der = 50
    ancho_escala = ancho - margen_izq - margen_der
    max_cents = 500.0  # Cuarta justa = 498-500 cents
    px_por_cent = ancho_escala / max_cents

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" class="didactic-svg didactic-ladder">',
        '<style>',
        '.ld-bg { fill: #fcfcfd; rx: 8px; }',
        '.ld-rule { stroke: #cbd5e1; stroke-width: 1; }',
        '.ld-rule-label { font-family: system-ui, sans-serif; font-size: 10px; fill: #64748b; text-anchor: middle; }',
        '.ld-genre-title { font-family: system-ui, sans-serif; font-size: 12.5px; font-weight: 700; fill: #0f172a; text-anchor: end; }',
        '.ld-genre-sub { font-family: system-ui, sans-serif; font-size: 10px; fill: #64748b; text-anchor: end; }',
        '.ld-bar-text { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 700; fill: #ffffff; text-anchor: middle; }',
        '.ld-sub { font-family: system-ui, sans-serif; font-size: 11px; fill: #475569; }',
        '</style>',
        f'<rect width="{ancho}" height="{alto}" class="ld-bg"/>',
    ]

    # Regla horizontal de cents en la parte superior (0c a 500c)
    y_regla = 48
    svg.append(f'<line x1="{margen_izq}" y1="{y_regla}" x2="{margen_izq + ancho_escala}" y2="{y_regla}" class="ld-rule"/>')
    for c in range(0, 501, 100):
        xc = margen_izq + c * px_por_cent
        svg.append(f'<line x1="{xc}" y1="{y_regla - 5}" x2="{xc}" y2="{y_regla + 5}" class="ld-rule"/>')
        svg.append(f'<text x="{xc}" y="{y_regla - 8}" class="ld-rule-label">{c}c</text>')

    # Dibujar cada género en una franja horizontal
    generos_orden = ['diatonico', 'cromatico', 'enarmonico']
    y_base = 75
    altura_fila = 70

    for idx, gen_key in enumerate(generos_orden):
        gen_data = GENEROS_ESCALERA[gen_key]
        y_fila = y_base + idx * altura_fila

        svg.append(f'<text x="{margen_izq - 15}" y="{y_fila + 18}" class="ld-genre-title">{gen_data["titulo"]}</text>')
        resumen_formula = '1/4 + 1/4 + 2t' if gen_key == 'enarmonico' else ('1/2 + 1/2 + 1½t' if gen_key == 'cromatico' else '1/2 + 1t + 1t')
        svg.append(f'<text x="{margen_izq - 15}" y="{y_fila + 32}" class="ld-genre-sub">{resumen_formula}</text>')

        x_actual = margen_izq
        for inter in gen_data['intervalos']:
            w_bar = inter.cents * px_por_cent
            svg.append(
                f'<rect x="{x_actual}" y="{y_fila}" width="{w_bar}" height="36" '
                f'fill="{inter.color}" rx="3" style="stroke:#ffffff; stroke-width:1.5;"/>'
            )
            txt_label = f'{int(inter.cents)}c'
            if w_bar >= 85:
                txt_label += f' ({inter.nombre.split()[0]})'
            svg.append(f'<text x="{x_actual + w_bar/2}" y="{y_fila + 22}" class="ld-bar-text">{txt_label}</text>')
            x_actual += w_bar

    # Leyenda al pie
    svg.append(
        f'<text x="{ancho // 2}" y="{alto - 12}" class="ld-sub" style="text-anchor: middle;">'
        'El pyknon (acumulación de intervalos inferiores estrechos) en el enarmónico suma solo 100 cents (50 + 50), dejando un salto de ditono de 400 cents.'
        '</text>'
    )
    svg.append('</svg>')
    return '\n'.join(svg)


# ============================================================================
# 4. LÍNEA TEMPORAL DE AUTORES Y FUENTES HISTÓRICAS (Eje real de siglos)
# ============================================================================

# Diccionario canónico de tratadistas y figuras históricas para ubicar
# cronológicamente a los autores citados en las fuentes de la propuesta.
FIGURAS_HISTORICAS_GRIEGAS = {
    'pitagoras': {
        'nombre_canonico': 'Pitágoras de Samos',
        'epoca': 'c. 570–495 a. C.',
        'ano_numerico': -530,
        'aproximado': True,
        'obra_canon': 'Acústica del monocordio',
    },
    'platon': {
        'nombre_canonico': 'Platón',
        'epoca': 'c. 427–347 a. C.',
        'ano_numerico': -387,
        'aproximado': True,
        'obra_canon': 'La República (Timeo y educación musical)',
    },
    'aristoteles': {
        'nombre_canonico': 'Aristóteles',
        'epoca': 'c. 384–322 a. C.',
        'ano_numerico': -350,
        'aproximado': True,
        'obra_canon': 'Política (Libro VIII: teoría del ethos)',
    },
    'aristoxeno': {
        'nombre_canonico': 'Aristóxeno de Tarento',
        'epoca': 'c. 375–300 a. C.',
        'ano_numerico': -335,
        'aproximado': True,
        'obra_canon': 'Elementos de armonía (Harmonika Stoicheia)',
    },
    'euclides': {
        'nombre_canonico': 'Euclides / Pseudo-Euclides',
        'epoca': 'c. 300 a. C.',
        'ano_numerico': -300,
        'aproximado': True,
        'obra_canon': 'División del canon (Sectio Canonis)',
    },
    'seikilos': {
        'nombre_canonico': 'Epitafio de Seikilos',
        'epoca': 'c. s. I–II d. C.',
        'ano_numerico': 50,
        'aproximado': True,
        'obra_canon': 'Inscripción en estela funeraria (Tralles)',
    },
    'ptolomeo': {
        'nombre_canonico': 'Claudio Ptolomeo',
        'epoca': 'c. 100–170 d. C.',
        'ano_numerico': 140,
        'aproximado': True,
        'obra_canon': 'Harmónicos (Harmonika)',
    },
    'alipio': {
        'nombre_canonico': 'Alipio de Alejandría',
        'epoca': 'c. s. IV d. C.',
        'ano_numerico': 350,
        'aproximado': True,
        'obra_canon': 'Introducción a la música (Tablas notacionales)',
    },
    'agustin': {
        'nombre_canonico': 'San Agustín de Hipona',
        'epoca': '354–430 d. C.',
        'ano_numerico': 390,
        'aproximado': False,
        'obra_canon': 'De musica (Seis libros)',
    },
    'boecio': {
        'nombre_canonico': 'Anicio Manlio Torcuato Severino Boecio',
        'epoca': 'c. 480–524 d. C.',
        'ano_numerico': 505,
        'aproximado': False,
        'obra_canon': 'De institutione musica',
    },
}


def construir_hitos_linea_temporal(
    evidence: list[dict[str, Any]] | None = None,
    autores_solicitados: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Construye dinámicamente los hitos de la línea temporal a partir de las fuentes
    citadas de la propuesta. Si un autor solicitado no tiene fuente en la biblioteca,
    se marca explícitamente como 'sin_fuente' para la guía docente."""
    hitos: list[dict[str, Any]] = []
    autores_en_fuentes: dict[str, dict[str, Any]] = {}

    def _normalizar(s: str) -> str:
        res = s.lower()
        for orig, dest in (('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ü', 'u')):
            res = res.replace(orig, dest)
        return res

    # 1. Extraer autores y obras de las fuentes efectivamente citadas
    for ev in (evidence or []):
        meta = ev.get('metadata') or {}
        titulo_doc = meta.get('title') or ev.get('source_title') or ''
        for autor_raw in (meta.get('authors') or []):
            autor_clean = str(autor_raw).strip()
            # Reconocer clave canónica
            key = None
            autor_norm = _normalizar(autor_clean)
            if 'plat' in autor_norm: key = 'platon'
            elif 'aristot' in autor_norm: key = 'aristoteles'
            elif 'aristox' in autor_norm: key = 'aristoxeno'
            elif 'pitag' in autor_norm: key = 'pitagoras'
            elif 'ptol' in autor_norm: key = 'ptolomeo'
            elif 'seikil' in autor_norm or 'epitaf' in autor_norm: key = 'seikilos'
            elif 'euclid' in autor_norm: key = 'euclides'
            elif 'boec' in autor_norm or 'boeth' in autor_norm: key = 'boecio'
            elif 'alipi' in autor_norm: key = 'alipio'
            elif 'agust' in autor_norm: key = 'agustin'

            if key and key not in autores_en_fuentes:
                canon = FIGURAS_HISTORICAS_GRIEGAS[key]
                autores_en_fuentes[key] = {
                    'key': key,
                    'autor': canon['nombre_canonico'],
                    'epoca': canon['epoca'],
                    'ano_numerico': canon['ano_numerico'],
                    'aproximado': canon['aproximado'],
                    'obra': titulo_doc or canon['obra_canon'],
                    'fuente': titulo_doc or 'Fuente autorizada en biblioteca',
                    'sin_fuente': False,
                }

    # Si hay autores en fuentes, añadirlos
    for item in autores_en_fuentes.values():
        hitos.append(item)

    # 2. Si se solicitaron autores específicos en parámetros
    for aut_sol in (autores_solicitados or []):
        aut_norm = _normalizar(aut_sol)
        key = None
        for k in FIGURAS_HISTORICAS_GRIEGAS:
            if k in aut_norm:
                key = k
                break
        if key and key not in autores_en_fuentes:
            canon = FIGURAS_HISTORICAS_GRIEGAS[key]
            hitos.append({
                'key': key,
                'autor': canon['nombre_canonico'],
                'epoca': canon['epoca'],
                'ano_numerico': canon['ano_numerico'],
                'aproximado': canon['aproximado'],
                'obra': canon['obra_canon'],
                'fuente': 'sin fuente en la biblioteca',
                'sin_fuente': True,
            })

    # Si no había fuentes citadas específicas (ej. test aislado), poblar con las figuras de Grecia relevantes
    if not hitos:
        for k in ('pitagoras', 'platon', 'aristoteles', 'aristoxeno', 'euclides', 'seikilos', 'ptolomeo', 'boecio'):
            canon = FIGURAS_HISTORICAS_GRIEGAS[k]
            hitos.append({
                'key': k,
                'autor': canon['nombre_canonico'],
                'epoca': canon['epoca'],
                'ano_numerico': canon['ano_numerico'],
                'aproximado': canon['aproximado'],
                'obra': canon['obra_canon'],
                'fuente': 'Referencia histórica',
                'sin_fuente': False,
            })

    # Ordenar estrictamente por año cronológico
    hitos.sort(key=lambda h: h['ano_numerico'])
    return hitos


def generar_svg_linea_temporal(
    hitos: list[dict[str, Any]] | None = None,
    para_alumnado: bool = False,
    ancho: int = 980,
    alto: int = 370
) -> str:
    """Genera un SVG determinista del eje cronológico real (600 a. C. a 600 d. C.)
    con distribución anticolisión escalonada en 4 niveles para evitar todo solapamiento."""
    hitos = hitos or construir_hitos_linea_temporal()

    # Si es para el alumnado, excluir los autores sin fuente autorizada
    if para_alumnado:
        hitos = [h for h in hitos if not h.get('sin_fuente')]

    ano_min = -600
    ano_max = 600
    margen_x = 75
    ancho_eje = ancho - 2 * margen_x
    y_eje = 185

    def ano_a_x(ano: int) -> float:
        return margen_x + ((ano - ano_min) / (ano_max - ano_min)) * ancho_eje

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" class="didactic-svg didactic-timeline">',
        '<style>',
        '.tl-bg { fill: #f8fafc; rx: 8px; }',
        '.tl-axis { stroke: #0f172a; stroke-width: 2.5; stroke-linecap: round; }',
        '.tl-era-divide { stroke: #dc2626; stroke-width: 1.5; stroke-dasharray: 4,3; }',
        '.tl-era-badge { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 800; fill: #dc2626; }',
        '.tl-century-tick { stroke: #94a3b8; stroke-width: 1.2; }',
        '.tl-century-label { font-family: system-ui, sans-serif; font-size: 9px; fill: #64748b; text-anchor: middle; }',
        '.tl-node { fill: #0284c7; stroke: #ffffff; stroke-width: 2; cursor: pointer; }',
        '.tl-stem { stroke: #0284c7; stroke-width: 1.2; }',
        '.tl-card-author { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 700; fill: #0f172a; }',
        '.tl-card-date { font-family: system-ui, sans-serif; font-size: 9.5px; fill: #0284c7; font-weight: 600; }',
        '.tl-card-work { font-family: system-ui, sans-serif; font-size: 9px; fill: #475569; font-style: italic; }',
        '.tl-card-warn { font-family: system-ui, sans-serif; font-size: 8.5px; font-weight: 700; fill: #b91c1c; }',
        '</style>',
        f'<rect width="{ancho}" height="{alto}" class="tl-bg"/>',
        # Eje cronológico principal
        f'<line x1="{margen_x}" y1="{y_eje}" x2="{ancho - margen_x}" y2="{y_eje}" class="tl-axis"/>',
    ]

    # Separador a. C. / d. C. en año 0
    x_cero = ano_a_x(0)
    svg.append(f'<line x1="{x_cero}" y1="25" x2="{x_cero}" y2="{alto - 25}" class="tl-era-divide"/>')
    # Etiquetas de era en la parte superior despejada
    svg.append(f'<text x="{x_cero - 12}" y="36" class="tl-era-badge" style="text-anchor:end;">a. C.</text>')
    svg.append(f'<text x="{x_cero + 12}" y="36" class="tl-era-badge" style="text-anchor:start;">d. C.</text>')

    # Marcas de siglos
    siglos = [
        (-600, 'VI a.C.'), (-500, 'V a.C.'), (-400, 'IV a.C.'), (-300, 'III a.C.'),
        (-200, 'II a.C.'), (-100, 'I a.C.'), (0, '0'), (100, 'I d.C.'),
        (200, 'II d.C.'), (300, 'III d.C.'), (400, 'IV d.C.'), (500, 'V d.C.'), (600, 'VI d.C.')
    ]
    for ano_siglo, texto_siglo in siglos:
        xs = ano_a_x(ano_siglo)
        svg.append(f'<line x1="{xs}" y1="{y_eje - 4}" x2="{xs}" y2="{y_eje + 4}" class="tl-century-tick"/>')
        svg.append(f'<text x="{xs}" y="{y_eje + 15}" class="tl-century-label">{texto_siglo}</text>')

    # Disposición anticolisión escalonada en 4 niveles de altura
    # Arriba: nivel 0 (Y = 55), nivel 1 (Y = 105)
    # Abajo:  nivel 0 (Y = 245), nivel 1 (Y = 295)
    alturas_arriba = [55, 105]
    alturas_abajo = [245, 295]

    ultimo_x_arriba = -999.0
    ultimo_nivel_arriba = 0
    ultimo_x_abajo = -999.0
    ultimo_nivel_abajo = 0

    for i, hito in enumerate(hitos):
        x_nodo = ano_a_x(hito['ano_numerico'])
        arriba = (i % 2 == 0)

        if arriba:
            if abs(x_nodo - ultimo_x_arriba) < 130:
                nivel = 1 - ultimo_nivel_arriba
            else:
                nivel = 0
            ultimo_x_arriba = x_nodo
            ultimo_nivel_arriba = nivel
            y_tarjeta = alturas_arriba[nivel]
            y_stem = y_tarjeta + 26
        else:
            if abs(x_nodo - ultimo_x_abajo) < 130:
                nivel = 1 - ultimo_nivel_abajo
            else:
                nivel = 0
            ultimo_x_abajo = x_nodo
            ultimo_nivel_abajo = nivel
            y_tarjeta = alturas_abajo[nivel]
            y_stem = y_tarjeta - 10

        # Línea de conexión al eje
        svg.append(f'<line x1="{x_nodo}" y1="{y_eje}" x2="{x_nodo}" y2="{y_stem}" class="tl-stem"/>')
        # Nodo en el eje
        svg.append(f'<circle cx="{x_nodo}" cy="{y_eje}" r="5.5" class="tl-node"/>')

        # Alineación del texto para no salirse de los márgenes
        anchor = 'middle'
        if x_nodo < margen_x + 50:
            anchor = 'start'
        elif x_nodo > ancho - margen_x - 50:
            anchor = 'end'

        aprox_mark = ' (aprox.)' if hito.get('aproximado') else ''
        autor_txt = hito['autor']
        if len(autor_txt) > 28:
            autor_txt = autor_txt.split()[0] + ' ' + autor_txt.split()[-1]

        svg.append(f'<text x="{x_nodo}" y="{y_tarjeta}" class="tl-card-author" style="text-anchor:{anchor};">{autor_txt}</text>')
        svg.append(f'<text x="{x_nodo}" y="{y_tarjeta + 12}" class="tl-card-date" style="text-anchor:{anchor};">{hito["epoca"]}{aprox_mark}</text>')

        # Advertencia en guía docente si no tiene fuente
        if hito.get('sin_fuente'):
            svg.append(f'<text x="{x_nodo}" y="{y_tarjeta + 23}" class="tl-card-warn" style="text-anchor:{anchor};">[sin fuente en la biblioteca]</text>')
        else:
            obra_corta = hito.get('obra', '')[:30]
            svg.append(f'<text x="{x_nodo}" y="{y_tarjeta + 23}" class="tl-card-work" style="text-anchor:{anchor};">{obra_corta}</text>')

    svg.append('</svg>')
    return '\n'.join(svg)


# ============================================================================
# 5. TETRACORDOS SVG (Tres géneros con afinación dual)
# ============================================================================

def generar_svg_tetracordos(ancho: int = 920, alto: int = 340) -> str:
    """Genera un SVG determinista de la partitura de los tres géneros de tetracordos
    (diatónico, cromático y enarmónico con cuarto de tono), con pentagramas limpios."""
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" class="didactic-svg didactic-tetracordos">',
        '<style>',
        '.tc-bg { fill: #fcfcfd; rx: 8px; }',
        '.tc-box { fill: #ffffff; stroke: #e2e8f0; stroke-width: 1.5; rx: 6px; }',
        '.tc-gen-title { font-family: system-ui, sans-serif; font-size: 13px; font-weight: 700; fill: #0f172a; }',
        '.tc-gen-sub { font-family: system-ui, sans-serif; font-size: 11px; fill: #64748b; }',
        '.tc-staff { stroke: #cbd5e1; stroke-width: 1; }',
        '.tc-bar { stroke: #475569; stroke-width: 2; }',
        '.tc-note { fill: #0f172a; cursor: pointer; transition: fill 0.15s; }',
        '.tc-note:hover { fill: #2563eb; }',
        '.tc-note-name { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 700; fill: #334155; text-anchor: middle; }',
        '.tc-acc { font-family: system-ui, sans-serif; font-size: 13px; font-weight: 700; fill: #b45309; text-anchor: middle; }',
        '.tc-quarter-acc { font-family: system-ui, sans-serif; font-size: 14px; font-weight: 700; fill: #dc2626; text-anchor: middle; }',
        '.tc-hz-label { font-family: system-ui, sans-serif; font-size: 10px; font-weight: 600; fill: #0284c7; text-anchor: middle; }',
        '.tc-badge { font-family: system-ui, sans-serif; font-size: 10px; font-weight: 600; fill: #0284c7; }',
        '</style>',
        f'<rect width="{ancho}" height="{alto}" class="tc-bg"/>',
    ]

    generos = [
        {
            'nombre': '1. Género Diatónico',
            'desc': 'Tono – Tono – Semitono (200 + 200 + 100 = 500 cents)',
            'notas': [
                {'nombre': 'Mi4', 'y_line': 1, 'freq_pit': '330.0 Hz', 'freq_temp': '329.6 Hz', 'acc': None},
                {'nombre': 'Re4', 'y_line': 2, 'freq_pit': '293.3 Hz', 'freq_temp': '293.7 Hz', 'acc': None},
                {'nombre': 'Do4', 'y_line': 3, 'freq_pit': '260.7 Hz', 'freq_temp': '261.6 Hz', 'acc': None},
                {'nombre': 'Si3', 'y_line': 4, 'freq_pit': '247.5 Hz', 'freq_temp': '246.9 Hz', 'acc': None},
            ]
        },
        {
            'nombre': '2. Género Cromático',
            'desc': 'Trihemitono – Semitono – Semitono (300 + 100 + 100 = 500 cents)',
            'notas': [
                {'nombre': 'Mi4', 'y_line': 1, 'freq_pit': '330.0 Hz', 'freq_temp': '329.6 Hz', 'acc': None},
                {'nombre': 'Do♯4', 'y_line': 3, 'freq_pit': '278.4 Hz', 'freq_temp': '277.2 Hz', 'acc': '♯'},
                {'nombre': 'Do♮4', 'y_line': 3, 'freq_pit': '260.7 Hz', 'freq_temp': '261.6 Hz', 'acc': '♮'},
                {'nombre': 'Si3', 'y_line': 4, 'freq_pit': '247.5 Hz', 'freq_temp': '246.9 Hz', 'acc': None},
            ]
        },
        {
            'nombre': '3. Género Enarmónico (cuartos de tono)',
            'desc': 'Ditono – Cuarto de tono – Cuarto de tono (400 + 50 + 50 = 500 cents)',
            'notas': [
                {'nombre': 'Mi4', 'y_line': 1, 'freq_pit': '330.0 Hz', 'freq_temp': '329.6 Hz', 'acc': None},
                {'nombre': 'Do♮4', 'y_line': 3, 'freq_pit': '260.7 Hz', 'freq_temp': '261.6 Hz', 'acc': '♮'},
                {'nombre': 'Si𝄲3', 'y_line': 4, 'freq_pit': '254.0 Hz', 'freq_temp': '254.2 Hz', 'acc': '𝄲'},
                {'nombre': 'Si3', 'y_line': 4, 'freq_pit': '247.5 Hz', 'freq_temp': '246.9 Hz', 'acc': None},
            ]
        },
    ]

    box_w = (ancho - 48 - 32) / 3
    for g_idx, gen in enumerate(generos):
        bx = 24 + g_idx * (box_w + 16)
        by = 28
        bh = alto - 48
        svg.append(f'<rect x="{bx}" y="{by}" width="{box_w}" height="{bh}" class="tc-box"/>')
        svg.append(f'<text x="{bx + 14}" y="{by + 24}" class="tc-gen-title">{gen["nombre"]}</text>')
        svg.append(f'<text x="{bx + 14}" y="{by + 40}" class="tc-gen-sub">{gen["desc"]}</text>')

        # Pentagrama (5 líneas)
        staff_base = by + 75
        line_step = 12
        for l in range(5):
            ly = staff_base + l * line_step
            svg.append(f'<line x1="{bx + 20}" y1="{ly}" x2="{bx + box_w - 20}" y2="{ly}" class="tc-staff"/>')

        # Barras divisorias en extremos
        svg.append(f'<line x1="{bx + 20}" y1="{staff_base}" x2="{bx + 20}" y2="{staff_base + 4 * line_step}" class="tc-bar"/>')
        svg.append(f'<line x1="{bx + box_w - 20}" y1="{staff_base}" x2="{bx + box_w - 20}" y2="{staff_base + 4 * line_step}" class="tc-bar"/>')

        n_space = (box_w - 80) / 3
        for n_idx, notita in enumerate(gen['notas']):
            nx = bx + 40 + n_idx * n_space
            ny = staff_base + notita['y_line'] * (line_step / 2) + 12

            # Cabeza de nota (sin plica)
            svg.append(f'<ellipse cx="{nx}" cy="{ny}" rx="6" ry="4.5" class="tc-note"/>')

            # Alteración
            if notita['acc']:
                is_quarter = '¼' in notita['acc']
                acc_class = 'tc-quarter-acc' if is_quarter else 'tc-acc'
                svg.append(f'<text x="{nx - 14}" y="{ny + 5}" class="{acc_class}">{notita["acc"]}</text>')

            # Nombre de la nota
            svg.append(f'<text x="{nx}" y="{by + 160}" class="tc-note-name">{notita["nombre"]}</text>')
            # Frecuencia (pitagórica por defecto)
            svg.append(
                f'<text x="{nx}" y="{by + 175}" class="tc-hz-label" '
                f'data-tc-gen="{g_idx}" data-tc-note="{n_idx}" '
                f'data-freq-pit="{notita["freq_pit"]}" data-freq-temp="{notita["freq_temp"]}">'
                f'{notita["freq_pit"]}</text>'
            )

        svg.append(f'<text x="{bx + 14}" y="{by + 205}" class="tc-badge">Web Audio: afinación pitagórica exacta</text>')

    svg.append('</svg>')
    return '\n'.join(svg)


# ============================================================================
# 6. DICCIONARIO INTEGRADO Y RESOLUCIÓN DE COMPONENTES
# ============================================================================

def resolver_componente_didactico(
    tipo: str,
    parametros: dict[str, Any] | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resuelve deterministamente un componente didáctico musical devolviendo sus
    datos estructurados, frecuencias sonoras y código SVG listo para renderizado.
    Separa lo calculado (teoría acústica) de lo factual (fuentes históricas)."""
    tipo = (tipo or '').strip().lower()
    parametros = parametros or {}

    if tipo in ('tetracordos', 'tetracordo'):
        from docente_ai.music.greek import asegurar_archivo_partitura_tres_generos
        archivo = asegurar_archivo_partitura_tres_generos()
        svg = generar_svg_tetracordos()
        return {
            'tipo': 'tetracordos',
            'titulo': 'Tetracordo descendente mi–si en los tres géneros',
            'archivo_partitura': archivo,
            'svg': svg,
            'afinados': {
                'pitagorica': {
                    'diatonico': [330.0, 293.33, 260.74, 247.5],
                    'cromatico': [330.0, 278.44, 260.74, 247.5],
                    'enarmonico': [330.0, 260.74, 254.04, 247.5],
                },
                'temperada': {
                    'diatonico': [329.63, 293.66, 261.63, 246.94],
                    'cromatico': [329.63, 277.18, 261.63, 246.94],
                    'enarmonico': [329.63, 261.63, 254.18, 246.94],
                },
            },
            'frecuencias_hz': [330.0, 293.33, 260.74, 247.5],  # Diatónico pitagórico por defecto
            'descripcion': 'Ilustración de la subdivisión del intervalo de cuarta en los géneros diatónico, cromático y enarmónico.',
            'calculado_teoria': True,
            'verificado': True,
        }

    elif tipo in ('gran_sistema_perfecto', 'gsp', 'sistema_perfecto'):
        svg = generar_svg_gran_sistema_perfecto()
        return {
            'tipo': 'gran_sistema_perfecto',
            'titulo': 'Gran Sistema Perfecto (Systema Teleion Meizon)',
            'subtitulo': SUBTITULO_GSP,
            'svg': svg,
            'notas': NOTAS_GRAN_SISTEMA_PERFECTO,
            'afinados': {
                'pitagorica': [n['freq_pitagorica'] for n in NOTAS_GRAN_SISTEMA_PERFECTO],
                'temperada': [n['freq_temperada'] for n in NOTAS_GRAN_SISTEMA_PERFECTO],
            },
            'frecuencias_hz': [n['freq_pitagorica'] for n in NOTAS_GRAN_SISTEMA_PERFECTO],
            'descripcion': SUBTITULO_GSP,
            'calculado_teoria': True,
            'verificado': True,
        }

    elif tipo in ('monocordio', 'monocordio_pitagorico', 'canon'):
        svg = generar_svg_monocordio()
        return {
            'tipo': 'monocordio',
            'titulo': 'Monocordio Pitagórico (Canon)',
            'svg': svg,
            'divisiones': [
                {
                    'fraccion': d.fraccion,
                    'intervalo_moderno': d.intervalo_moderno,
                    'nombre_proporcion': d.nombre_proporcion,
                    'proporcion': d.proporcion_frecuencia,
                    'freq_hz': d.freq_pitagorica,
                    'freq_pitagorica': d.freq_pitagorica,
                    'freq_temperada': d.freq_temperada,
                    'descripcion': d.descripcion,
                }
                for d in DIVISIONES_MONOCORDIO
            ],
            'afinados': {
                'pitagorica': [d.freq_pitagorica for d in DIVISIONES_MONOCORDIO],
                'temperada': [d.freq_temperada for d in DIVISIONES_MONOCORDIO],
            },
            'frecuencias_hz': [d.freq_pitagorica for d in DIVISIONES_MONOCORDIO],
            'descripcion': 'Cuerda dividida en proporciones 1/2 (octava, diplásion), 2/3 (quinta, hemiólion) y 3/4 (cuarta, epítriton).',
            'calculado_teoria': True,
            'verificado': True,
        }

    elif tipo in ('escalera_intervalos', 'escalera', 'cents'):
        svg = generar_svg_escalera_intervalos()
        return {
            'tipo': 'escalera_intervalos',
            'titulo': 'Escalera de Intervalos en Cents',
            'svg': svg,
            'descripcion': 'Comparativa de las dimensiones interválicas en cents de los tres géneros.',
            'calculado_teoria': True,
            'verificado': True,
        }

    elif tipo in ('linea_temporal', 'cronologia', 'timeline'):
        autores = parametros.get('autores')
        hitos = construir_hitos_linea_temporal(evidence, autores)
        svg_docente = generar_svg_linea_temporal(hitos, para_alumnado=False)
        svg_alumnado = generar_svg_linea_temporal(hitos, para_alumnado=True)
        return {
            'tipo': 'linea_temporal',
            'titulo': 'Línea Temporal de Tratadistas de la Música Griega',
            'svg': svg_docente,
            'svg_alumnado': svg_alumnado,
            'hitos': hitos,
            'descripcion': 'Eje cronológico real de siglos (a. C. / d. C.) construido a partir de los autores y fuentes de la propuesta.',
            'calculado_teoria': False,  # Contenido factual histórico, no calculado por proporciones
            'verificado': True,
        }

    raise ValueError(
        f"Tipo de componente didáctico no soportado: '{tipo}'. "
        f"Tipos válidos: tetracordos, gran_sistema_perfecto, monocordio, escalera_intervalos, linea_temporal."
    )


def cargar_reglas_componentes_por_tema(config_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Carga las reglas deterministas para asociar temas con componentes didácticos."""
    candidatos = []
    if config_path:
        candidatos.append(Path(config_path))
    candidatos.append(Path("config/componentes_por_tema.yaml"))
    candidatos.append(Path("config/componentes_por_tema.example.yaml"))
    for p in candidatos:
        if p.is_file():
            try:
                data = yaml.safe_load(p.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "reglas" in data:
                    return data["reglas"]
            except Exception:
                continue
    return []


def seleccionar_componentes_por_tema(
    texto: str,
    config_path: Path | str | None = None
) -> list[dict[str, Any]]:
    """Evalúa el texto libre (tema, plan, claims) frente a las reglas deterministas
    y devuelve los componentes didácticos sugeridos por regla temática."""
    reglas = cargar_reglas_componentes_por_tema(config_path)
    if not reglas or not texto:
        return []

    texto_lower = str(texto).lower()
    componentes: list[dict[str, Any]] = []
    tipos_vistos: set[str] = set()

    for regla in reglas:
        patron = regla.get("patron", "")
        if patron and re.search(patron, texto_lower, re.IGNORECASE):
            for c in regla.get("componentes", []):
                tipo = c.get("tipo")
                if tipo and tipo not in tipos_vistos:
                    tipos_vistos.add(tipo)
                    componentes.append({
                        "tipo": tipo,
                        "parametros": c.get("parametros") or {},
                        "origen": "regla_tema",
                    })
    return componentes
