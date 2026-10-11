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
from datetime import datetime
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
    "hfm_weimar": {
        "nombre": "HfM Weimar – Computergestützte Musikanalyse",
        "url_base": "https://analyse.hfm-weimar.de",
        "cobertura": "Base de datos MusicXML para análisis musical computacional (HfM Weimar)",
        "formatos": ["musicxml"],
        "licencia": "licencia no especificada: uso docente con atribución",
        "atribucion": "HfM Weimar – Computergestützte Musikanalyse",
        "exportable": False,
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


def coincide_con_jrp(filename: str, composer: str = "", work: str = "") -> bool:
    """Comprueba si un archivo o entrada de HfM Weimar coincide con el Josquin Research Project.

    En la base de datos de HfM Weimar:
    - La base de datos '002' corresponde al Josquin Research Project (Stanford University).
    - Códigos de opus como Duf1004, Jos..., Ock..., Agr..., etc. proceden del corpus de JRP.
    - Obras polifónicas renacentistas de estos autores cubiertas por JRP.
    """
    fn_lower = filename.lower()
    c_lower = composer.lower()
    w_lower = work.lower()

    if "_002_" in filename or "_02_" in filename:
        return True

    jrp_opus_prefixes = ["duf", "jos", "ock", "agr", "bus", "isa", "rue", "com", "ghp", "tin"]
    for pref in jrp_opus_prefixes:
        if f"_{pref}" in fn_lower or fn_lower.startswith(pref):
            return True

    ren_composers = ["josquin", "des prez", "ockeghem", "du fay", "dufay", "agricola", "busnois", "isaac"]
    if any(rc in c_lower or rc in fn_lower for rc in ren_composers):
        return True

    return False


def buscar_en_hfm_weimar(
    query: dict[str, Any],
    destino_cache: Path | str | None = None,
    *,
    html_fuente: str | None = None,
    client_http: Any = None,
    filtrar_coincidentes_jrp: bool = False,
) -> list[dict[str, Any]]:
    """Busca y descarga partituras MusicXML reales desde la base de datos de HfM Weimar.

    Reglas de la fuente HfM Weimar:
    - Solo archivos MusicXML (.xml), NUNCA archivos .sv (Sonic Visualiser).
    - Guarda URL, fecha y atribución ('HfM Weimar – Computergestützte Musikanalyse').
    - Licencia: 'licencia no especificada: uso docente con atribución'.
    - exportable: False (no puede exportarse fuera del material de clase).
    - Prioridad JRP: si los archivos del Renacimiento coinciden con JRP, se detecta y se da prioridad a JRP.
    """
    composer_q = (query.get("composer") or "").strip().lower()
    work_q = (query.get("work") or "").strip().lower()
    headers = {"User-Agent": "Arkhé-Docente/1.0"}

    if html_fuente is None:
        import httpx
        url = "https://analyse.hfm-weimar.de/doku.php?id=notenauswahl"
        try:
            if client_http is not None:
                resp = client_http.get(url, headers=headers)
                if resp.status_code == 200:
                    html_fuente = resp.text
            else:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url, headers=headers)
                    if resp.status_code == 200:
                        html_fuente = resp.text
        except Exception:
            return []

    if not html_fuente:
        return []

    # Extraer enlaces a archivos en la base de datos
    # REGLA ESTRICTA: Solo archivos .xml, NUNCA archivos .sv
    links = []
    pattern = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
    for match in pattern.finditer(html_fuente):
        raw_href = match.group(1).strip()
        link_text = re.sub(r'<[^>]+>', '', match.group(2)).strip()

        if raw_href.lower().endswith(".sv") or (".sv" in raw_href.lower() and not raw_href.lower().endswith(".xml")):
            continue
        if not raw_href.lower().endswith(".xml"):
            continue

        if raw_href.startswith("/"):
            full_url = f"https://analyse.hfm-weimar.de{raw_href}"
        elif not raw_href.startswith("http"):
            full_url = f"https://analyse.hfm-weimar.de/{raw_href}"
        else:
            full_url = raw_href

        links.append((full_url, link_text))

    work_words = [w for w in work_q.replace("-", " ").split() if len(w) > 2]
    composer_words = [w for w in composer_q.replace("-", " ").split() if len(w) > 2]

    candidatos_items = []
    for full_url, title_text in links:
        fname = full_url.split("/")[-1]
        fname_lower = fname.lower()
        title_lower = title_text.lower()

        if composer_words:
            if not any(cw in fname_lower or cw in title_lower for cw in composer_words):
                continue
        if work_words:
            if not any(ww in fname_lower or ww in title_lower for ww in work_words):
                continue

        candidatos_items.append((full_url, title_text, fname))

    if not candidatos_items and composer_words:
        for full_url, title_text in links:
            fname = full_url.split("/")[-1]
            fname_lower = fname.lower()
            title_lower = title_text.lower()
            if any(cw in fname_lower or cw in title_lower for cw in composer_words):
                candidatos_items.append((full_url, title_text, fname))

    if not candidatos_items and not composer_words and not work_words:
        candidatos_items = [(u, t, u.split("/")[-1]) for u, t in links[:3]]

    cache_dir = Path(destino_cache) if destino_cache else Path("data/cache/partituras/hfm_weimar")
    cache_dir.mkdir(parents=True, exist_ok=True)
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    candidatos = []
    for full_url, title_text, fname in candidatos_items[:3]:
        es_jrp_match = coincide_con_jrp(fname, composer=query.get("composer", ""), work=query.get("work", ""))
        if filtrar_coincidentes_jrp and es_jrp_match:
            continue

        local_file = cache_dir / fname
        if not local_file.is_file():
            try:
                if client_http is not None:
                    f_resp = client_http.get(full_url, headers=headers)
                    if f_resp.status_code == 200:
                        local_file.write_bytes(f_resp.content)
                else:
                    import httpx
                    with httpx.Client(timeout=15.0) as client:
                        f_resp = client.get(full_url, headers=headers)
                        if f_resp.status_code == 200:
                            local_file.write_bytes(f_resp.content)
            except Exception:
                pass

        meta = {}
        if local_file.is_file():
            try:
                meta = parse_score_file(local_file)
            except Exception:
                pass

        cand_id = f"hfm-weimar-{local_file.stem}".replace(".", "-").replace(" ", "-")
        candidatos.append({
            "id": cand_id,
            "titulo": meta.get("titulo") or title_text or fname,
            "compositor": meta.get("compositor") or query.get("composer") or "HfM Weimar Database",
            "seccion": query.get("section") or "",
            "fuente": "HfM Weimar – Computergestützte Musikanalyse",
            "url": full_url,
            "path": str(local_file) if local_file.is_file() else "",
            "archivo": fname,
            "edicion": "Computergestützte Musikanalyse (HfM Weimar)",
            "atribucion": "HfM Weimar – Computergestützte Musikanalyse",
            "fecha": fecha_hoy,
            "licencia": "licencia no especificada: uso docente con atribución",
            "exportable": False,
            "formato": "musicxml",
            "voces": meta.get("voces", []),
            "compases": meta.get("compases", 0),
            "claves": meta.get("claves", []),
            "mensuracion": meta.get("mensuracion", "No especificada"),
            "verificado": False,
            "coincide_jrp": es_jrp_match,
        })

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

    if len(candidatos) >= 3:
        return candidatos[:3]

    # 3. HfM Weimar – Computergestützte Musikanalyse (MusicXML, opcional)
    try:
        hfm_cands = buscar_en_hfm_weimar(query, destino_cache=destino_cache, filtrar_coincidentes_jrp=True)
        candidatos.extend(hfm_cands)
    except Exception:
        pass

    return candidatos[:3]
