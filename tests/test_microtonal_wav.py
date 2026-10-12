"""Test para la exportación y síntesis exacta de ejemplos microtonales (WAV).

Comprueba que el WAV generado conserve exactamente los cuartos de tono
y que la frecuencia de la tercera nota del enarmónico (Si con diesis / cuarto de tono sostenido)
sea de aproximadamente 254 Hz.
"""

import io
import wave
from pathlib import Path
import numpy as np
import pytest

from docente_ai.web.workspace import Workspace
from docente_ai.music.greek import sintetizar_tetracordos_wav
from test_generation import FakeEmbedder


def test_sintesis_tetracordos_wav_frecuencias_exactas():
    """Comprueba que la síntesis de tetracordos preserve la frecuencia de la 3ª nota del enarmónico (≈254 Hz)."""
    # 12 notas:
    # 0-3: Diatónico (E4, D4, C4, B3)
    # 4-7: Cromático (E4, C#4, C4, B3)
    # 8-11: Enarmónico (E4, C4, B3+diesis, B3)
    # La 3ª nota del enarmónico es el índice 10 (B3+diesis, 254.18 Hz).
    dur_nota = 0.6
    dur_silencio = 0.05
    sample_rate = 44100

    wav_bytes = sintetizar_tetracordos_wav(
        duracion_nota=dur_nota,
        duracion_silencio=dur_silencio,
        sample_rate=sample_rate,
    )
    assert wav_bytes[:4] == b"RIFF"
    assert b"WAVE" in wav_bytes[:16]

    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == sample_rate
        raw_frames = wf.readframes(wf.getnframes())

    samples = np.frombuffer(raw_frames, dtype=np.int16)
    
    # Extraer el segmento central de la 3ª nota del enarmónico (índice 10)
    samples_por_nota_total = int(sample_rate * (dur_nota + dur_silencio))
    inicio_nota_10 = 10 * samples_por_nota_total
    # Tomar la porción central estable (omitiendo los transitorios de ataque y relajación)
    chunk_inicio = inicio_nota_10 + int(sample_rate * 0.1)
    chunk_fin = inicio_nota_10 + int(sample_rate * 0.5)
    chunk = samples[chunk_inicio:chunk_fin]

    # Calcular la FFT con alta resolución mediante zero-padding (n = sample_rate * 4 -> resolución 0.25 Hz)
    n_fft = sample_rate * 4
    spectrum = np.abs(np.fft.rfft(chunk, n=n_fft))
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)
    pico_freq = freqs[np.argmax(spectrum)]

    # La frecuencia teórica es 254.18 Hz
    assert abs(pico_freq - 254.18) <= 2.0, (
        f"Se esperaba una frecuencia de ≈254 Hz para el Si+diesis del enarmónico, "
        f"pero se midió {pico_freq:.2f} Hz"
    )


def test_export_score_wav_ejemplo_microtonal_frecuencia_enarmonica(tmp_path):
    """Comprueba que export_score_wav devuelva el audio exacto con la tercera nota enarmónica a ≈254 Hz."""
    ws = Workspace(tmp_path, embedder_factory=FakeEmbedder)
    wav_bytes = ws.export_score_wav("teoria-tetracordos-tres-generos")

    assert wav_bytes.startswith(b"RIFF")
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        sample_rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())

    samples = np.frombuffer(raw, dtype=np.int16)
    # Por defecto duracion_nota = 0.6, duracion_silencio = 0.05
    dur_total = 0.65
    idx_nota_10 = 10
    inicio = int(idx_nota_10 * dur_total * sample_rate) + int(sample_rate * 0.1)
    fin = int(idx_nota_10 * dur_total * sample_rate) + int(sample_rate * 0.5)
    chunk = samples[inicio:fin]

    n_fft = sample_rate * 4
    spectrum = np.abs(np.fft.rfft(chunk, n=n_fft))
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)
    pico = freqs[np.argmax(spectrum)]

    assert abs(pico - 254.18) <= 2.0
