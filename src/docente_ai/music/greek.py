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
