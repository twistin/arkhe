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


# ----------------------------------------------------------------------------
# 3.1 ESCALERA DE INTERVALOS PERSONALIZADA (Afinación Justa o Pitagórica)
# ----------------------------------------------------------------------------

MAPA_INTERVALOS_CANONICOS = {
    'unisono': {
        'nombre': 'Unísono',
        'razon_justa': '1/1', 'cents_justa': 0.0,
        'razon_pit': '1/1', 'cents_pit': 0.0,
        'color': '#0284c7',
    },
    'segunda_menor': {
        'nombre': 'Segunda menor',
        'razon_justa': '16/15', 'cents_justa': 111.73,
        'razon_pit': '256/243', 'cents_pit': 90.22,
        'color': '#0ea5e9',
    },
    'segunda_mayor': {
        'nombre': 'Segunda mayor (tono)',
        'razon_justa': '9/8', 'cents_justa': 203.91,
        'razon_pit': '9/8', 'cents_pit': 203.91,
        'color': '#06b6d4',
    },
    'tercera_menor': {
        'nombre': 'Tercera menor',
        'razon_justa': '6/5', 'cents_justa': 315.64,
        'razon_pit': '32/27', 'cents_pit': 294.13,
        'color': '#10b981',
    },
    'tercera_mayor': {
        'nombre': 'Tercera mayor',
        'razon_justa': '5/4', 'cents_justa': 386.31,
        'razon_pit': '81/64', 'cents_pit': 407.82,
        'color': '#059669',
    },
    'cuarta_justa': {
        'nombre': 'Cuarta justa',
        'razon_justa': '4/3', 'cents_justa': 498.04,
        'razon_pit': '4/3', 'cents_pit': 498.04,
        'color': '#16a34a',
    },
    'tritono': {
        'nombre': 'Tritono (4ª aum / 5ª dism)',
        'razon_justa': '45/32', 'cents_justa': 590.22,
        'razon_pit': '729/512', 'cents_pit': 611.73,
        'color': '#eab308',
    },
    'quinta_justa': {
        'nombre': 'Quinta justa',
        'razon_justa': '3/2', 'cents_justa': 701.96,
        'razon_pit': '3/2', 'cents_pit': 701.96,
        'color': '#f59e0b',
    },
    'sexta_menor': {
        'nombre': 'Sexta menor',
        'razon_justa': '8/5', 'cents_justa': 813.69,
        'razon_pit': '128/81', 'cents_pit': 792.18,
        'color': '#f97316',
    },
    'sexta_mayor': {
        'nombre': 'Sexta mayor',
        'razon_justa': '5/3', 'cents_justa': 884.36,
        'razon_pit': '27/16', 'cents_pit': 905.87,
        'color': '#ea580c',
    },
    'septima_menor': {
        'nombre': 'Séptima menor',
        'razon_justa': '9/5', 'cents_justa': 1017.60,
        'razon_pit': '16/9', 'cents_pit': 996.09,
        'color': '#8b5cf6',
    },
    'septima_mayor': {
        'nombre': 'Séptima mayor',
        'razon_justa': '15/8', 'cents_justa': 1088.27,
        'razon_pit': '243/128', 'cents_pit': 1109.78,
        'color': '#7c3aed',
    },
    'octava': {
        'nombre': 'Octava justa',
        'razon_justa': '2/1', 'cents_justa': 1200.0,
        'razon_pit': '2/1', 'cents_pit': 1200.0,
        'color': '#6366f1',
    },
}


def normalizar_nombre_intervalo(texto: str) -> str | None:
    """Mapea un nombre o designación informal de intervalo al identificador canónico."""
    import unicodedata
    if texto in MAPA_INTERVALOS_CANONICOS:
        return texto
    s = unicodedata.normalize('NFD', str(texto).lower().strip())
    t = ''.join(c for c in s if unicodedata.category(c) != 'Mn').replace('_', ' ').strip()
    if t.replace(' ', '_') in MAPA_INTERVALOS_CANONICOS:
        return t.replace(' ', '_')

    if t in ('unisono', 'unison', '1', '1j'):
        return 'unisono'
    if t in ('octava', 'octava justa', '8', '8j'):
        return 'octava'
    if t in ('quinta justa', 'quinta', '5', '5j'):
        return 'quinta_justa'
    if t in ('cuarta justa', 'cuarta', '4', '4j'):
        return 'cuarta_justa'
    if 'tritono' in t or 'aumentada' in t or 'disminuida' in t:
        return 'tritono'
    if 'tercera' in t or t in ('3', '3m', '3m'):
        if 'menor' in t or t == '3m':
            return 'tercera_menor'
        return 'tercera_mayor'
    if 'segunda' in t or t in ('2', '2m', '2m'):
        if 'menor' in t or t == '2m' or 'semitono' in t:
            return 'segunda_menor'
        return 'segunda_mayor'
    if 'sexta' in t or t in ('6', '6m', '6m'):
        if 'menor' in t or t == '6m':
            return 'sexta_menor'
        return 'sexta_mayor'
    if 'septima' in t or t in ('7', '7m', '7m'):
        if 'menor' in t or t == '7m':
            return 'septima_menor'
        return 'septima_mayor'
    return None


def generar_svg_escalera_intervalos_personalizada(
    intervalos: list[dict[str, Any]],
    afinacion: str = 'justa',
    ancho: int = 920,
) -> str:
    """Genera un SVG determinista comparando a escala en cents los intervalos solicitados."""
    margen_izq = 180
    margen_der = 60
    ancho_escala = ancho - margen_izq - margen_der
    max_cents = 1200.0
    px_por_cent = ancho_escala / max_cents
    alto = max(240, 90 + len(intervalos) * 44 + 40)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" class="didactic-svg didactic-ladder">',
        '<style>',
        '.ld-bg { fill: #fcfcfd; rx: 8px; }',
        '.ld-rule { stroke: #cbd5e1; stroke-width: 1; }',
        '.ld-rule-label { font-family: system-ui, sans-serif; font-size: 10px; fill: #64748b; text-anchor: middle; }',
        '.ld-inter-title { font-family: system-ui, sans-serif; font-size: 12px; font-weight: 700; fill: #0f172a; text-anchor: end; }',
        '.ld-bar-text { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 700; fill: #ffffff; text-anchor: middle; }',
        '.ld-bar-outside { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 700; fill: #1e293b; text-anchor: start; }',
        '.ld-sub { font-family: system-ui, sans-serif; font-size: 11px; fill: #475569; }',
        '</style>',
        f'<rect width="{ancho}" height="{alto}" class="ld-bg"/>',
    ]

    y_regla = 48
    svg.append(f'<line x1="{margen_izq}" y1="{y_regla}" x2="{margen_izq + ancho_escala}" y2="{y_regla}" class="ld-rule"/>')
    for c in range(0, 1201, 200):
        xc = margen_izq + c * px_por_cent
        svg.append(f'<line x1="{xc}" y1="{y_regla - 5}" x2="{xc}" y2="{y_regla + 5}" class="ld-rule"/>')
        svg.append(f'<text x="{xc}" y="{y_regla - 8}" class="ld-rule-label">{c}c</text>')

    y_base = 75
    altura_fila = 42

    for idx, inter in enumerate(intervalos):
        y_fila = y_base + idx * altura_fila
        nombre = inter.get('nombre', '')
        razon = inter.get('razon_str', '1/1')
        cents = float(inter.get('cents', 0.0))
        color = inter.get('color', '#0284c7')

        svg.append(f'<text x="{margen_izq - 15}" y="{y_fila + 20}" class="ld-inter-title">{nombre}</text>')

        w_bar = max(3.0, cents * px_por_cent)
        svg.append(
            f'<rect x="{margen_izq}" y="{y_fila}" width="{w_bar}" height="28" '
            f'fill="{color}" rx="3" style="stroke:#ffffff; stroke-width:1.5;"/>'
        )
        label_txt = f"{razon} ({int(round(cents))}c)"
        if w_bar >= 90:
            svg.append(f'<text x="{margen_izq + w_bar/2}" y="{y_fila + 18}" class="ld-bar-text">{label_txt}</text>')
        else:
            svg.append(f'<text x="{margen_izq + w_bar + 8}" y="{y_fila + 18}" class="ld-bar-outside">{label_txt}</text>')

    tipo_af = "justa (zarliniana)" if afinacion.lower() == 'justa' else "pitagórica"
    svg.append(
        f'<text x="{ancho // 2}" y="{alto - 14}" class="ld-sub" style="text-anchor: middle;">'
        f'Afinación {tipo_af}: intervalos representados a escala exacta en cents sobre la octava (0–1200c).'
        '</text>'
    )
    svg.append('</svg>')
    return '\n'.join(svg)


# ----------------------------------------------------------------------------
# 3.2 ÁMBITOS HISTÓRICO-TEMÁTICOS POR COMPONENTE DIDÁCTICO
# ----------------------------------------------------------------------------

AMBITOS_COMPONENTES_DEFAULT = {
    'tetracordos': {
        'periodos': ('antiguedad', 'antigüedad', 'grecia', 'grecia antigua', 'edad media', 'medieval', 'teoria medieval'),
        'materias': ('historia-i', 'historia_1', 'historia_de_la_musica_1', 'fundamentos'),
    },
    'gran_sistema_perfecto': {
        'periodos': ('antiguedad', 'antigüedad', 'grecia', 'grecia antigua', 'edad media', 'medieval', 'teoria medieval'),
        'materias': ('historia-i', 'historia_1', 'historia_de_la_musica_1', 'fundamentos'),
    },
    'monocordio': {
        'periodos': ('antiguedad', 'antigüedad', 'grecia', 'grecia antigua', 'edad media', 'medieval', 'teoria medieval'),
        'materias': ('historia-i', 'historia_1', 'historia_de_la_musica_1', 'fundamentos', 'acustica', 'organologia'),
    },
}


def cargar_ambitos_componentes() -> dict[str, Any]:
    """Carga los ámbitos por componente declarados en config/componentes_por_tema.yaml o example."""
    import yaml
    root = Path(__file__).resolve().parents[3]
    for filename in ('config/componentes_por_tema.yaml', 'config/componentes_por_tema.example.yaml'):
        candidate = root / filename
        if candidate.is_file():
            try:
                data = yaml.safe_load(candidate.read_text(encoding='utf-8'))
                if isinstance(data, dict) and 'ambitos_componentes' in data:
                    return data['ambitos_componentes']
            except Exception:
                pass
    return AMBITOS_COMPONENTES_DEFAULT


def comprobar_ambito_componente(
    tipo: str,
    topic: str | None = None,
    subject: str | None = None,
    periodo: str | None = None,
    parametros: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    """Comprueba si un componente está dentro de su ámbito temático y temporal.
    Tetracordos, gran sistema perfecto y monocordio pertenecen exclusivamente
    a la Antigüedad griega y teoría medieval. Fuera de su ámbito no se instancian.
    escalera_intervalos y linea_temporal son transversales (validan sus parámetros).
    """
    tipo_norm = str(tipo or '').lower().strip()
    if tipo_norm in ('gsp', 'sistema_perfecto'):
        tipo_norm = 'gran_sistema_perfecto'
    elif tipo_norm in ('monocordio_pitagorico', 'canon'):
        tipo_norm = 'monocordio'
    elif tipo_norm in ('tetracordo',):
        tipo_norm = 'tetracordos'

    # Solo tetracordos, gran_sistema_perfecto y monocordio tienen restricción de ámbito histórico
    if tipo_norm not in ('tetracordos', 'gran_sistema_perfecto', 'monocordio'):
        return True, None

    # Textos indicativos de materia, tema y periodo
    textos = [
        str(topic or ''),
        str(subject or ''),
        str(periodo or ''),
        str((parametros or {}).get('periodo', '')),
        str((parametros or {}).get('tema', '')),
    ]
    texto_combinado = ' '.join(textos).lower().strip()

    # Si no hay ningún contexto temático ni temporal especificado (llamada aislada de test/teoría), permitir
    if not texto_combinado:
        return True, None

    # 1. Descarte inmediato si se detecta cualquier periodo o estilo posterior
    periodos_posteriores = (
        'siglo xvi', 's. xvi', 'siglo 16', '16th century', 'renacimiento', 'renacentista',
        'siglo xv', 's. xv', 'siglo 15', '15th century',
        'siglo xvii', 's. xvii', 'siglo 17', 'barroco', 'barroca',
        'siglo xviii', 's. xviii', 'siglo 18', 'clasicismo', 'clasico', 'clásico',
        'siglo xix', 's. xix', 'siglo 19', 'romanticismo', 'romantico', 'romántico',
        'siglo xx', 's. xx', 'siglo 20', 'siglo xxi', 's. xxi', 'siglo 21',
        'contemporan', 'contemporaneo', 'contemporáneo', 'contemporánea', 'ntam',
        'nuevas tecnologias', 'nuevas tecnologías', 'cine', 'jazz', 'pop', 'rock',
        'polifonia', 'polifonía', 'misa', 'madrigal', 'chanson', 'motete'
    )
    for p_post in periodos_posteriores:
        if re.search(r'\b' + re.escape(p_post) + r'\b', texto_combinado):
            return False, (
                f"El componente '{tipo_norm}' pertenece exclusivamente al ámbito de Antigüedad y Teoría Medieval; "
                f"no es aplicable a un contexto de {p_post}."
            )

    # 2. Validación por lista blanca afirmativa:
    # Debe pertenecer explícitamente a la Antigüedad griega o Teoría Medieval
    terminos_autorizados = (
        'antiguedad', 'antigüedad', 'antiguo', 'antigua',
        'grecia', 'griego', 'griega', 'helenic', 'helenístic',
        'seikilos', 'epitafio', 'pitagoras', 'pitágoras', 'pitagorico', 'pitagórico',
        'platon', 'platón', 'aristoteles', 'aristóteles', 'aristoxeno', 'aristóxeno',
        'ptolomeo', 'monocordio', 'sistema perfecto', 'tetracordo', 'tetracordos',
        'edad media', 'medieval', 'teoria medieval', 'teoría medieval',
        'boecio', 'guido', 'hucbaldo', 'modos eclesiasticos', 'modos eclesiásticos',
        'canto gregoriano', 'historia-i', 'historia_i', 'historia-1', 'historia 1'
    )
    es_autorizado = any(
        re.search(r'\b' + re.escape(t) + r'\b', texto_combinado)
        for t in terminos_autorizados
    )

    if not es_autorizado:
        return False, (
            f"El componente '{tipo_norm}' pertenece exclusivamente al ámbito de Antigüedad griega y Teoría Medieval; "
            f"no es aplicable a '{topic or periodo or subject or 'tema no especificado'}'."
        )

    return True, None


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
        'obra_canon': 'La República y Timeo',
    },
    'aristoteles': {
        'nombre_canonico': 'Aristóteles',
        'epoca': 'c. 384–322 a. C.',
        'ano_numerico': -350,
        'aproximado': True,
        'obra_canon': 'Política y Problemata',
    },
    'aristoxeno': {
        'nombre_canonico': 'Aristóxeno de Tarento',
        'epoca': 'fl. c. 330 a. C.',
        'ano_numerico': -330,
        'aproximado': True,
        'obra_canon': 'Elementos de armonía (Harmonika Stoicheia)',
    },
    'euclides': {
        'nombre_canonico': 'Euclides / Pseudo-Euclides',
        'epoca': 'fl. c. 300 a. C.',
        'ano_numerico': -300,
        'aproximado': True,
        'obra_canon': 'División del canon (Katatome kanonos)',
    },
    'nicomaco': {
        'nombre_canonico': 'Nicómaco de Gerasa',
        'epoca': 'fl. c. 100 d. C.',
        'ano_numerico': 100,
        'aproximado': True,
        'obra_canon': 'Manual de armónica (Harmonikon encheiridion)',
    },
    'ptolomeo': {
        'nombre_canonico': 'Claudio Ptolomeo',
        'epoca': 'fl. c. 150 d. C.',
        'ano_numerico': 150,
        'aproximado': True,
        'obra_canon': 'Harmónicos (Harmonika)',
    },
    'aristides_quintiliano': {
        'nombre_canonico': 'Arístides Quintiliano',
        'epoca': 'fl. c. 300 d. C.',
        'ano_numerico': 300,
        'aproximado': True,
        'obra_canon': 'Sobre la música (Peri mousikes)',
    },
    'alipio': {
        'nombre_canonico': 'Alipio de Alejandría',
        'epoca': 'fl. c. 360 d. C.',
        'ano_numerico': 360,
        'aproximado': True,
        'obra_canon': 'Introducción a la música (Tablas notacionales)',
    },
    'san_ambrosio': {
        'nombre_canonico': 'San Ambrosio de Milán',
        'epoca': 'c. 340–397 d. C.',
        'ano_numerico': 374,
        'aproximado': True,
        'obra_canon': 'Himnodia litúrgica y canto antifonal',
    },
    'san_agustin': {
        'nombre_canonico': 'San Agustín de Hipona',
        'epoca': 'c. 354–430 d. C.',
        'ano_numerico': 390,
        'aproximado': True,
        'obra_canon': 'De Musica (seis libros sobre ritmo)',
    },
    'boecio': {
        'nombre_canonico': 'Anicio Manlio Torcuato Severino Boecio',
        'epoca': 'c. 480–524 d. C.',
        'ano_numerico': 505,
        'aproximado': True,
        'obra_canon': 'De institutione musica (Quadrivium)',
    },
    'casiodoro': {
        'nombre_canonico': 'Flavio Magno Aurelio Casiodoro',
        'epoca': 'c. 485–585 d. C.',
        'ano_numerico': 540,
        'aproximado': True,
        'obra_canon': 'Institutiones divinarum et saecularium litterarum',
    },
}

PATRONES_AUTORES = {
    'pitagoras': re.compile(r'\bpit[aá]gor', re.IGNORECASE),
    'platon': re.compile(r'\bplat[oó]n', re.IGNORECASE),
    'aristoteles': re.compile(r'\barist[oó]tel', re.IGNORECASE),
    'aristoxeno': re.compile(r'\barist[oó]xen', re.IGNORECASE),
    'euclides': re.compile(r'\beuclid', re.IGNORECASE),
    'nicomaco': re.compile(r'\bnic[oó]mac', re.IGNORECASE),
    'ptolomeo': re.compile(r'\bptolom|\btolom', re.IGNORECASE),
    'aristides_quintiliano': re.compile(r'\bar[ií]stides\s+quintilian|\bquintilian', re.IGNORECASE),
    'alipio': re.compile(r'\balipi', re.IGNORECASE),
    'san_ambrosio': re.compile(r'\bambrosio\b', re.IGNORECASE),
    'san_agustin': re.compile(r'\bagust[ií]n\b', re.IGNORECASE),
    'boecio': re.compile(r'\bboec|\bboeth', re.IGNORECASE),
    'casiodoro': re.compile(r'\bcasiodor', re.IGNORECASE),
}


def envolver_texto(texto: str, max_chars: int = 24) -> list[str]:
    """Divide un texto en líneas respetando palabras para evitar que desborde de las tarjetas."""
    if not texto:
        return []
    palabras = str(texto).split()
    lineas = []
    actual: list[str] = []
    long_actual = 0
    for p in palabras:
        if long_actual + len(p) + (1 if actual else 0) <= max_chars:
            actual.append(p)
            long_actual += len(p) + (1 if len(actual) > 1 else 0)
        else:
            if actual:
                lineas.append(' '.join(actual))
            actual = [p]
            long_actual = len(p)
    if actual:
        lineas.append(' '.join(actual))
    return lineas


def formatear_fuente_corta(autor: str, titulo: str, max_chars_titulo: int = 28) -> str:
    """Formatea la fuente bibliográfica como 'Autor, título corto' sin truncar a mitad de palabra."""
    autor_str = autor.split(',')[0].strip() if autor else ''
    titulo_str = titulo.strip() if titulo else ''
    if not titulo_str and not autor_str:
        return 'Fuente autorizada'
    if not autor_str:
        autor_str = 'Fuente'

    if len(titulo_str) > max_chars_titulo:
        corte = titulo_str[:max_chars_titulo]
        if ' ' in corte:
            corte = corte.rsplit(' ', 1)[0]
        titulo_corto = corte.rstrip('.,;:- ')
    else:
        titulo_corto = titulo_str

    if autor_str and titulo_corto:
        return f"{autor_str}, {titulo_corto}"
    return autor_str or titulo_corto


def construir_hitos_linea_temporal(
    evidence: list[dict[str, Any]] | None = None,
    autores_solicitados: list[str] | None = None,
    claims: list[dict[str, Any]] | None = None,
    visualizaciones: list[dict[str, Any]] | None = None,
    inicio: int | None = None,
    fin: int | None = None,
    hitos_modelo: list[dict[str, Any]] | None = None,
    topic: str | None = None,
    subject: str | None = None,
) -> list[dict[str, Any]]:
    """Construye dinámicamente los hitos de la línea temporal a partir de las fuentes
    citadas de la propuesta, de los hitos propuestos por el modelo y de los autores en claims/fuentes.
    Solo entran personas (tratadistas). Obras y fuentes (Epitafio de Seikilos) no van a la línea.
    Respeta el rango cronológico [inicio, fin] si se especifica: los autores fuera de rango se descartan.
    cronologia_autores.yaml solo aporta fechas de autores que ya estén en la propuesta y en el rango."""
    from docente_ai.teaching.fichas import get_ficha, is_ficha_verified

    ficha_cron = get_ficha('cronologia_autores')
    cron_verificada = is_ficha_verified(ficha_cron)
    mapa_ficha: dict[str, dict[str, Any]] = {}
    if ficha_cron and isinstance(ficha_cron.get('autores'), list):
        for a in ficha_cron['autores']:
            if isinstance(a, dict) and 'id' in a:
                mapa_ficha[a['id']] = a

    hitos: list[dict[str, Any]] = []
    autores_en_fuentes: dict[str, dict[str, Any]] = {}

    def _esta_en_rango(ano: int) -> bool:
        if inicio is not None and ano < inicio:
            return False
        if fin is not None and ano > fin:
            return False
        return True

    def _normalizar(s: str) -> str:
        res = s.lower()
        for orig, dest in (('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ü', 'u')):
            res = res.replace(orig, dest)
        return res

    def _detectar_key(texto: str) -> str | None:
        t_norm = _normalizar(texto)
        if 'seikil' in t_norm or 'epitaf' in t_norm:
            return None  # Solo personas; las obras y estelas no van a la línea de tratadistas
        if 'quintilian' in t_norm: return 'aristides_quintiliano'
        if 'ambrosio' in t_norm: return 'san_ambrosio'
        if 'casiodor' in t_norm: return 'casiodoro'
        if 'plat' in t_norm: return 'platon'
        if 'aristot' in t_norm: return 'aristoteles'
        if 'aristox' in t_norm: return 'aristoxeno'
        if 'pitag' in t_norm: return 'pitagoras'
        if 'nicom' in t_norm: return 'nicomaco'
        if 'ptol' in t_norm or 'tolom' in t_norm: return 'ptolomeo'
        if 'euclid' in t_norm: return 'euclides'
        if 'alipi' in t_norm: return 'alipio'
        if 'agust' in t_norm: return 'san_agustin'
        if 'boec' in t_norm or 'boeth' in t_norm: return 'boecio'
        return None

    # 1. Hitos proporcionados explícitamente por el modelo
    if hitos_modelo:
        for hm in hitos_modelo:
            if not isinstance(hm, dict):
                continue
            autor_hm = hm.get('autor') or hm.get('nombre') or hm.get('titulo') or ''
            if not autor_hm:
                continue
            ano_val = hm.get('ano_numerico')
            if ano_val is None:
                ano_val = hm.get('ano') or hm.get('year') or hm.get('fecha')
            try:
                ano_num = int(str(ano_val).replace('c.', '').replace('fl.', '').replace('d. C.', '').replace('a. C.', '').strip())
            except Exception:
                ano_num = inicio or 0

            if _esta_en_rango(ano_num):
                hitos.append({
                    'key': f"mod_{_normalizar(autor_hm)[:12]}",
                    'autor': autor_hm,
                    'epoca': hm.get('epoca') or hm.get('fecha') or f"c. {ano_num}",
                    'ano_numerico': ano_num,
                    'aproximado': True,
                    'obra': hm.get('obra') or '',
                    'fuente': hm.get('fuente') or 'Propuesta curricular',
                    'sin_fuente': False,
                    'cronologia_verificada': True,
                    'fecha_documentada': True,
                })

    # 2. Extraer autores y obras de las fuentes y pasajes citados
    for ev in (evidence or []):
        meta = ev.get('metadata') or {}
        autor_doc = (meta.get('authors') or [''])[0] or ev.get('source_author') or ''
        titulo_doc = meta.get('title') or ev.get('source_title') or ''
        fuente_corta = formatear_fuente_corta(autor_doc, titulo_doc, max_chars_titulo=26)

        texto_ev = (ev.get('text') or '') + ' ' + ' '.join(str(p) for p in (ev.get('passages') or []))
        todo_texto = f"{autor_doc} {titulo_doc} {texto_ev}"

        for key, pat in PATRONES_AUTORES.items():
            if pat.search(todo_texto):
                canon = FIGURAS_HISTORICAS_GRIEGAS[key]
                ficha_item = mapa_ficha.get(key) or {}
                epoca_str = ficha_item.get('fecha_display') or canon['epoca']
                ano_num = ficha_item.get('ano_numerico', canon['ano_numerico'])
                obra_str = ficha_item.get('obra_canon') or canon['obra_canon']

                if _esta_en_rango(ano_num) and key not in autores_en_fuentes:
                    autores_en_fuentes[key] = {
                        'key': key,
                        'autor': canon['nombre_canonico'],
                        'epoca': epoca_str,
                        'ano_numerico': ano_num,
                        'aproximado': canon.get('aproximado', True),
                        'obra': obra_str,
                        'fuente': fuente_corta,
                        'sin_fuente': False,
                        'cronologia_verificada': cron_verificada,
                        'fecha_documentada': cron_verificada,
                    }

    for item in autores_en_fuentes.values():
        if not any(h['autor'] == item['autor'] for h in hitos):
            hitos.append(item)

    # 3. Extraer autores nombrados en claims y visualizaciones
    autores_mencionados: set[str] = set()
    for cl in (claims or []):
        t = cl.get('text', '') + ' ' + cl.get('student_summary', '')
        for k in FIGURAS_HISTORICAS_GRIEGAS:
            if k in _normalizar(t):
                autores_mencionados.add(k)
    for vz in (visualizaciones or []):
        t = vz.get('title', '') + ' ' + vz.get('caption', '')
        for it in (vz.get('items') or []):
            t += ' ' + str(it.get('label', '')) + ' ' + str(it.get('detail', ''))
        for k in FIGURAS_HISTORICAS_GRIEGAS:
            if k in _normalizar(t):
                autores_mencionados.add(k)

    # 4. Autores solicitados explícitamente en parámetros o mencionados en tema/asignatura
    for aut_sol in (autores_solicitados or []):
        key = _detectar_key(str(aut_sol))
        if key:
            autores_mencionados.add(key)

    texto_tema = f"{topic or ''} {subject or ''}"
    if texto_tema.strip():
        for k in FIGURAS_HISTORICAS_GRIEGAS:
            if k in _normalizar(texto_tema):
                autores_mencionados.add(k)

    for key in autores_mencionados:
        if key not in autores_en_fuentes and key in FIGURAS_HISTORICAS_GRIEGAS:
            canon = FIGURAS_HISTORICAS_GRIEGAS[key]
            ficha_item = mapa_ficha.get(key) or {}
            epoca_str = ficha_item.get('fecha_display') or canon['epoca']
            ano_num = ficha_item.get('ano_numerico', canon['ano_numerico'])
            obra_str = ficha_item.get('obra_canon') or canon['obra_canon']
            if _esta_en_rango(ano_num) and not any(h.get('key') == key for h in hitos):
                hitos.append({
                    'key': key,
                    'autor': canon['nombre_canonico'],
                    'epoca': epoca_str,
                    'ano_numerico': ano_num,
                    'aproximado': canon.get('aproximado', True),
                    'obra': obra_str,
                    'fuente': 'sin fuente en la biblioteca',
                    'sin_fuente': True,
                    'cronologia_verificada': cron_verificada,
                    'fecha_documentada': False,
                })

    # En llamadas unitarias abstractas o en temas de la Grecia Antigua sin autores explícitos, aportar figuras canónicas griegas.
    # Fuera de la Antigüedad griega, si no hay autores citados ni hitos, la línea temporal se descarta.
    if not hitos and inicio is None and fin is None and not hitos_modelo:
        es_tema_griego = any(w in _normalizar(f"{topic or ''} {subject or ''}") for w in ('grecia', 'griego', 'griega', 'antiguedad', 'seikilos', 'pitagoras'))
        es_llamada_unitaria = not autores_solicitados and not claims and not evidence and not topic and not subject
        if es_llamada_unitaria or es_tema_griego:
            for k in ('pitagoras', 'platon', 'aristoteles', 'aristoxeno', 'euclides', 'nicomaco', 'ptolomeo', 'san_agustin', 'boecio'):
                canon = FIGURAS_HISTORICAS_GRIEGAS[k]
                ficha_item = mapa_ficha.get(k) or {}
                hitos.append({
                    'key': k,
                    'autor': canon['nombre_canonico'],
                    'epoca': ficha_item.get('fecha_display') or canon['epoca'],
                    'ano_numerico': ficha_item.get('ano_numerico', canon['ano_numerico']),
                    'aproximado': canon.get('aproximado', True),
                    'obra': ficha_item.get('obra_canon') or canon['obra_canon'],
                    'fuente': 'Referencia histórica',
                    'sin_fuente': False,
                    'cronologia_verificada': cron_verificada,
                    'fecha_documentada': cron_verificada,
                })

    # Ordenar estrictamente por año cronológico
    hitos.sort(key=lambda h: h['ano_numerico'])
    return hitos


def generar_svg_linea_temporal(
    hitos: list[dict[str, Any]] | None = None,
    para_alumnado: bool = False,
    ancho: int = 980,
    alto: int = 420,
    ano_min: int | None = None,
    ano_max: int | None = None,
) -> str:
    """Genera un SVG determinista de la línea temporal:
    - Si cronologia_autores está verificada: eje cronológico real con fechas.
    - Si NO está verificada: el alumnado ve la línea temporal sin fechas (solo orden relativo histórico)
      y la guía docente ve el aviso destacado.
    - Tarjetas con ajuste automático de línea y alto para que no corten texto.
    - Soporta rangos arbitrarios (ej. 1500–1600) respetando ano_min y ano_max."""
    hitos = hitos or construir_hitos_linea_temporal()

    if para_alumnado:
        hitos = [h for h in hitos if not h.get('sin_fuente')]

    cron_verificada = any(h.get('cronologia_verificada') for h in hitos)
    n = len(hitos)
    if n == 0:
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} 100"><text x="20" y="50">Sin tratadistas disponibles en el rango solicitado</text></svg>'

    margen_x = 40
    ancho_util = ancho - 2 * margen_x

    # Caso 1: Para el alumnado y cronología no verificada -> Secuencia histórica sin fechas numéricas
    if para_alumnado and not cron_verificada:
        usar_grid = (n > 4)
        alto_calc = 390 if usar_grid else 280
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto_calc}" class="didactic-svg didactic-timeline-seq">',
            '<style>',
            '.tl-bg { fill: #f8fafc; rx: 8px; }',
            '.tl-title { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 700; fill: #475569; letter-spacing: 0.5px; }',
            '.tl-card-box { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.2; rx: 6px; }',
            '.tl-badge-ord { font-family: system-ui, sans-serif; font-size: 10px; font-weight: 800; fill: #0284c7; }',
            '.tl-card-name { font-family: system-ui, sans-serif; font-size: 11.5px; font-weight: 700; fill: #0f172a; }',
            '.tl-card-work { font-family: system-ui, sans-serif; font-size: 9.5px; font-style: italic; fill: #475569; }',
            '.tl-card-src { font-family: system-ui, sans-serif; font-size: 9px; font-weight: 600; fill: #64748b; }',
            '.tl-guide-line { stroke: #0284c7; stroke-width: 2; stroke-dasharray: 4,4; }',
            '.tl-ord-circle { fill: #0284c7; stroke: #ffffff; stroke-width: 2; }',
            '.tl-ord-num { font-family: system-ui, sans-serif; font-size: 11px; font-weight: 800; fill: #ffffff; text-anchor: middle; dominant-baseline: central; }',
            '</style>',
            f'<rect width="{ancho}" height="{alto_calc}" class="tl-bg"/>',
            f'<text x="{margen_x + 10}" y="26" class="tl-title">SECUENCIA HISTÓRICA DE TRATADISTAS Y FIGURAS HISTÓRICAS (ORDEN RELATIVO)</text>',
        ]

        if not usar_grid:
            espacio_x = ancho_util / n
            y_base = 50
            for idx, h in enumerate(hitos):
                cx = margen_x + idx * espacio_x
                cw = espacio_x - 14
                lineas_nombre = envolver_texto(h['autor'], max_chars=int(cw / 7.5))
                lineas_obra = envolver_texto(h.get('obra', ''), max_chars=int(cw / 6.5))
                lineas_fuente = envolver_texto(h.get('fuente', ''), max_chars=int(cw / 6.0))
                h_card = 28 + len(lineas_nombre) * 14 + len(lineas_obra) * 12 + len(lineas_fuente) * 12 + 10
                cy = y_base + 35
                nx = cx + cw / 2
                svg.append(f'<circle cx="{nx}" cy="{y_base + 12}" r="12" class="tl-ord-circle"/>')
                svg.append(f'<text x="{nx}" y="{y_base + 12}" class="tl-ord-num">{idx + 1}</text>')
                svg.append(f'<line x1="{nx}" y1="{y_base + 24}" x2="{nx}" y2="{cy}" class="tl-guide-line"/>')
                svg.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{h_card}" class="tl-card-box"/>')
                cur_y = cy + 18
                for ln in lineas_nombre:
                    svg.append(f'<text x="{cx + 10}" y="{cur_y}" class="tl-card-name">{ln}</text>')
                    cur_y += 14
                cur_y += 2
                for ln in lineas_obra:
                    svg.append(f'<text x="{cx + 10}" y="{cur_y}" class="tl-card-work">{ln}</text>')
                    cur_y += 12
                cur_y += 2
                for ln in lineas_fuente:
                    svg.append(f'<text x="{cx + 10}" y="{cur_y}" class="tl-card-src">{ln}</text>')
                    cur_y += 12
        else:
            cols = 4
            col_w = (ancho_util - (cols - 1) * 14) / cols
            for idx, h in enumerate(hitos):
                row = idx // cols
                col = idx % cols
                cx = margen_x + col * (col_w + 14)
                cy = 45 + row * 165
                lineas_nombre = envolver_texto(h['autor'], max_chars=24)
                lineas_obra = envolver_texto(h.get('obra', ''), max_chars=26)
                lineas_fuente = envolver_texto(h.get('fuente', ''), max_chars=28)
                h_card = 24 + len(lineas_nombre) * 14 + len(lineas_obra) * 12 + len(lineas_fuente) * 12 + 8
                svg.append(f'<rect x="{cx}" y="{cy}" width="{col_w}" height="{h_card}" class="tl-card-box"/>')
                svg.append(f'<circle cx="{cx + 16}" cy="{cy + 16}" r="9" class="tl-ord-circle"/>')
                svg.append(f'<text x="{cx + 16}" y="{cy + 16}" class="tl-ord-num" style="font-size:9.5px;">{idx + 1}</text>')
                cur_y = cy + 20
                svg.append(f'<text x="{cx + 32}" y="{cur_y}" class="tl-badge-ord">TRATADISTA {idx + 1}</text>')
                cur_y += 18
                for ln in lineas_nombre:
                    svg.append(f'<text x="{cx + 10}" y="{cur_y}" class="tl-card-name">{ln}</text>')
                    cur_y += 14
                cur_y += 2
                for ln in lineas_obra:
                    svg.append(f'<text x="{cx + 10}" y="{cur_y}" class="tl-card-work">{ln}</text>')
                    cur_y += 12
                cur_y += 2
                for ln in lineas_fuente:
                    svg.append(f'<text x="{cx + 10}" y="{cur_y}" class="tl-card-src">{ln}</text>')
                    cur_y += 12

        svg.append('</svg>')
        return '\n'.join(svg)

    # Caso 2: Guía docente o Ficha verificada (Eje real de siglos/años con fechas)
    alto_real = 440
    y_eje = 160

    # Determinar rango dinámico
    if ano_min is None or ano_max is None:
        anos_hitos = [h['ano_numerico'] for h in hitos]
        min_h = min(anos_hitos)
        max_h = max(anos_hitos)
        if any(h < 0 for h in anos_hitos):
            calc_min = min(-600, min_h - 20)
            calc_max = max(600, max_h + 20)
        else:
            calc_min = max(0, min_h - 20)
            calc_max = max_h + 20
        ano_min = ano_min if ano_min is not None else calc_min
        ano_max = ano_max if ano_max is not None else calc_max

    if ano_max <= ano_min:
        ano_max = ano_min + 50

    ancho_eje = ancho - 2 * margen_x

    def ano_a_x(ano: int) -> float:
        ratio = (ano - ano_min) / (ano_max - ano_min)
        ratio = max(0.0, min(1.0, ratio))
        return margen_x + ratio * ancho_eje

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto_real}" class="didactic-svg didactic-timeline">',
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
        '.tl-notice-box { fill: #fffbeb; stroke: #fde68a; stroke-width: 1.2; rx: 6px; }',
        '.tl-notice-text { font-family: system-ui, sans-serif; font-size: 10px; font-weight: 700; fill: #b45309; }',
        '</style>',
        f'<rect width="{ancho}" height="{alto_real}" class="tl-bg"/>',
    ]

    if not cron_verificada:
        svg.append(f'<rect x="{margen_x}" y="12" width="{ancho_eje}" height="28" class="tl-notice-box"/>')
        svg.append(
            f'<text x="{ancho // 2}" y="30" class="tl-notice-text" style="text-anchor:middle;">'
            '⚠️ Ficha cronologia_autores pendiente de verificación — en material del alumnado solo se muestra el orden sin fechas'
            '</text>'
        )

    svg.append(f'<line x1="{margen_x}" y1="{y_eje}" x2="{ancho - margen_x}" y2="{y_eje}" class="tl-axis"/>')

    # Divisoria de era solo si 0 cae dentro del rango estricto
    if ano_min < 0 < ano_max:
        x_cero = ano_a_x(0)
        svg.append(f'<line x1="{x_cero}" y1="48" x2="{x_cero}" y2="{y_eje + 80}" class="tl-era-divide"/>')
        svg.append(f'<text x="{x_cero - 12}" y="60" class="tl-era-badge" style="text-anchor:end;">a. C.</text>')
        svg.append(f'<text x="{x_cero + 12}" y="60" class="tl-era-badge" style="text-anchor:start;">d. C.</text>')

    # Generación de ticks y etiquetas
    delta_anos = ano_max - ano_min
    if delta_anos <= 150:
        paso_tick = 25
    elif delta_anos <= 400:
        paso_tick = 50
    else:
        paso_tick = 100

    primer_tick = ((ano_min + paso_tick - 1) // paso_tick) * paso_tick
    cur_tick = primer_tick
    while cur_tick <= ano_max:
        xs = ano_a_x(cur_tick)
        if cur_tick < 0:
            txt_tick = f"{abs(cur_tick)} a.C."
        elif cur_tick == 0:
            txt_tick = "0"
        else:
            txt_tick = str(cur_tick)
        svg.append(f'<line x1="{xs}" y1="{y_eje - 4}" x2="{xs}" y2="{y_eje + 4}" class="tl-century-tick"/>')
        svg.append(f'<text x="{xs}" y="{y_eje + 15}" class="tl-century-label">{txt_tick}</text>')
        cur_tick += paso_tick

    for i, hito in enumerate(hitos):
        x_nodo = ano_a_x(hito['ano_numerico'])
        arriba = (i % 2 == 0)
        y_stem = y_eje - 50 if arriba else y_eje + 65
        y_txt = y_stem - 24 if arriba else y_stem + 14

        svg.append(f'<line x1="{x_nodo}" y1="{y_eje}" x2="{x_nodo}" y2="{y_stem}" class="tl-stem"/>')
        svg.append(f'<circle cx="{x_nodo}" cy="{y_eje}" r="5.5" class="tl-node"/>')

        anchor = 'middle'
        if x_nodo < margen_x + 60:
            anchor = 'start'
        elif x_nodo > ancho - margen_x - 60:
            anchor = 'end'

        autor_ln = envolver_texto(hito['autor'], 22)
        cur_y = y_txt
        for ln in autor_ln:
            svg.append(f'<text x="{x_nodo}" y="{cur_y}" class="tl-card-author" style="text-anchor:{anchor};">{ln}</text>')
            cur_y += 12

        fecha_lbl = hito['epoca'] if cron_verificada else f"{hito['epoca']} [sin verificar]"
        if hito.get('sin_fuente'):
            fecha_lbl += ' [sin fuente]'
        svg.append(f'<text x="{x_nodo}" y="{cur_y}" class="tl-card-date" style="text-anchor:{anchor};">{fecha_lbl}</text>')
        cur_y += 11

        fuente_lbl = hito.get('fuente') or hito.get('obra', '')
        if hito.get('sin_fuente') and not fuente_lbl.startswith('['):
            fuente_lbl = f"[{fuente_lbl}]"
        lineas_fuente = [fuente_lbl] if hito.get('sin_fuente') else envolver_texto(fuente_lbl, 28)
        for ln in lineas_fuente:
            svg.append(f'<text x="{x_nodo}" y="{cur_y}" class="tl-card-work" style="text-anchor:{anchor};">{ln}</text>')
            cur_y += 10

    svg.append('</svg>')
    return '\n'.join(svg)


# ============================================================================
# 5. TETRACORDOS (Tres géneros con Verovio y afinación dual)
# ============================================================================

def calcular_afinacion_tetracordos(sistema: str = 'pitagorica') -> dict[str, Any]:
    """Calcula deterministamente los cents y frecuencias Hz de los tres géneros
    de tetracordos (diatónico, cromático, enarmónico) a partir de la misma función:
    Pitagórica:
      - Diatónico:  204 + 204 + 90  (suma 498 cents)
      - Cromático:  294 + 114 + 90  (suma 498 cents)
      - Enarmónico: 408 +  45 + 45  (suma 498 cents)
    Temperada:
      - Diatónico:  200 + 200 + 100 (suma 500 cents)
      - Cromático:  300 + 100 + 100 (suma 500 cents)
      - Enarmónico: 400 +  50 +  50 (suma 500 cents)
    Nota de cuarto de tono en el enarmónico: 'si ↑¼' a 254.0 Hz.
    """
    sistema = (sistema or 'pitagorica').lower().strip()
    if sistema not in ('pitagorica', 'temperada'):
        sistema = 'pitagorica'

    if sistema == 'pitagorica':
        return {
            'sistema': 'pitagorica',
            'nombre_sistema': 'Afinación pitagórica exacta (proporciones puras)',
            'generos': {
                'diatonico': {
                    'nombre': '1. Género Diatónico',
                    'formula': 'Tono – Tono – Semitono (Límma)',
                    'cents': [204, 204, 90],
                    'suma_cents': 498,
                    'notas': [
                        {'nombre': 'Mi4', 'freq_hz': 330.0, 'cents_intervalo': 0},
                        {'nombre': 'Re4', 'freq_hz': 293.33, 'cents_intervalo': 204},
                        {'nombre': 'Do4', 'freq_hz': 260.74, 'cents_intervalo': 204},
                        {'nombre': 'Si3', 'freq_hz': 247.5, 'cents_intervalo': 90},
                    ],
                    'frecuencias_hz': [330.0, 293.33, 260.74, 247.5],
                },
                'cromatico': {
                    'nombre': '2. Género Cromático',
                    'formula': 'Trihemitono – Semitono – Semitono',
                    'cents': [294, 114, 90],
                    'suma_cents': 498,
                    'notas': [
                        {'nombre': 'Mi4', 'freq_hz': 330.0, 'cents_intervalo': 0},
                        {'nombre': 'Do♯4', 'freq_hz': 278.44, 'cents_intervalo': 294},
                        {'nombre': 'Do♮4', 'freq_hz': 260.74, 'cents_intervalo': 114},
                        {'nombre': 'Si3', 'freq_hz': 247.5, 'cents_intervalo': 90},
                    ],
                    'frecuencias_hz': [330.0, 278.44, 260.74, 247.5],
                },
                'enarmonico': {
                    'nombre': '3. Género Enarmónico (cuartos de tono)',
                    'formula': 'Dítono – Díesis – Díesis',
                    'cents': [408, 45, 45],
                    'suma_cents': 498,
                    'notas': [
                        {'nombre': 'Mi4', 'freq_hz': 330.0, 'cents_intervalo': 0},
                        {'nombre': 'Do4', 'freq_hz': 260.74, 'cents_intervalo': 408},
                        {'nombre': 'si ↑¼', 'freq_hz': 254.04, 'cents_intervalo': 45},
                        {'nombre': 'Si3', 'freq_hz': 247.5, 'cents_intervalo': 45},
                    ],
                    'frecuencias_hz': [330.0, 260.74, 254.04, 247.5],
                },
            },
        }
    else:  # temperada
        return {
            'sistema': 'temperada',
            'nombre_sistema': 'Temperamento igual moderno (12-EDO)',
            'generos': {
                'diatonico': {
                    'nombre': '1. Género Diatónico',
                    'formula': 'Tono – Tono – Semitono',
                    'cents': [200, 200, 100],
                    'suma_cents': 500,
                    'notas': [
                        {'nombre': 'Mi4', 'freq_hz': 329.63, 'cents_intervalo': 0},
                        {'nombre': 'Re4', 'freq_hz': 293.66, 'cents_intervalo': 200},
                        {'nombre': 'Do4', 'freq_hz': 261.63, 'cents_intervalo': 200},
                        {'nombre': 'Si3', 'freq_hz': 246.94, 'cents_intervalo': 100},
                    ],
                    'frecuencias_hz': [329.63, 293.66, 261.63, 246.94],
                },
                'cromatico': {
                    'nombre': '2. Género Cromático',
                    'formula': 'Trihemitono – Semitono – Semitono',
                    'cents': [300, 100, 100],
                    'suma_cents': 500,
                    'notas': [
                        {'nombre': 'Mi4', 'freq_hz': 329.63, 'cents_intervalo': 0},
                        {'nombre': 'Do♯4', 'freq_hz': 277.18, 'cents_intervalo': 300},
                        {'nombre': 'Do♮4', 'freq_hz': 261.63, 'cents_intervalo': 100},
                        {'nombre': 'Si3', 'freq_hz': 246.94, 'cents_intervalo': 100},
                    ],
                    'frecuencias_hz': [329.63, 277.18, 261.63, 246.94],
                },
                'enarmonico': {
                    'nombre': '3. Género Enarmónico (cuartos de tono)',
                    'formula': 'Dítono – Díesis – Díesis',
                    'cents': [400, 50, 50],
                    'suma_cents': 500,
                    'notas': [
                        {'nombre': 'Mi4', 'freq_hz': 329.63, 'cents_intervalo': 0},
                        {'nombre': 'Do4', 'freq_hz': 261.63, 'cents_intervalo': 400},
                        {'nombre': 'si ↑¼', 'freq_hz': 254.18, 'cents_intervalo': 50},
                        {'nombre': 'Si3', 'freq_hz': 246.94, 'cents_intervalo': 50},
                    ],
                    'frecuencias_hz': [329.63, 261.63, 254.18, 246.94],
                },
            },
        }


def renderizar_tetracordos_verovio_svg(xml_content: str | None = None) -> str:
    """Renderiza con Verovio el MusicXML de los tres géneros de tetracordos
    (clave de sol, notas sin plica, sin compás) y convierte el glifo de Stein
    (accidentalQuarterToneSharpStein, SMuFL E282) a un trazado vectorial explícito
    extraído de la fuente Bravura para garantizar su impresión idéntica en PDF."""
    from pathlib import Path
    import re
    import verovio

    if not xml_content:
        from docente_ai.music.greek import generar_partitura_tres_generos_musicxml
        xml_content = generar_partitura_tres_generos_musicxml()

    data_dir = Path(verovio.__file__).parent / "data"
    tk = verovio.toolkit(False)
    if data_dir.is_dir():
        tk.setResourcePath(str(data_dir))

    tk.setOptions({
        "pageWidth": 1800,
        "pageHeight": 450,
        "scale": 45,
        "adjustPageHeight": True,
        "breaks": "none",
        "header": "none",
        "footer": "none",
    })
    tk.loadData(xml_content)
    if tk.getPageCount() < 1:
        return ""
    svg = tk.renderToSVG(1)

    sym_m = re.search(r'<symbol id="(E282[^"]*)"[^>]*>([\s\S]*?)</symbol>', svg)
    if sym_m:
        sym_id = sym_m.group(1)
        path_m = re.search(r'<path[^>]*d="([^"]+)"', sym_m.group(2))
        if path_m:
            path_d = path_m.group(1)
            use_pattern = re.compile(
                rf'<use[^>]*xlink:href="#{re.escape(sym_id)}"[^>]*x="([^"]+)"[^>]*y="([^"]+)"[^>]*height="([^"]+)"[^>]*width="([^"]+)"[^>]*/>'
            )
            def _repl(m):
                x = m.group(1)
                y = m.group(2)
                h_val = float(m.group(3).replace("px", ""))
                scale = h_val / 1000.0
                return (
                    f'<g transform="translate({x}, {y}) scale({scale})">'
                    f'<path transform="scale(1,-1)" d="{path_d}" fill="currentColor" />'
                    f'</g>'
                )
            svg = use_pattern.sub(_repl, svg)

    return svg


def generar_svg_tetracordos(sistema: str = 'pitagorica') -> str:
    """Genera la partitura de tetracordos renderizada con Verovio desde MusicXML
    (clave de sol, sin plica, sin compás, y cuarto de tono con trazado de Stein)."""
    return renderizar_tetracordos_verovio_svg()


# ============================================================================
# 6. DICCIONARIO INTEGRADO Y RESOLUCIÓN DE COMPONENTES
# ============================================================================

def resolver_componente_didactico(
    tipo: str,
    parametros: dict[str, Any] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    claims: list[dict[str, Any]] | None = None,
    visualizaciones: list[dict[str, Any]] | None = None,
    topic: str | None = None,
    subject: str | None = None,
    periodo: str | None = None,
) -> dict[str, Any]:
    """Resuelve deterministamente un componente didáctico musical devolviendo sus
    datos estructurados, frecuencias sonoras y código SVG listo para renderizado.
    Valida parámetros estrictamente: si no puede representar lo pedido o está fuera de ámbito,
    devuelve estado 'descartado' con el motivo explicativo. Nunca cae a un contenido por defecto."""
    tipo = (tipo or '').strip().lower()
    parametros = parametros or {}

    # 1. Comprobar ámbito temático y cronológico
    valido_ambito, motivo_ambito = comprobar_ambito_componente(
        tipo, topic=topic, subject=subject, periodo=periodo, parametros=parametros
    )
    if not valido_ambito:
        return {
            'tipo': tipo,
            'titulo': f"Componente didáctico ({tipo})",
            'estado': 'descartado',
            'motivo_descarte': motivo_ambito,
            'calculado_teoria': False,
            'verificado': False,
            'svg': None,
        }

    # 2. Tetracordos
    if tipo in ('tetracordos', 'tetracordo'):
        from docente_ai.music.greek import asegurar_archivo_partitura_tres_generos
        archivo = asegurar_archivo_partitura_tres_generos()
        svg_partitura = renderizar_tetracordos_verovio_svg()
        af_pit = calcular_afinacion_tetracordos('pitagorica')
        af_temp = calcular_afinacion_tetracordos('temperada')
        return {
            'tipo': 'tetracordos',
            'titulo': 'Tetracordo descendente mi–si en los tres géneros',
            'archivo_partitura': archivo,
            'svg': svg_partitura,
            'svg_partitura': svg_partitura,
            'afinacion_pitagorica': af_pit,
            'afinacion_temperada': af_temp,
            'afinados': {
                'pitagorica': {
                    'diatonico': af_pit['generos']['diatonico']['frecuencias_hz'],
                    'cromatico': af_pit['generos']['cromatico']['frecuencias_hz'],
                    'enarmonico': af_pit['generos']['enarmonico']['frecuencias_hz'],
                },
                'temperada': {
                    'diatonico': af_temp['generos']['diatonico']['frecuencias_hz'],
                    'cromatico': af_temp['generos']['cromatico']['frecuencias_hz'],
                    'enarmonico': af_temp['generos']['enarmonico']['frecuencias_hz'],
                },
            },
            'frecuencias_hz': af_pit['generos']['diatonico']['frecuencias_hz'],
            'descripcion': 'Ilustración de la subdivisión del intervalo de cuarta en los géneros diatónico, cromático y enarmónico.',
            'calculado_teoria': True,
            'verificado': True,
            'estado': 'cumplido',
        }

    # 3. Gran Sistema Perfecto
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
            'estado': 'cumplido',
        }

    # 4. Monocordio
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
            'estado': 'cumplido',
        }

    # 5. Escalera de intervalos
    elif tipo in ('escalera_intervalos', 'escalera', 'cents'):
        intervalos_solicitados = parametros.get('intervalos')
        mostrar_tc = bool(parametros.get('mostrar_tetracordos'))
        afinacion = str(parametros.get('afinacion', 'justa')).lower()
        if afinacion not in ('justa', 'pitagorica'):
            afinacion = 'justa'

        # Caso A: Lista explícita de intervalos solicitada
        if intervalos_solicitados is not None:
            if not isinstance(intervalos_solicitados, (list, tuple)) or len(intervalos_solicitados) == 0:
                return {
                    'tipo': 'escalera_intervalos',
                    'titulo': 'Escalera de intervalos',
                    'estado': 'descartado',
                    'motivo_descarte': 'La lista de intervalos proporcionada está vacía.',
                    'calculado_teoria': True,
                    'verificado': False,
                    'svg': None,
                }

            lista_datos = []
            for inter_raw in intervalos_solicitados:
                key_norm = normalizar_nombre_intervalo(str(inter_raw))
                if not key_norm or key_norm not in MAPA_INTERVALOS_CANONICOS:
                    return {
                        'tipo': 'escalera_intervalos',
                        'titulo': 'Escalera de intervalos',
                        'estado': 'descartado',
                        'motivo_descarte': f"Intervalo no reconocido o no representable: '{inter_raw}'.",
                        'calculado_teoria': True,
                        'verificado': False,
                        'svg': None,
                    }
                canon_item = MAPA_INTERVALOS_CANONICOS[key_norm]
                razon = canon_item['razon_justa'] if afinacion == 'justa' else canon_item['razon_pit']
                cents = canon_item['cents_justa'] if afinacion == 'justa' else canon_item['cents_pit']
                lista_datos.append({
                    'nombre': canon_item['nombre'],
                    'razon_str': razon,
                    'cents': cents,
                    'color': canon_item['color'],
                })

            svg_cust = generar_svg_escalera_intervalos_personalizada(lista_datos, afinacion=afinacion)
            return {
                'tipo': 'escalera_intervalos',
                'titulo': f'Escalera de Intervalos en Cents (Afinación {afinacion})',
                'svg': svg_cust,
                'intervalos': lista_datos,
                'afinacion': afinacion,
                'descripcion': f'Comparativa exacta de proporciones y cents para los intervalos solicitados ({afinacion}).',
                'calculado_teoria': True,
                'verificado': True,
                'estado': 'cumplido',
            }

        # Caso B: Sin lista de intervalos explícita
        # Solo se generan tetracordos si se solicitó de forma expresa en los parámetros:
        if mostrar_tc:
            svg = generar_svg_escalera_intervalos()
            return {
                'tipo': 'escalera_intervalos',
                'titulo': 'Escalera de Intervalos en Cents',
                'svg': svg,
                'descripcion': 'Comparativa de las dimensiones interválicas en cents de los tres géneros.',
                'calculado_teoria': True,
                'verificado': True,
                'estado': 'cumplido',
            }
        else:
            return {
                'tipo': 'escalera_intervalos',
                'titulo': 'Escalera de intervalos',
                'estado': 'descartado',
                'motivo_descarte': 'No se han especificado los intervalos que deben representarse en la escalera (ej. unísono, tercera, quinta, octava), ni se solicitó expresamente la división de tetracordos.',
                'calculado_teoria': True,
                'verificado': False,
                'svg': None,
            }

    # 6. Línea temporal
    elif tipo in ('linea_temporal', 'cronologia', 'timeline'):
        autores = parametros.get('autores')
        hitos_param = parametros.get('hitos')

        # Parsear inicio y fin si se proporcionan
        inicio_num: int | None = None
        fin_num: int | None = None
        if parametros.get('inicio') is not None:
            try:
                inicio_num = int(str(parametros['inicio']).replace('c.', '').replace('a. C.', '-').replace('d. C.', '').strip())
            except Exception:
                pass
        if parametros.get('fin') is not None:
            try:
                fin_num = int(str(parametros['fin']).replace('c.', '').replace('a. C.', '-').replace('d. C.', '').strip())
            except Exception:
                pass

        if inicio_num is not None and fin_num is not None and inicio_num > fin_num:
            return {
                'tipo': 'linea_temporal',
                'titulo': 'Línea temporal histórica',
                'estado': 'descartado',
                'motivo_descarte': f"Rango cronológico inválido: el año de inicio ({inicio_num}) es posterior al año de fin ({fin_num}).",
                'calculado_teoria': False,
                'verificado': False,
                'svg': None,
            }

        hitos = construir_hitos_linea_temporal(
            evidence=evidence,
            autores_solicitados=autores,
            claims=claims,
            visualizaciones=visualizaciones,
            inicio=inicio_num,
            fin=fin_num,
            hitos_modelo=hitos_param,
            topic=topic,
            subject=subject,
        )

        if not hitos:
            rango_desc = f" ({inicio_num}–{fin_num})" if (inicio_num or fin_num) else ""
            return {
                'tipo': 'linea_temporal',
                'titulo': 'Línea temporal histórica',
                'estado': 'descartado',
                'motivo_descarte': f"No se han encontrado autores o hitos cronológicos documentados en el rango solicitado{rango_desc}.",
                'calculado_teoria': False,
                'verificado': False,
                'svg': None,
            }

        svg_docente = generar_svg_linea_temporal(hitos, para_alumnado=False, ano_min=inicio_num, ano_max=fin_num)
        svg_alumnado = generar_svg_linea_temporal(hitos, para_alumnado=True, ano_min=inicio_num, ano_max=fin_num)
        return {
            'tipo': 'linea_temporal',
            'titulo': 'Línea Temporal de Tratadistas y Figuras Históricas',
            'svg': svg_docente,
            'svg_alumnado': svg_alumnado,
            'hitos': hitos,
            'descripcion': 'Eje cronológico real construido a partir de los autores y fuentes documentadas en la propuesta.',
            'calculado_teoria': False,
            'verificado': True,
            'estado': 'cumplido',
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
