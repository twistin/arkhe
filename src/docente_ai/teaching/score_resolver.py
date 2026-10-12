"""Servicio de resolución en cascada de peticiones musicales (music_requests).

Orden de resolución:
1. Catálogo local data/ejemplos/ (y fallback config/ejemplos/).
2. Carpeta de importación del profesor (Conocimiento/Partituras/).
3. Repositorios abiertos con consentimiento explícito (JRP, KernScores, CPDL, music21).
"""

from pathlib import Path
from typing import Any
import yaml

from docente_ai.teaching.ejemplos import load_all_ejemplos, EJEMPLOS_DEFAULT_DIR, EJEMPLOS_EXAMPLE_DIR
from docente_ai.teaching.score_parser import parse_score_file
from docente_ai.teaching.score_repositories import buscar_en_repositorios

SCORE_IMPORT_DIR = Path('Conocimiento/Partituras')
SCORE_EXAMPLE_IMPORT_DIR = Path('config/partituras')


def _normalizar_texto(texto: str | None) -> str:
    if not texto:
        return ''
    return ' '.join(texto.lower().replace('-', ' ').replace('_', ' ').split())


def _coincide_ejemplo(request: dict[str, Any], ejemplo: dict[str, Any]) -> bool:
    req_comp = _normalizar_texto(request.get('composer'))
    req_work = _normalizar_texto(request.get('work'))
    req_sec = _normalizar_texto(request.get('section'))
    req_tech = _normalizar_texto(request.get('technique'))

    ej_comp = _normalizar_texto(ejemplo.get('compositor'))
    ej_work = _normalizar_texto(ejemplo.get('obra') or ejemplo.get('titulo'))
    ej_sec = _normalizar_texto(ejemplo.get('seccion'))
    ej_tech = _normalizar_texto(ejemplo.get('tecnica'))

    # Coincidencia por compositor si ambos están presentes
    if req_comp and ej_comp:
        if req_comp not in ej_comp and ej_comp not in req_comp:
            return False

    # Coincidencia por obra
    if req_work and ej_work:
        palabras_req = [p for p in req_work.split() if len(p) > 2]
        if not any(p in ej_work for p in palabras_req):
            return False

    # Coincidencia por sección (si se especificó en ambos)
    if req_sec and ej_sec and req_sec not in ej_sec and ej_sec not in req_sec:
        return False

    # Coincidencia por técnica (si se especificó en ambos)
    if req_tech and ej_tech and req_tech != ej_tech:
        return False

    return True


def escanear_partituras_locales(directorio: Path | str | None = None) -> list[dict[str, Any]]:
    """Escanea la carpeta de importación del profesor parseando cabeceras de partituras."""
    target_dir = Path(directorio) if directorio else SCORE_IMPORT_DIR
    if not target_dir.exists() or not any(target_dir.iterdir()):
        if SCORE_EXAMPLE_IMPORT_DIR.exists() and any(SCORE_EXAMPLE_IMPORT_DIR.iterdir()):
            target_dir = SCORE_EXAMPLE_IMPORT_DIR
        else:
            return []

    candidatos = []
    extensiones_validas = {'.xml', '.musicxml', '.mxl', '.mei', '.krn', '.abc'}
    for p in sorted(target_dir.rglob('*')):
        if p.is_file() and p.suffix.lower() in extensiones_validas:
            try:
                parsed = parse_score_file(p)
                candidatos.append(parsed)
            except Exception:
                continue
    return candidatos


def es_peticion_teoria_calculable(request: dict[str, Any]) -> bool:
    """Detecta si una petición musical pide tetracordos, géneros, escalas o modos calculables."""
    textos = [
        str(request.get('work') or ''),
        str(request.get('technique') or ''),
        str(request.get('description') or ''),
        str(request.get('activity_title') or ''),
        str(request.get('section') or ''),
        str(request.get('composer') or ''),
    ]
    combinado = ' '.join(textos).lower()
    terminos = [
        'tetracordo', 'tetracordos', 'tetrachord', 'géneros', 'generos', 'género', 'genero',
        'enarmónico', 'enarmonico', 'cuartos de tono', 'diesis', 'diatonico', 'diatónico',
        'cromatico', 'cromático', 'gran sistema perfecto', 'sistema perfecto'
    ]
    return any(t in combinado for t in terminos)


def resolver_peticion_musical(
    request: dict[str, Any],
    *,
    directorio_ejemplos: Path | str | None = None,
    directorio_partituras: Path | str | None = None,
    con_repositorios_abiertos: bool = False,
    descartes: list[str] | None = None,
    proveedor_test: Any = None
) -> dict[str, Any]:
    """Resuelve una petición musical individual según el orden estricto de resolución."""
    req_id = request.get('id', 'MR1')
    descartes_set = set(descartes or [])

    # 0. Peticiones de teoría musical calculables (tetracordos, géneros, escalas o modos)
    if es_peticion_teoria_calculable(request):
        from docente_ai.music.greek import asegurar_archivo_partitura_tres_generos
        archivo = asegurar_archivo_partitura_tres_generos()
        ejemplo_teoria = {
            'id': 'teoria-tetracordos-tres-generos',
            'titulo': 'Tetracordo descendente mi–si en los tres géneros (diatónico, cromático y enarmónico)',
            'compositor': 'Teoría musical griega (Aristóxeno / Ptolomeo)',
            'obra': request.get('work') or 'Tetracordo descendente mi–si',
            'seccion': request.get('section') or 'Tres géneros: diatónico, cromático y enarmónico',
            'compases': '1-3',
            'tecnica': 'Tetracordos (diatónico, cromático, enarmónico con cuartos de tono)',
            'voces': [{'id': 'Tetracordos', 'nombre': 'Tetracordo'}],
            'archivo': archivo,
            'fuente': 'Calculado a partir de la teoría',
            'licencia': 'Dominio público (teoría musical)',
            'calculado_teoria': True,
            'verificado': True,
            'frecuencias_hz': [
                329.63, 293.66, 261.63, 246.94,  # Diatónico (E4, D4, C4, B3)
                329.63, 277.18, 261.63, 246.94,  # Cromático (E4, C#4, C4, B3)
                329.63, 261.63, 254.18, 246.94,  # Enarmónico (E4, C4, B3+diesis, B3)
            ],
            'nota_analisis': 'Generado deterministamente a partir de la teoría con music21; frecuencias exactas para afinación Web Audio.',
        }
        return {
            'request_id': req_id,
            'status': 'resuelto_catalogo',
            'origen': 'calculado_teoria',
            'ejemplo': ejemplo_teoria,
            'verificado': True,
            'candidatos': [],
        }

    # 1. Catálogo local data/ejemplos/
    ejemplos_locales = load_all_ejemplos(directorio_ejemplos)
    for ej in ejemplos_locales:
        if ej.get('id') not in descartes_set and _coincide_ejemplo(request, ej):
            return {
                'request_id': req_id,
                'status': 'resuelto_catalogo',
                'origen': 'catalogo_local',
                'ejemplo': ej,
                'verificado': bool(ej.get('verificado', False)),
                'candidatos': [],
            }

    # 2. Carpeta de partituras del profesor
    partituras_locales = escanear_partituras_locales(directorio_partituras)
    candidatos_locales = []
    for part in partituras_locales:
        part_id = part.get('archivo', part.get('path'))
        if part_id not in descartes_set and _coincide_ejemplo(request, part):
            candidato = dict(part)
            candidato['id'] = f"local-{part_id}"
            candidato['fuente'] = "Carpeta de partituras del profesor"
            candidato['licencia'] = "Partitura aportada por el profesor"
            candidato['verificado'] = False
            candidato['compases_rango'] = "1-8"
            candidatos_locales.append(candidato)

    if candidatos_locales:
        return {
            'request_id': req_id,
            'status': 'candidatos_pendientes',
            'origen': 'partituras_profesor',
            'ejemplo': None,
            'verificado': False,
            'candidatos': candidatos_locales[:3],
        }

    # 3. Repositorios abiertos (solo si con_repositorios_abiertos es True)
    if con_repositorios_abiertos:
        candidatos_remotos = buscar_en_repositorios(request, proveedor_test=proveedor_test)
        candidatos_filtrados = [
            c for c in candidatos_remotos if c.get('id') not in descartes_set
        ]
        if candidatos_filtrados:
            return {
                'request_id': req_id,
                'status': 'candidatos_pendientes',
                'origen': 'repositorios_abiertos',
                'ejemplo': None,
                'verificado': False,
                'candidatos': candidatos_filtrados[:3],
            }

    # Sin resolver
    return {
        'request_id': req_id,
        'status': 'sin_resolver',
        'origen': None,
        'ejemplo': None,
        'verificado': False,
        'candidatos': [],
    }


def resolver_todas_las_peticiones(
    requests: list[dict[str, Any]],
    *,
    directorio_ejemplos: Path | str | None = None,
    directorio_partituras: Path | str | None = None,
    con_repositorios_abiertos: bool = False,
    descartes_map: dict[str, list[str]] | None = None,
    proveedor_test: Any = None
) -> list[dict[str, Any]]:
    """Resuelve en bloque una lista de peticiones musicales."""
    descartes_map = descartes_map or {}
    resultados = []
    for req in requests:
        req_id = req.get('id', '')
        descartes = descartes_map.get(req_id, [])
        res = resolver_peticion_musical(
            req,
            directorio_ejemplos=directorio_ejemplos,
            directorio_partituras=directorio_partituras,
            con_repositorios_abiertos=con_repositorios_abiertos,
            descartes=descartes,
            proveedor_test=proveedor_test
        )
        resultados.append(res)
    return resultados


def usar_candidato_como_ejemplo(
    request: dict[str, Any],
    candidato: dict[str, Any],
    *,
    rango_compases: str = "1-8",
    voz_resaltar: str | None = None,
    directorio_destino: Path | str | None = None
) -> dict[str, Any]:
    """Guarda un candidato en data/ejemplos/ con verificado: true y los metadatos elegidos."""
    target_dir = Path(directorio_destino) if directorio_destino else EJEMPLOS_DEFAULT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    yaml_file = target_dir / 'ejemplos.yaml'
    existentes = []
    if yaml_file.is_file():
        try:
            existentes = yaml.safe_load(yaml_file.read_text(encoding='utf-8')) or []
        except Exception:
            existentes = []

    nuevo_id = f"ejemplo-{candidato.get('id', 'partitura')}".replace('/', '-').replace(' ', '-')
    # Copiar o referenciar archivo si procede
    archivo_nombre = candidato.get('archivo', f"{nuevo_id}.musicxml")
    if candidato.get('path') and Path(candidato['path']).is_file():
        src_path = Path(candidato['path'])
        dest_path = target_dir / src_path.name
        if not dest_path.is_file() or dest_path.resolve() != src_path.resolve():
            dest_path.write_bytes(src_path.read_bytes())
        archivo_nombre = src_path.name

    nuevo_ejemplo = {
        'id': nuevo_id,
        'titulo': candidato.get('titulo') or request.get('work') or 'Ejemplo musical',
        'compositor': candidato.get('compositor') or request.get('composer') or 'Anónimo',
        'obra': request.get('work') or candidato.get('titulo', ''),
        'seccion': request.get('section') or candidato.get('seccion', ''),
        'compases': rango_compases,
        'tecnica': request.get('technique', ''),
        'voces': candidato.get('voces', []),
        'archivo': archivo_nombre,
        'fuente': candidato.get('fuente', 'Importación del profesor'),
        'licencia': candidato.get('licencia', 'Licencia libre / Dominio público'),
        'edicion': candidato.get('edicion', ''),
        'url': candidato.get('url', ''),
        'verificado': True,
        'voz_resaltada': voz_resaltar or request.get('voice', ''),
        'nota_analisis': request.get('description', ''),
    }

    # Si hay voz resaltada, marcarla en las voces
    if voz_resaltar:
        for v in nuevo_ejemplo['voces']:
            if voz_resaltar.lower() in v.get('nombre', '').lower() or voz_resaltar.lower() in v.get('id', '').lower():
                v['es_cantus_firmus'] = True
                v['nota'] = request.get('description', 'Voz destacada en análisis')

    # Añadir o reemplazar en existentes
    existentes = [e for e in existentes if e.get('id') != nuevo_id]
    existentes.append(nuevo_ejemplo)

    yaml_file.write_text(yaml.safe_dump(existentes, allow_unicode=True, sort_keys=False), encoding='utf-8')
    return nuevo_ejemplo
