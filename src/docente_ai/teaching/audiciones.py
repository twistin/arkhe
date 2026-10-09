"""Servicio de gestión y consulta del catálogo de audiciones verificadas."""

from pathlib import Path
import re
import yaml

AUDICIONES_DEFAULT_PATH = Path('data/audiciones.yaml')
AUDICIONES_EXAMPLE_PATH = Path('config/audiciones.example.yaml')


def load_audiciones_catalog(path: Path | str | None = None) -> list[dict]:
    """Carga el catálogo de audiciones verificadas desde YAML."""
    target = Path(path) if path else AUDICIONES_DEFAULT_PATH
    if not target.exists():
        if AUDICIONES_EXAMPLE_PATH.exists():
            target = AUDICIONES_EXAMPLE_PATH
        else:
            return []
    try:
        content = yaml.safe_load(target.read_text(encoding='utf-8'))
    except Exception:
        return []
    if isinstance(content, dict):
        return content.get('audiciones') or []
    if isinstance(content, list):
        return content
    return []


def get_audicion_by_id(audicion_id: str, catalog: list[dict] | None = None) -> dict | None:
    """Busca una audición por su ID en el catálogo."""
    items = catalog if catalog is not None else load_audiciones_catalog()
    for item in items:
        if item.get('id') == audicion_id:
            return item
    return None


def find_audiciones_for_topic(
    topic: str,
    criteria: str = '',
    catalog: list[dict] | None = None,
    limit: int = 4
) -> list[dict]:
    """Encuentra audiciones relevantes en el catálogo para un tema y criterios dados."""
    items = catalog if catalog is not None else load_audiciones_catalog()
    if not items:
        return []
    
    query_text = f"{topic} {criteria}".lower()
    scored = []
    for item in items:
        score = 0
        a_id = item.get('id', '').lower()
        obra = item.get('obra', '').lower()
        comp = item.get('compositor', '').lower()
        tags = [t.lower() for t in item.get('temas_relacionados', [])]
        
        # Coincidencia directa por id o compositor o tags
        for t in tags:
            if t in query_text:
                score += 3
        if comp and comp != 'pendiente de verificar' and comp in query_text:
            score += 4
        if obra and obra != 'pendiente de verificar' and obra in query_text:
            score += 3
        if a_id in query_text:
            score += 5
        
        if score > 0:
            scored.append((score, item))
            
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]
