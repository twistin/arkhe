"""Gestión y consulta del catálogo de ejemplos musicales verificables."""

from pathlib import Path
from typing import Any
import yaml

EJEMPLOS_DEFAULT_DIR = Path('data/ejemplos')
EJEMPLOS_EXAMPLE_DIR = Path('config/ejemplos')


def _resolve_ejemplos_dir(directory: Path | str | None = None) -> Path | None:
    """Resuelve el directorio de ejemplos con fallback a config/ejemplos."""
    if directory:
        target = Path(directory)
        if target.exists():
            return target
    if EJEMPLOS_DEFAULT_DIR.exists() and (
        (EJEMPLOS_DEFAULT_DIR / 'ejemplos.yaml').is_file()
        or (EJEMPLOS_DEFAULT_DIR / 'ejemplos.example.yaml').is_file()
    ):
        return EJEMPLOS_DEFAULT_DIR
    if EJEMPLOS_EXAMPLE_DIR.exists() and (
        (EJEMPLOS_EXAMPLE_DIR / 'ejemplos.example.yaml').is_file()
        or (EJEMPLOS_EXAMPLE_DIR / 'ejemplos.yaml').is_file()
    ):
        return EJEMPLOS_EXAMPLE_DIR
    return None


def load_all_ejemplos(directory: Path | str | None = None) -> list[dict[str, Any]]:
    """Carga todos los ejemplos del catálogo en YAML."""
    target_dir = _resolve_ejemplos_dir(directory)
    if not target_dir:
        return []

    yaml_file = target_dir / 'ejemplos.yaml'
    if not yaml_file.is_file():
        yaml_file = target_dir / 'ejemplos.example.yaml'
    if not yaml_file.is_file():
        return []

    try:
        raw = yaml_file.read_text(encoding='utf-8')
        data = yaml.safe_load(raw)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    ejemplos = []
    for item in data:
        if isinstance(item, dict) and 'id' in item:
            ejemplo = dict(item)
            archivo = ejemplo.get('archivo')
            if archivo:
                musicxml_path = target_dir / archivo
                ejemplo['archivo_existe'] = musicxml_path.is_file()
                ejemplo['archivo_path'] = str(musicxml_path)
            else:
                ejemplo['archivo_existe'] = False
                ejemplo['archivo_path'] = None
            ejemplos.append(ejemplo)

    return ejemplos


def get_ejemplo(id_ejemplo: str, directory: Path | str | None = None) -> dict[str, Any] | None:
    """Busca un ejemplo específico por su ID."""
    if not id_ejemplo:
        return None
    for ej in load_all_ejemplos(directory):
        if ej.get('id') == id_ejemplo:
            return ej
    return None


def get_ejemplo_musicxml(id_ejemplo: str, directory: Path | str | None = None) -> str | None:
    """Devuelve el contenido MusicXML de un ejemplo si existe."""
    ej = get_ejemplo(id_ejemplo, directory)
    if not ej:
        return None
    path_str = ej.get('archivo_path')
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return None


def is_ejemplo_verificado(id_ejemplo: str, directory: Path | str | None = None) -> bool:
    """Comprueba si un ejemplo musical está verificado."""
    ej = get_ejemplo(id_ejemplo, directory)
    if not ej:
        return False
    return bool(ej.get('verificado', False))
