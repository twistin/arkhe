"""Gestión, parseo e indexación de fichas temáticas curadas en Markdown."""

from pathlib import Path
import re
from typing import Any
import yaml

FICHAS_DEFAULT_DIR = Path('data/fichas')
FICHAS_EXAMPLE_DIR = Path('config/fichas')

FRONTMATTER_REGEX = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def parse_ficha_file(path: Path) -> dict[str, Any] | None:
    """Lee y parsea un archivo de ficha Markdown con frontmatter YAML."""
    if not path.is_file() or path.suffix.lower() != '.md':
        return None
    try:
        raw = path.read_text(encoding='utf-8')
    except Exception:
        return None
    
    match = FRONTMATTER_REGEX.match(raw)
    if not match:
        return None
    
    fm_text = match.group(1)
    body = raw[match.end():].strip()
    
    try:
        metadata = yaml.safe_load(fm_text)
    except Exception:
        return None
    
    if not isinstance(metadata, dict):
        return None
        
    return {
        'path': str(path),
        'filename': path.name,
        'metadata': metadata,
        'body': body,
        'full_text': raw,
    }


def load_all_fichas(directory: Path | str | None = None) -> list[dict[str, Any]]:
    """Carga todas las fichas disponibles en el directorio."""
    target_dir = Path(directory) if directory else FICHAS_DEFAULT_DIR
    if not target_dir.exists() or not any(target_dir.glob('*.md')):
        if FICHAS_EXAMPLE_DIR.exists() and any(FICHAS_EXAMPLE_DIR.glob('*.md')):
            target_dir = FICHAS_EXAMPLE_DIR
        else:
            return []
            
    fichas = []
    for p in sorted(target_dir.glob('*.md')):
        if p.name.startswith('00_'):
            continue  # Saltar plantilla base
        ficha = parse_ficha_file(p)
        if ficha:
            fichas.append(ficha)
    return fichas


def find_relevant_fichas(topic: str, criteria: str = '', directory: Path | str | None = None, limit: int = 3) -> list[dict[str, Any]]:
    """Encuentra fichas curadas relevantes para un tema y criterios dados."""
    fichas = load_all_fichas(directory)
    if not fichas:
        return []
    
    query = f"{topic} {criteria}".lower()
    scored = []
    for f in fichas:
        score = 0
        meta = f['metadata']
        f_tema = str(meta.get('tema', '')).lower()
        f_titulo = str(meta.get('titulo', '')).lower()
        keywords = [str(k).lower() for k in (meta.get('palabras_clave') or [])]
        
        for kw in keywords:
            if kw in query:
                score += 4
        if f_tema and f_tema in query:
            score += 5
        if f_titulo and any(w in query for w in f_titulo.split() if len(w) > 4):
            score += 3
        # Búsqueda también en el texto del cuerpo si no hay match directo
        if score == 0:
            words = [w for w in re.findall(r'\b[A-Za-zÀ-ÿ]{5,}\b', query)]
            matches = sum(1 for w in words if w in f['body'].lower())
            if matches >= 2:
                score = matches
                
        if score > 0:
            scored.append((score, f))
            
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:limit]]
