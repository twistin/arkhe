"""Conectores y metadatos para repositorios de partituras.

Implementaciones reales:
1. Corpus de music21 (instalado en local, sin red):
   - Búsqueda real en el corpus local de music21 por compositor y título.
   - Extrae metadatos reales y devuelve la ruta del archivo real en el sistema.

2. Josquin Research Project (JRP) (repositorio público en GitHub):
   - Descarga real de archivos Humdrum (**kern) desde github.com/josquin-research-project/jrp-scores.
   - Guarda la URL exacta del archivo descargado y extrae metadatos.

Otros repositorios (KernScores, CPDL):
- Si se solicitan pero no están implementados, informan que no están disponibles todavía
  y NUNCA devuelven candidatos inventados ni simulados en código de producción.

Los proveedores simulados solo están permitidos en tests mediante fixtures o inyección de dependencias.
"""

from pathlib import Path
from typing import Any
import re
import urllib.parse

from docente_ai.teaching.score_parser import parse_score_file

REPOSITORIOS_METADATOS = {
    "music21": {
        "nombre": "Corpus de music21",
        "url_base": "https://github.com/cuthbertLab/music21/tree/master/music21/corpus",
        "cobertura": "Repertorio musicológico local: Josquin, corales de Bach, Trecento, canciones tradicionales",
        "formatos": ["musicxml", "mxl", "humdrum", "abc"],
        "licencia": "BSD 3-Clause / Dominio público",
        "edicion": "Michael Scott Cuthbert et al. (MIT)",
        "disponible": True,
    },
    "jrp": {
        "nombre": "Josquin Research Project",
        "url_base": "https://raw.githubusercontent.com/josquin-research-project/jrp-scores/main",
        "cobertura": "Polifonía de los siglos XV y XVI (Josquin, Ockeghem, Du Fay, Agricola)",
        "formatos": ["humdrum"],
        "licencia": "CC BY-NC 4.0",
        "edicion": "Jesse Rodin et al. (Stanford University)",
        "disponible": True,
    },
    "kernscores": {
        "nombre": "KernScores",
        "url_base": "http://kernscores.stanford.edu",
        "cobertura": "Archivo digital Humdrum CCARH (Stanford University)",
        "formatos": ["humdrum"],
        "licencia": "Dominio público / Uso académico libre",
        "edicion": "CCARH",
        "disponible": False,
        "mensaje": "Repositorio no disponible todavía",
    },
    "cpdl": {
        "nombre": "Choral Public Domain Library (CPDL)",
        "url_base": "https://www.cpdl.org",
        "cobertura": "Partituras corales de dominio público",
        "formatos": ["musicxml", "mxl", "pdf"],
        "licencia": "CPDL / Dominio público",
        "edicion": "Comunidad CPDL",
        "disponible": False,
        "mensaje": "Repositorio no disponible todavía",
    },
}


def buscar_en_corpus_music21(query: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    """Busca obras reales en el corpus local de music21 por compositor y obra."""
    from docente_ai.music import get_music21
    m21 = get_music21()

    composer_q = (query.get("composer") or "").strip()
    work_q = (query.get("work") or "").strip()
    section_q = (query.get("section") or "").strip()

    search_terms = []
    if composer_q:
        search_terms.append(composer_q)
    if work_q:
        search_terms.append(work_q)
    elif section_q:
        search_terms.append(section_q)

    if not search_terms:
        return []

    entries = []
    # 1. Búsqueda específica por compositor si se indicó
    if composer_q:
        try:
            entries = list(m21.corpus.search(composer_q, "composer"))
        except Exception:
            entries = []

    # 2. Si no hubo resultados o además hay obra, buscar término general
    if not entries or work_q:
        term = f"{composer_q} {work_q}".strip() if (composer_q and work_q) else (work_q or composer_q)
        try:
            extra = list(m21.corpus.search(term))
            for ex in extra:
                if ex not in entries:
                    entries.append(ex)
        except Exception:
            pass

    # Si hay término de obra, filtrar / ordenar por relevancia
    if work_q and entries:
        norm_work = work_q.lower()
        coincidentes = []
        otros = []
        for e in entries:
            name_str = f"{e.sourcePath}".lower()
            title_str = (getattr(e.metadata, 'title', '') or '').lower() if hasattr(e, 'metadata') and e.metadata else ''
            if norm_work in name_str or norm_work in title_str or any(w in name_str for w in norm_work.split() if len(w) > 3):
                coincidentes.append(e)
            else:
                otros.append(e)
        entries = coincidentes + otros

    candidatos = []
    for entry in entries[:limit]:
        try:
            work_path = m21.corpus.getWork(entry.sourcePath)
            if not work_path or not Path(work_path).is_file():
                continue
            path_obj = Path(work_path)
            meta = parse_score_file(path_obj)
            
            # Si el parser rápido no extrajo compositor/título con precisión, consultar RichMetadata
            if hasattr(entry, 'metadata') and entry.metadata:
                if entry.metadata.composer and meta.get("compositor") in ("", "Anónimo"):
                    meta["compositor"] = entry.metadata.composer
                if entry.metadata.title and meta.get("titulo") in ("", "Sin título"):
                    meta["titulo"] = entry.metadata.title

            cand_id = f"m21-{path_obj.stem}".replace(" ", "-").replace(".", "-")
            candidatos.append({
                "id": cand_id,
                "titulo": meta.get("titulo") or path_obj.stem,
                "compositor": meta.get("compositor") or composer_q or "music21 corpus",
                "seccion": section_q or meta.get("titulo", ""),
                "fuente": "Corpus de music21",
                "url": f"file://{path_obj}",
                "path": str(path_obj),
                "archivo": path_obj.name,
                "edicion": "music21 corpus (local)",
                "licencia": "BSD 3-Clause / Dominio público",
                "formato": meta.get("formato", path_obj.suffix.lstrip(".")),
                "voces": meta.get("voces", []),
                "compases": meta.get("compases", 0),
                "claves": meta.get("claves", []),
                "mensuracion": meta.get("mensuracion", "No especificada"),
                "verificado": False,
            })
        except Exception:
            continue

    return candidatos


def buscar_en_jrp(query: dict[str, Any], destino_cache: Path | str | None = None) -> list[dict[str, Any]]:
    """Descarga de forma real partituras Humdrum desde el repositorio GitHub público de JRP."""
    import httpx
    
    composer_q = (query.get("composer") or "").lower()
    work_q = (query.get("work") or "").lower()
    
    # Mapeo de compositores en JRP GitHub: Jos, Ock, Duf, Agr, Bus, Isa, Rue, etc.
    folder_prefix = None
    if "josquin" in composer_q or "des prez" in composer_q:
        folder_prefix = "Jos"
    elif "ockeghem" in composer_q:
        folder_prefix = "Ock"
    elif "du fay" in composer_q or "dufay" in composer_q:
        folder_prefix = "Duf"
    elif "agricola" in composer_q:
        folder_prefix = "Agr"
    elif "busnois" in composer_q or "busnoys" in composer_q:
        folder_prefix = "Bus"

    if not folder_prefix:
        return []

    # Consultar API de contenidos de GitHub para la carpeta del compositor
    api_url = f"https://api.github.com/repos/josquin-research-project/jrp-scores/contents/{folder_prefix}"
    headers = {"User-Agent": "Arkhé-Docente/1.0"}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(api_url, headers=headers)
            if resp.status_code != 200:
                return []
            archivos = resp.json()
    except Exception:
        return []

    if not isinstance(archivos, list):
        return []

    # Filtrar por obra si se especificó
    candidatos_items = []
    work_words = [w for w in work_q.replace("-", " ").split() if len(w) > 2]
    
    for item in archivos:
        fname = item.get("name", "")
        if not fname.endswith(".krn"):
            continue
        fname_lower = fname.lower()
        if work_words:
            if any(w in fname_lower for w in work_words):
                candidatos_items.append(item)
        else:
            candidatos_items.append(item)

    if not candidatos_items:
        candidatos_items = [it for it in archivos if it.get("name", "").endswith(".krn")][:3]

    cache_dir = Path(destino_cache) if destino_cache else Path("data/cache/partituras/jrp")
    cache_dir.mkdir(parents=True, exist_ok=True)

    candidatos = []
    for item in candidatos_items[:3]:
        raw_url = item.get("download_url")
        fname = item.get("name")
        if not raw_url or not fname:
            continue
        local_file = cache_dir / fname
        try:
            if not local_file.is_file():
                with httpx.Client(timeout=15.0) as client:
                    file_resp = client.get(raw_url, headers=headers)
                    if file_resp.status_code == 200:
                        local_file.write_bytes(file_resp.content)
            
            if local_file.is_file():
                meta = parse_score_file(local_file)
                candidatos.append({
                    "id": f"jrp-{local_file.stem}".replace(".", "-"),
                    "titulo": meta.get("titulo") or fname,
                    "compositor": meta.get("compositor") or query.get("composer") or "Josquin Research Project",
                    "seccion": query.get("section") or "",
                    "fuente": "Josquin Research Project",
                    "url": raw_url,
                    "path": str(local_file),
                    "archivo": fname,
                    "edicion": "Jesse Rodin et al. (Stanford University)",
                    "licencia": "CC BY-NC 4.0",
                    "formato": "humdrum",
                    "voces": meta.get("voces", []),
                    "compases": meta.get("compases", 0),
                    "claves": meta.get("claves", []),
                    "mensuracion": meta.get("mensuracion", "No especificada"),
                    "verificado": False,
                })
        except Exception:
            continue

    return candidatos


def buscar_en_repositorios(
    query: dict[str, Any],
    *,
    proveedor_test: Any = None,
    destino_cache: Path | str | None = None
) -> list[dict[str, Any]]:
    """Busca en repositorios abiertos reales.

    NUNCA devuelve candidatos simulados o inventados en código de producción.
    Si un repositorio no está implementado (como KernScores o CPDL), no inventa datos.
    El parámetro proveedor_test solo se utiliza para inyección de dependencias en tests unitarios.
    """
    if proveedor_test is not None:
        if callable(proveedor_test):
            return proveedor_test(query)
        if isinstance(proveedor_test, list):
            return proveedor_test

    candidatos = []

    # 1. Corpus de music21 (instalado localmente)
    try:
        m21_cands = buscar_en_corpus_music21(query, limit=3)
        candidatos.extend(m21_cands)
    except Exception:
        pass

    if len(candidatos) >= 3:
        return candidatos[:3]

    # 2. Josquin Research Project (GitHub público, descarga real)
    try:
        jrp_cands = buscar_en_jrp(query, destino_cache=destino_cache)
        candidatos.extend(jrp_cands)
    except Exception:
        pass

    return candidatos[:3]
