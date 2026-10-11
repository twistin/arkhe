"""Gestión y consulta de fichas modulares de contenido pedagógico."""

from pathlib import Path
import re
from typing import Any
import yaml

FICHAS_DEFAULT_DIR = Path('data/fichas')
FICHAS_CONFIG_DIR = Path('config/fichas')

_POLYPHONY_REGEXES = (
    re.compile(r'\bpolifon[ií]a\b', re.IGNORECASE),
    re.compile(r'\bsiglo\s*xv\b|\bs\.\s*xv\b|\b15th\s*century\b', re.IGNORECASE),
    re.compile(r'\bcantus\s+firmus\b', re.IGNORECASE),
    re.compile(r'\bmisa\s+c[ií]clica\b', re.IGNORECASE),
    re.compile(r'\bmisa\s+parodia\b', re.IGNORECASE),
    re.compile(r'\bmisa\s+par[aá]frasis\b', re.IGNORECASE),
    re.compile(r'\bdu\s*fay\b|\bdufay\b', re.IGNORECASE),
    re.compile(r'\bockeghem\b|\bbinchois\b|\bbusno[iy]s\b', re.IGNORECASE),
    re.compile(r'\bse\s+la\s+face\s+ay\s+pale\b', re.IGNORECASE),
    re.compile(r'\bl[\'\’]?homme\s+arm[eé]\b', re.IGNORECASE),
)

_EGYPT_REGEXES = (
    re.compile(r'\begipto\b|\begipci[ao]s?\b', re.IGNORECASE),
    re.compile(r'\bhathor\b|\bsistro\b|\bsistrum\b|\bmenat\b', re.IGNORECASE),
    re.compile(r'\bquironimia\b|\bnebamun\b|\btutankam[oó]n\b', re.IGNORECASE),
)

_NTAM_REGEXES = (
    re.compile(r'\bntam\b', re.IGNORECASE),
    re.compile(r'\bnuevas\s+tecnolog[ií]as\b', re.IGNORECASE),
    re.compile(r'\bnovas\s+tecnolox[ií]as\b', re.IGNORECASE),
)


def _resolve_fichas_dirs(directory: Path | str | None = None) -> list[Path]:
    """Resuelve directorios de búsqueda de fichas (prioridad: directory, data/fichas, config/fichas)."""
    dirs: list[Path] = []
    if directory:
        target = Path(directory)
        if target.is_dir():
            dirs.append(target)
    if FICHAS_DEFAULT_DIR.is_dir() and FICHAS_DEFAULT_DIR not in dirs:
        dirs.append(FICHAS_DEFAULT_DIR)
    if FICHAS_CONFIG_DIR.is_dir() and FICHAS_CONFIG_DIR not in dirs:
        dirs.append(FICHAS_CONFIG_DIR)
    return dirs


def load_all_fichas(directory: Path | str | None = None) -> list[dict[str, Any]]:
    """Carga todas las fichas disponibles en los directorios configurados."""
    dirs = _resolve_fichas_dirs(directory)
    if not dirs:
        return []

    fichas_by_id: dict[str, dict[str, Any]] = {}
    for d in dirs:
        for yaml_file in sorted(d.glob('*.yaml')):
            if yaml_file.name.endswith('.example.yaml'):
                continue
            try:
                raw = yaml_file.read_text(encoding='utf-8')
                data = yaml.safe_load(raw)
            except Exception:
                continue
            if isinstance(data, dict) and 'id' in data:
                f_id = str(data['id'])
                if f_id not in fichas_by_id:
                    data['_source_file'] = str(yaml_file)
                    fichas_by_id[f_id] = data

    return list(fichas_by_id.values())


def get_ficha(ficha_id: str, directory: Path | str | None = None) -> dict[str, Any] | None:
    """Busca una ficha por su ID exacto."""
    fichas = load_all_fichas(directory)
    for f in fichas:
        if f.get('id') == ficha_id:
            return f
    return None


def is_ficha_verified(ficha: dict[str, Any] | None) -> bool:
    """Comprueba si una ficha está marcada como verificada por el profesor."""
    if not ficha or not isinstance(ficha, dict):
        return False
    return bool(ficha.get('verificado') is True)


def get_ficha_for_topic(topic: str, directory: Path | str | None = None) -> dict[str, Any] | None:
    """Obtiene la ficha correspondiente a un tema de estudio según patrones canónicos."""
    if not topic:
        return None
    t = str(topic).strip()

    # 1. Comprobación de polifonía del siglo XV
    if any(rx.search(t) for rx in _POLYPHONY_REGEXES):
        return get_ficha('polifonia_xv', directory)

    # 2. Comprobación de Antiguo Egipto
    if any(rx.search(t) for rx in _EGYPT_REGEXES):
        return get_ficha('egipto', directory)

    # 3. Comprobación de NTAM
    if any(rx.search(t) for rx in _NTAM_REGEXES):
        return get_ficha('ntam', directory)

    # 4. Búsqueda por coincidencia en el campo 'tema'
    fichas = load_all_fichas(directory)
    for f in fichas:
        tema = str(f.get('tema') or '').lower()
        if tema and tema in t.lower():
            return f

    return None


def get_ficha_for_run(run: dict[str, Any], directory: Path | str | None = None) -> dict[str, Any] | None:
    """Determina si un run tiene asignada una ficha temática."""
    if not run or not isinstance(run, dict):
        return None

    # Si el run ya tiene ficha inyectada, devolverla
    if 'ficha' in run and isinstance(run['ficha'], dict):
        return run['ficha']

    req = run.get('request') or {}
    ped = req.get('pedagogy') or {}
    group = ped.get('group') or {}
    unit = ped.get('unit') or {}
    subj = str(req.get('subject') or group.get('subject_id') or '')
    q = str(run.get('original_topic') or req.get('original_topic') or req.get('question') or '')
    disp = str(run.get('display_title') or req.get('display_title') or '')
    crit = str(ped.get('teacher_criteria') or '')

    combined = f"{disp} {q} {crit} {subj} {group.get('name', '')} {unit.get('id', '')} {ped.get('unit_id', '')}"

    return get_ficha_for_topic(combined, directory)
