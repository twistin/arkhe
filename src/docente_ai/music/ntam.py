"""Detección y comprobación de disponibilidad del grupo opcional ntam (librosa, pedalboard)."""

import importlib.util


def ntam_available() -> bool:
    """Devuelve True solo si tanto librosa como pedalboard están instalados en el entorno."""
    librosa_found = importlib.util.find_spec("librosa") is not None
    pedalboard_found = importlib.util.find_spec("pedalboard") is not None
    return bool(librosa_found and pedalboard_found)


def get_ntam_info() -> dict[str, bool | str]:
    """Proporciona el estado de disponibilidad detallado del grupo de análisis de audio y DSP."""
    librosa_ok = importlib.util.find_spec("librosa") is not None
    pedalboard_ok = importlib.util.find_spec("pedalboard") is not None
    disponible = bool(librosa_ok and pedalboard_ok)
    
    mensaje = (
        "Grupo opcional ntam activo (librosa y pedalboard disponibles)."
        if disponible
        else "Grupo opcional ntam no disponible (instale con: pip install '.[ntam]')."
    )
    
    return {
        "disponible": disponible,
        "librosa": bool(librosa_ok),
        "pedalboard": bool(pedalboard_ok),
        "mensaje": mensaje,
    }
