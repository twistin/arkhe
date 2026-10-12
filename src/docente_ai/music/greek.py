"""Generador de tetracordos en la teoría musical de la Grecia Antigua.

Genera los tres géneros de tetracordos (diatónico, cromático y enarmónico con cuartos de tono)
a partir de una nota de partida (o frecuencia base), calculando las frecuencias exactas en Hz.

Intervalos del tetracordo griego (ámbito de cuarta justa, razón 4:3 o 498-500 cents):
1. Diatónico: semitono, tono, tono (en cents temperados o pitagóricos, aprox 100c, 200c, 200c).
   En afinación pitagórica / teoría griega estándar (Architas / Aristóxeno / Ptolomeo):
   - Frecuencia base f0
   - Nota 1: +100 cents (semitono diatónico) o limma (256/243 ~ 1.0535)
   - Nota 2: +300 cents (semitono + tono) o sesquioctava (9/8)
   - Nota 3: +500 cents (cuarta justa, 4/3 ~ 1.3333)
2. Cromático: semitono, semitono, trihemitono (tercera menor) (100c, 100c, 300c).
3. Enarmónico: cuarto de tono (diesis), cuarto de tono (diesis), ditono (tercera mayor) (50c, 50c, 400c).
"""

from typing import Any
import math

# Frecuencias de referencia estándar (A4 = 440 Hz)
NOTE_OFFSETS = {
    "C": -9, "C#": -8, "DB": -8,
    "D": -7, "D#": -6, "EB": -6,
    "E": -5,
    "F": -4, "F#": -3, "GB": -3,
    "G": -2, "G#": -1, "AB": -1,
    "A": 0, "A#": 1, "BB": 1,
    "B": 2,
}


def note_name_to_freq(note_str: str) -> float:
    """Convierte un nombre de nota como 'A4', 'E4', 'C4' a frecuencia en Hz (A4 = 440 Hz)."""
    clean = note_str.strip().upper()
    if not clean:
        return 440.0
    
    # Extraer octava si existe al final
    octave = 4
    if clean[-1].isdigit():
        octave = int(clean[-1])
        pitch_name = clean[:-1]
    else:
        pitch_name = clean

    offset = NOTE_OFFSETS.get(pitch_name, 0)
    semitones_from_a4 = offset + (octave - 4) * 12
    return 440.0 * (2.0 ** (semitones_from_a4 / 12.0))


def freq_from_cents(base_freq: float, cents: float) -> float:
    """Calcula la frecuencia en Hz añadiendo un desplazamiento en cents."""
    return base_freq * (2.0 ** (cents / 1200.0))


def generar_tetracordos(
    base: str | float = 440.0,
    direccion: str = "ascendente",
    sistema: str = "temperado",
) -> dict[str, Any]:
    """Genera los tetracordos diatónico, cromático y enarmónico con frecuencias exactas en Hz.

    Parámetros:
        base: Nota de partida (ej. 'E4', 'A4') o frecuencia en Hz (ej. 440.0).
        direccion: 'ascendente' o 'descendente'.
        sistema: 'temperado' (100 cents/semitono, 50 cents/cuarto de tono) o 'justo'/'pitagorico'.

    Devuelve:
        Diccionario con las notas, frecuencias exactas en Hz y proporciones de cada género.
    """
    if isinstance(base, (int, float)):
        base_freq = float(base)
        base_name = f"{base_freq:.1f} Hz"
    else:
        base_name = str(base)
        base_freq = note_name_to_freq(base_name)

    sign = 1.0 if direccion == "ascendente" else -1.0

    # 1. Diatónico: semitono (100 c), tono (200 c), tono (200 c) -> acum: 0, 100, 300, 500 c
    # En afinación pitagórica exacta: 1/1, 256/243 (90c), 32/27 (294c), 4/3 (498c)
    if sistema == "pitagorico":
        if direccion == "ascendente":
            diatonico_freqs = [base_freq, base_freq * (256 / 243), base_freq * (32 / 27), base_freq * (4 / 3)]
            cromatico_freqs = [base_freq, base_freq * (256 / 243), base_freq * (9 / 8), base_freq * (4 / 3)]
            # Enarmónico: diesis de 50 cents o 28/27, 16/15, 4/3 según Arquitas
            enarmonico_freqs = [
                base_freq,
                freq_from_cents(base_freq, 50),
                freq_from_cents(base_freq, 100),
                base_freq * (4 / 3),
            ]
        else:
            diatonico_freqs = [base_freq, base_freq / (256 / 243), base_freq / (32 / 27), base_freq / (4 / 3)]
            cromatico_freqs = [base_freq, base_freq / (256 / 243), base_freq / (9 / 8), base_freq / (4 / 3)]
            enarmonico_freqs = [
                base_freq,
                freq_from_cents(base_freq, -50),
                freq_from_cents(base_freq, -100),
                base_freq / (4 / 3),
            ]
    else:
        # Sistema estándar de cuartos de tono (Aristóxeno / 24-EDO)
        # Diatónico: 0, 100, 300, 500 cents
        diat_cents = [0, 100 * sign, 300 * sign, 500 * sign]
        diatonico_freqs = [freq_from_cents(base_freq, c) for c in diat_cents]

        # Cromático: 0, 100, 200, 500 cents (semitono, semitono, trihemitono de 300 c)
        crom_cents = [0, 100 * sign, 200 * sign, 500 * sign]
        cromatico_freqs = [freq_from_cents(base_freq, c) for c in crom_cents]

        # Enarmónico: 0, 50, 100, 500 cents (diesis 1/4 tono, diesis 1/4 tono, ditono 400 c)
        enarm_cents = [0, 50 * sign, 100 * sign, 500 * sign]
        enarmonico_freqs = [freq_from_cents(base_freq, c) for c in enarm_cents]

    return {
        "base": base_name,
        "frecuencia_base_hz": round(base_freq, 2),
        "direccion": direccion,
        "generos": {
            "diatonico": {
                "nombre": "Diatónico",
                "intervalos": "Semitono - Tono - Tono",
                "cents": [0, 100, 300, 500] if direccion == "ascendente" else [0, -100, -300, -500],
                "frecuencias_hz": [round(f, 2) for f in diatonico_freqs],
            },
            "cromatico": {
                "nombre": "Cromático",
                "intervalos": "Semitono - Semitono - Trihemitono (3 semitonos)",
                "cents": [0, 100, 200, 500] if direccion == "ascendente" else [0, -100, -200, -500],
                "frecuencias_hz": [round(f, 2) for f in cromatico_freqs],
            },
            "enarmonico": {
                "nombre": "Enarmónico (cuartos de tono)",
                "intervalos": "Diesis (1/4 tono) - Diesis (1/4 tono) - Ditono (2 tonos)",
                "cents": [0, 50, 100, 500] if direccion == "ascendente" else [0, -50, -100, -500],
                "frecuencias_hz": [round(f, 2) for f in enarmonico_freqs],
            },
        },
    }


def generar_partitura_tres_generos_musicxml() -> str:
    """Genera deterministamente con music21 el MusicXML del tetracordo descendente mi–si en los tres géneros:
    diatónico, cromático y enarmónico (con cuartos de tono / diéseis).
    """
    from docente_ai.music import get_music21
    m21 = get_music21()

    score = m21.stream.Score()
    part = m21.stream.Part()
    part.id = "Tetracordos"

    part.append(m21.clef.TrebleClef())
    part.append(m21.meter.TimeSignature('4/4'))

    # Compás 1: Diatónico (E4, D4, C4, B3)
    m1 = m21.stream.Measure(number=1)
    m1.append(m21.expressions.TextExpression('1. Diatónico'))
    n1 = m21.note.Note('E4', quarterLength=1)
    n2 = m21.note.Note('D4', quarterLength=1)
    n3 = m21.note.Note('C4', quarterLength=1)
    n4 = m21.note.Note('B3', quarterLength=1)
    m1.append([n1, n2, n3, n4])
    part.append(m1)

    # Compás 2: Cromático (E4, C#4, C4, B3)
    m2 = m21.stream.Measure(number=2)
    m2.append(m21.expressions.TextExpression('2. Cromático'))
    n5 = m21.note.Note('E4', quarterLength=1)
    n6 = m21.note.Note('C#4', quarterLength=1)
    n7 = m21.note.Note('C4', quarterLength=1)
    n7.pitch.accidental = m21.pitch.Accidental('natural')
    n8 = m21.note.Note('B3', quarterLength=1)
    m2.append([n5, n6, n7, n8])
    part.append(m2)

    # Compás 3: Enarmónico con cuartos de tono (E4, C4, B3+half-sharp, B3)
    m3 = m21.stream.Measure(number=3)
    m3.append(m21.expressions.TextExpression('3. Enarmónico (cuartos de tono)'))
    n9 = m21.note.Note('E4', quarterLength=1)
    n10 = m21.note.Note('C4', quarterLength=1)
    n10.pitch.accidental = m21.pitch.Accidental('natural')
    n11 = m21.note.Note('B3', quarterLength=1)
    n11.pitch.accidental = m21.pitch.Accidental('half-sharp')
    n12 = m21.note.Note('B3', quarterLength=1)
    n12.pitch.accidental = m21.pitch.Accidental('natural')
    m3.append([n9, n10, n11, n12])
    part.append(m3)

    score.append(part)
    xml_bytes = m21.musicxml.m21ToXml.GeneralObjectExporter().parse(score)
    return xml_bytes.decode('utf-8')


def asegurar_archivo_partitura_tres_generos() -> str:
    """Asegura que el archivo MusicXML del tetracordo exista en config/ejemplos y data/ejemplos."""
    from pathlib import Path
    xml_content = generar_partitura_tres_generos_musicxml()
    filename = "teoria_tetracordos_tres_generos.musicxml"

    rutas = [
        Path("config/ejemplos") / filename,
        Path("data/ejemplos") / filename,
    ]
    for r in rutas:
        r.parent.mkdir(parents=True, exist_ok=True)
        r.write_text(xml_content, encoding="utf-8")
    return filename

