"""Carga perezosa de music21 para no ralentizar el arranque de la aplicación."""

_music21_module = None


def get_music21():
    """Importa music21 bajo demanda solo cuando se procesa una partitura."""
    global _music21_module
    if _music21_module is None:
        import music21
        _music21_module = music21
    return _music21_module
