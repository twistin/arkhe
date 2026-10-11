"""Integración opcional con FluidSynth para exportar archivos MIDI a audio WAV.

FluidSynth NO es una dependencia obligatoria de Python.
Si el ejecutable `fluidsynth` está instalado en el sistema, ofrece la opción de exportar;
si no, la opción no está disponible.
"""

from pathlib import Path
import shutil
import subprocess

# Rutas estándar habituales para SoundFonts en Linux y macOS
SOUNDFONT_SEARCH_PATHS = [
    Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
    Path("/usr/share/soundfonts/FluidR3_GM.sf2"),
    Path("/usr/share/sounds/sf2/default.sf2"),
    Path("/usr/share/soundfonts/default.sf2"),
    Path("/opt/homebrew/share/soundfonts/FluidR3_GM.sf2"),
    Path("/usr/local/share/soundfonts/FluidR3_GM.sf2"),
]


def fluidsynth_binary() -> str | None:
    """Devuelve la ruta al ejecutable fluidsynth si está instalado en el sistema."""
    return shutil.which("fluidsynth")


def fluidsynth_available() -> bool:
    """Comprueba si el comando fluidsynth está disponible en el PATH del sistema."""
    return fluidsynth_binary() is not None


def find_default_soundfont() -> Path | None:
    """Busca un archivo SoundFont (.sf2) en ubicaciones conocidas del sistema."""
    for sf_path in SOUNDFONT_SEARCH_PATHS:
        if sf_path.is_file():
            return sf_path
    return None


def export_midi_to_wav(
    midi_path: Path | str,
    wav_path: Path | str,
    soundfont_path: Path | str | None = None,
    sample_rate: int = 44100,
) -> bool:
    """Convierte un archivo MIDI a WAV utilizando FluidSynth en modo fast-render (sin reproducir).

    Parámetros:
        midi_path: Ruta al archivo MIDI de entrada.
        wav_path: Ruta al archivo WAV de salida.
        soundfont_path: Ruta opcional al SoundFont (.sf2). Si es None, busca en rutas estándar.
        sample_rate: Frecuencia de muestreo (por defecto 44100 Hz).

    Devuelve:
        True si la conversión fue exitosa, False en caso contrario.
    """
    bin_path = fluidsynth_binary()
    if not bin_path:
        raise RuntimeError("FluidSynth no está instalado en el sistema.")

    midi_p = Path(midi_path)
    if not midi_p.is_file():
        raise FileNotFoundError(f"Archivo MIDI no encontrado: {midi_path}")

    sf_p = Path(soundfont_path) if soundfont_path else find_default_soundfont()
    if not sf_p or not sf_p.is_file():
        raise RuntimeError(
            "No se encontró ningún archivo SoundFont (.sf2). "
            "Especifique uno o instale FluidR3_GM en el sistema."
        )

    wav_p = Path(wav_path)
    wav_p.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        bin_path,
        "-ni",  # no interactivo
        "-F", str(wav_p),  # archivo de salida WAV
        "-r", str(sample_rate),
        str(sf_p),
        str(midi_p),
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return wav_p.is_file() and wav_p.stat().st_size > 0
    except subprocess.CalledProcessError as exc:
        stderr_msg = exc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"Error al ejecutar FluidSynth: {stderr_msg}") from exc
