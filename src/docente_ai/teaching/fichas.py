"""Gestión y consulta de fichas modulares de contenido pedagógico."""

from pathlib import Path
import re
from typing import Any
import yaml

FICHAS_DEFAULT_DIR = Path('data/fichas')
FICHAS_CONFIG_DIR = Path('config/fichas')

# Reglas estrictas de coincidencia: requieren coherencia de periodo y materia.
# Prohibido usar palabras sueltas como 'polifonía' que causan cruces de periodos.
_PERIODOS_INCOMPATIBLES_SIGLO_XV = re.compile(
    r'\bsiglo\s*xvi\b|\bs\.\s*xvi\b|\b16th\s*century\b|\brenacimiento\b|\brenacentista\b|'
    r'\bpalestrina\b|\blassus\b|\bvictoria\b|\bmorales\b|\bguerrero\b',
    re.IGNORECASE
)

_POLYPHONY_XV_REGEXES = (
    re.compile(r'\bsiglo\s*xv\b|\bs\.\s*xv\b|\b15th\s*century\b', re.IGNORECASE),
    re.compile(r'\bdu\s*fay\b|\bdufay\b|\bockeghem\b|\bbinchois\b|\bbusno[iy]s\b', re.IGNORECASE),
    re.compile(r'\bse\s+la\s+face\s+ay\s+pale\b', re.IGNORECASE),
)

_EGYPT_REGEXES = (
    re.compile(r'\begipto\b|\begipci[ao]s?\b', re.IGNORECASE),
    re.compile(r'\bhathor\b|\bsistro\b|\bsistrum\b|\bmenat\b', re.IGNORECASE),
    re.compile(r'\bquironimia\b|\bnebamun\b|\btutankam[oó]n\b', re.IGNORECASE),
)

_NTAM_REGEXES = (
    re.compile(r'\bntam\b', re.IGNORECASE),
    re.compile(r'\bnuevas\s+tecnolog[ií]as\b|\bnovas\s+tecnolox[ií]as\b', re.IGNORECASE),
)

_GREECE_REGEXES = (
    re.compile(r'\bgrecia\b|\bgrieg[ao]s?\b', re.IGNORECASE),
    re.compile(r'\bseikilos\b|\bepitafio\b', re.IGNORECASE),
    re.compile(r'\btetracordo\b|\barist[oó]xeno\b|\bptolomeo\b', re.IGNORECASE),
    re.compile(r'\bmonocordio\b|\bsistema\s+perfecto\b', re.IGNORECASE),
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


def verificar_ficha(
    ficha_id: str,
    verificado_por: str = 'profesor',
    directory: Path | str | None = None,
) -> dict[str, Any] | None:
    """Acción explícita de UI del profesor: verifica una ficha y registra verificado_por y verificado_en."""
    from datetime import datetime, timezone

    ficha = get_ficha(ficha_id, directory=directory)
    if not ficha:
        return None

    ficha['verificado'] = True
    ficha['verificado_por'] = verificado_por
    ficha['verificado_en'] = datetime.now(timezone.utc).isoformat()

    source_file = ficha.get('_source_file')
    target_path = Path(source_file) if source_file else Path('config/fichas') / f"{ficha_id}.yaml"

    data_to_save = {k: v for k, v in ficha.items() if k != '_source_file'}
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        yaml.safe_dump(data_to_save, sort_keys=False, allow_unicode=True),
        encoding='utf-8',
    )
    return ficha


def listar_fichas_aplicables(
    topic: str,
    criteria: str = "",
    subject: str = "",
    directory: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Lista todas las fichas temáticas aplicables a un tema y periodo específicos.
    Permite que la UI muestre al profesor las fichas que se utilizarán, con opción de quitarlas."""
    if not topic:
        return []
    texto_eval = f"{topic} {criteria} {subject}".strip()

    candidatas = []
    # 1. Polifonía del siglo XV
    if not _PERIODOS_INCOMPATIBLES_SIGLO_XV.search(texto_eval):
        if any(rx.search(texto_eval) for rx in _POLYPHONY_XV_REGEXES):
            f = get_ficha('polifonia_xv', directory)
            if f:
                candidatas.append(f)

    # 2. Antiguo Egipto
    if any(rx.search(texto_eval) for rx in _EGYPT_REGEXES):
        f = get_ficha('egipto', directory)
        if f:
            candidatas.append(f)

    # 3. NTAM
    if any(rx.search(texto_eval) for rx in _NTAM_REGEXES):
        f = get_ficha('ntam', directory)
        if f:
            candidatas.append(f)

    # 4. Grecia Antigua
    if any(rx.search(texto_eval) for rx in _GREECE_REGEXES):
        f = get_ficha('glosario_griego', directory)
        if f:
            candidatas.append(f)

    # 5. Coincidencia declarada en otras fichas por tema exacto con límites de palabra
    fichas = load_all_fichas(directory)
    vistas = {c['id'] for c in candidatas}
    periodos_defecto = {
        'polifonia_xv': 'Siglo XV',
        'egipto': 'Antigüedad',
        'ntam': 'Música contemporánea',
        'glosario_griego': 'Antigüedad',
        'cronologia_autores': 'Antigüedad a Edad Media',
    }
    for f in fichas:
        fid = f.get('id')
        if fid in vistas or fid == 'cronologia_autores':
            continue
        if fid == 'polifonia_xv' and _PERIODOS_INCOMPATIBLES_SIGLO_XV.search(texto_eval):
            continue
        f_tema = str(f.get('tema') or '').strip().lower()
        f_periodo = str(f.get('periodo') or periodos_defecto.get(fid, '')).strip().lower()
        if 'siglo xv' in f_periodo and _PERIODOS_INCOMPATIBLES_SIGLO_XV.search(texto_eval):
            continue
        if f_tema and re.search(rf'\b{re.escape(f_tema)}\b', texto_eval, re.IGNORECASE):
            candidatas.append(f)
            vistas.add(fid)

    return candidatas


def get_ficha_for_topic(
    topic: str,
    directory: Path | str | None = None,
    fichas_excluidas: list[str] | set[str] | None = None,
) -> dict[str, Any] | None:
    """Obtiene la ficha correspondiente a un tema respetando periodo y exclusiones."""
    excluidas = set(fichas_excluidas or [])
    aplicables = listar_fichas_aplicables(topic, directory=directory)
    for f in aplicables:
        if f.get('id') not in excluidas:
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
    fichas_excluidas = req.get('fichas_excluidas') or ped.get('fichas_excluidas')
    return get_ficha_for_topic(combined, directory, fichas_excluidas=fichas_excluidas)
