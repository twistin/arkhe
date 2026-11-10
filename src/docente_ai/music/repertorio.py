"""Catálogo de repertorio real disponible para ejemplos musicales.

El catálogo solo contiene obras cuyos archivos existen en corpus libres instalados
(corpus de music21). Los metadatos (compositor, obra, movimiento, voces) se leen de
los propios archivos; nunca los escribe el modelo de lenguaje. El modelo solo puede
elegir obras de este catálogo por su identificador, de modo que cada ejemplo musical
de una propuesta corresponde a una partitura real y comprobable.

El índice se genera con ``construir_indice_corpus()`` y se guarda en
``src/docente_ai/music/datos/repertorio_corpus.json`` (solo metadatos, ninguna nota musical).
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

INDICE_PATH = Path(__file__).resolve().parent / 'datos' / 'repertorio_corpus.json'

EDICION_CORPUS = 'Corpus libre de music21'

# Palabras que identifican géneros en las indicaciones del profesor o en el tema.
GENEROS_PALABRAS = {
    'misa': ('misa', 'missa', 'mass', 'kyrie', 'gloria', 'credo', 'sanctus', 'agnus', 'parodia', 'cantus firmus'),
    'chanson': ('chanson', 'canción francesa', 'cancion francesa'),
    'madrigal': ('madrigal',),
    'motete': ('motete', 'motet'),
    'motete isorrítmico': ('isorritm', 'ars nova', 'motete'),
    'canción polifónica': ('ars nova', 'trecento', 'balada', 'ballata', 'caccia'),
}

MOVIMIENTOS_MISA = ('Kyrie', 'Gloria', 'Credo', 'Sanctus', 'Benedictus', 'Agnus')

# Carpetas del corpus cuyo texto cantado procede de OCR con errores: se muestran sin letra.
CORPUS_LETRA_NO_FIABLE = ('monteverdi',)


def letra_no_fiable(ruta: Path | str) -> bool:
    """True si la partitura pertenece a una colección del corpus con la letra mal reconocida."""
    partes = Path(ruta).parts
    return 'corpus' in partes and any(c in partes for c in CORPUS_LETRA_NO_FIABLE)


def _sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize('NFKD', texto or '')
    return ''.join(c for c in texto if not unicodedata.combining(c)).lower()


def _slug(texto: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', _sin_tildes(texto)).strip('-')


def _corpus_dir() -> Path:
    from docente_ai.music.lazy import get_music21
    m21 = get_music21()
    return Path(m21.corpus.__file__).parent.resolve()


# ---------------------------------------------------------------------------
# Construcción del índice (se ejecuta una vez y se guarda en config/)
# ---------------------------------------------------------------------------

def _cabeceras_krn(path: Path) -> dict[str, str]:
    cab: dict[str, str] = {}
    spines = 0
    nombres: list[str] = []
    with path.open(encoding='latin-1') as fh:
        for linea in fh:
            if linea.startswith('!!!'):
                m = re.match(r'!!!(\w+)[^:]*:\s*(.*)', linea.strip())
                if m and m.group(1) not in cab:
                    cab[m.group(1)] = m.group(2).strip()
            elif linea.startswith('**'):
                spines = linea.count('**kern')
            elif linea.startswith('!') and not linea.startswith('!!') and spines and not nombres:
                nombres = [c.strip('! ').strip() for c in linea.rstrip('\n').split('\t')]
            elif linea.startswith('='):
                break
    cab['_voces'] = str(spines)
    cab['_nombres'] = '|'.join(reversed([n for n in nombres if n]))  # Humdrum: grave a agudo
    return cab


def _nombre_compositor(raw: str) -> str:
    raw = (raw or '').strip()
    if raw.lower().startswith('palestrina'):
        return 'Giovanni Pierluigi da Palestrina'
    if 'josquin' in raw.lower():
        return 'Josquin des Prez'
    if ',' in raw:
        apellido, nombre = [p.strip() for p in raw.split(',', 1)]
        return f'{nombre} {apellido}'.strip()
    return raw


def _limpiar_compositor(raw: str) -> str:
    raw = re.sub(r'\s+[A-Z]{1,2}-[A-Za-z]+.*$', '', raw.strip())   # siglas RISM (F-Pn 568, I-Rvat...)
    raw = re.sub(r'\s+(?:\?|\d).*$', '', raw).strip()
    if re.match(r'anon', raw, re.I) or not raw:
        return 'Anónimo'
    return raw


def _titulo_desde_archivo(stem: str) -> str:
    t = re.sub(r'^(?:PMFC|Fava)[_\d]*-?', '', stem)
    t = re.sub(r'^(?:Jacopo-)?\d+[a-z]?-', '', t)
    t = re.sub(r'^\d+[a-z]?-', '', t)
    t = t.replace('_', ' ').replace('-', ' ').strip()
    return re.sub(r'\s+', ' ', t)


def _genero_trecento(sub: str, compositor: str, titulo: str) -> str:
    if sub == 'lusitano':
        return 'madrigal'
    if re.match(r'(kyrie|gloria|credo|sanctus|agnus|benedicamus)', titulo, re.I):
        return 'movimiento de misa'
    if re.search(r'vitry', compositor, re.I):
        return 'motete'
    if re.search(r'madrigal', titulo, re.I) or 'jacopo' in compositor.lower():
        return 'madrigal (trecento)'
    return 'canción polifónica'


def construir_indice_corpus() -> list[dict[str, Any]]:
    """Recorre el corpus de music21 y devuelve las obras de música antigua con metadatos leídos de los archivos."""
    from docente_ai.music.lazy import get_music21
    m21 = get_music21()
    base = _corpus_dir()
    entradas: list[dict[str, Any]] = []

    # Palestrina: misas en Humdrum, un archivo por movimiento.
    for p in sorted((base / 'palestrina').glob('*.krn')):
        cab = _cabeceras_krn(p)
        obra = cab.get('OPR') or ''
        if not obra:
            continue
        base_mov = next((m for m in MOVIMIENTOS_MISA if p.stem.lower().startswith(m.lower())), '')
        otl = (cab.get('OTL') or '').strip()
        if base_mov and otl and base_mov.lower() not in otl.lower():
            mov = f'{base_mov} ({otl})'
        else:
            mov = otl or base_mov or p.stem
        entradas.append({
            'archivo_corpus': f'palestrina/{p.name}',
            'compositor': _nombre_compositor(cab.get('COM', 'Palestrina')),
            'obra': obra,
            'movimiento': mov,
            'genero': 'misa',
            'voces': int(cab.get('_voces') or 0),
            'nombres_voces': [n for n in cab.get('_nombres', '').split('|') if n],
        })

    # Josquin: canciones y motetes en ABC (título y compositor en las cabeceras T:/C:).
    for p in sorted((base / 'josquin').glob('*.abc')):
        texto = p.read_text(encoding='latin-1')
        t = re.search(r'^T:\s*(.+)$', texto, re.M)
        if not t:
            continue
        titulo = t.group(1).strip().rstrip(',')
        titulo = re.sub(r'^\d+v\.\s*', '', titulo)
        bloques = [b for b in re.split(r'^X:', texto, flags=re.M)[1:]]
        nombres = []
        for b in bloques:
            ts = re.findall(r'^T:\s*(.+)$', b, re.M)
            if len(ts) > 1:
                nombres.append(re.sub(r'\s*\(.*?\)', '', ts[1]).strip())
        voces = len(bloques) or None
        genero = 'motete' if re.search(r'\b(ave|per illud|deploration)\b', titulo, re.I) else 'chanson'
        if 'ploration' in titulo.lower():
            genero = 'motete-chanson'
        if re.search(r'fortuna|venus', titulo, re.I):
            genero = 'canción polifónica'
        entradas.append({
            'archivo_corpus': f'josquin/{p.name}',
            'compositor': 'Josquin des Prez',
            'obra': titulo,
            'movimiento': '',
            'genero': genero,
            'voces': voces,
            'nombres_voces': nombres if len(nombres) == len(bloques) else [],
        })

    # Monteverdi (libros III-V) queda fuera: en el corpus su texto cantado y su maquetación proceden
    # de OCR con errores visibles, impropios de un material para el alumnado.

    # Vicente Lusitano (madrigal) y trecento / Ars nova. En el trecento algunos metadatos internos
    # no coinciden con la obra; el título se toma del nombre del archivo (edición PMFC).
    for sub in ('lusitano', 'trecento', 'ciconia'):
        for p in sorted((base / sub).glob('*')):
            if p.suffix.lower() not in ('.xml', '.mxl', '.musicxml') or p.stem.endswith('_bak'):
                continue
            try:
                s = m21.converter.parse(str(p))
            except Exception:
                continue
            md = s.metadata
            comp = _limpiar_compositor((md.composer or '').split('\n')[0])
            if sub == 'trecento':
                titulo = _titulo_desde_archivo(p.stem)
            else:
                titulo = re.sub(r'^\d+\.\s*', '', (md.title or md.movementName or p.stem).strip())
            if not comp or len(titulo) < 3:
                continue
            entradas.append({
                'archivo_corpus': f'{sub}/{p.name}',
                'compositor': comp,
                'obra': titulo,
                'movimiento': '',
                'genero': _genero_trecento(sub, comp, titulo),
                'voces': len(list(s.parts)),
                'nombres_voces': [x.partName for x in s.parts if x.partName],
            })

    for ent in entradas:
        ent['obra_id'] = f"{_slug(_apellido(ent['compositor']) or 'anonimo')}:{_slug(ent['obra'])}"
        ent['id'] = 'rep:' + ent['archivo_corpus']
        ent['edicion'] = EDICION_CORPUS
    return entradas


def guardar_indice(entradas: list[dict[str, Any]], destino: Path = INDICE_PATH) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({"version": 1, "entradas": entradas}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return destino


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def cargar_indice(path: str | None = None) -> tuple[dict[str, Any], ...]:
    p = Path(path) if path else INDICE_PATH
    if not p.is_file():
        return ()
    data = json.loads(p.read_text(encoding='utf-8'))
    return tuple(data.get('entradas', []))


def obras_del_indice(entradas=None) -> dict[str, dict[str, Any]]:
    """Agrupa los archivos por obra (una misa reúne sus movimientos)."""
    entradas = cargar_indice() if entradas is None else entradas
    obras: dict[str, dict[str, Any]] = {}
    for ent in entradas:
        o = obras.setdefault(ent['obra_id'], {
            'id': ent['obra_id'], 'compositor': ent['compositor'], 'obra': ent['obra'],
            'genero': ent['genero'], 'voces': ent.get('voces'), 'movimientos': [], 'archivos': {},
        })
        o.setdefault('_voces', []).append(ent.get('voces'))
        mov = ent.get('movimiento') or ''
        if mov and mov not in o['movimientos']:
            o['movimientos'].append(mov)
        o['archivos'].setdefault(mov, ent)
    for o in obras.values():
        vs = [v for v in o.pop('_voces', []) if v]
        if vs:
            o['voces'] = max(set(vs), key=vs.count)
        o['movimientos'].sort(key=lambda m: next((i for i, x in enumerate(MOVIMIENTOS_MISA) if x.lower() in m.lower()), 99))
    return obras


def _apellido(compositor: str) -> str:
    partes = re.sub(r'\(.*?\)', ' ', _sin_tildes(compositor)).replace(',', ' ').split()
    if 'palestrina' in partes:
        return 'palestrina'
    if 'josquin' in partes:
        return 'josquin'
    return partes[-1] if partes else ''


def seleccionar_repertorio(texto_tema: str, texto_fuentes: str = '', limite: int = 24,
                           entradas=None) -> list[dict[str, Any]]:
    """Elige obras del catálogo pertinentes para el tema.

    Una obra entra si su compositor aparece en el tema, en las indicaciones del profesor
    o en los pasajes recuperados de la biblioteca. Las obras cuyo título aparece en los
    pasajes van primero. Los géneros pedidos por el profesor (misa, chanson, madrigal...)
    priorizan dentro de cada compositor. Ningún compositor entra solo por su época.
    """
    tema = _sin_tildes(texto_tema)
    fuentes = _sin_tildes(texto_fuentes)
    todo = f'{tema} {fuentes}'
    obras = obras_del_indice(entradas)
    generos_pedidos = {g for g, palabras in GENEROS_PALABRAS.items() if any(p in tema for p in palabras)}

    puntuadas = []
    for o in obras.values():
        ape = _apellido(o['compositor'])
        if not ape or not re.search(r'\b' + re.escape(ape) + r'\b', todo):
            continue
        puntos = 1
        if re.search(r'\b' + re.escape(ape) + r'\b', tema):
            puntos += 3
        titulo = _sin_tildes(re.sub(r'^(missa|misa)\s+', '', o['obra'], flags=re.I))
        titulo = re.sub(r'\(.*?\)', '', titulo).strip()
        if len(titulo) >= 6 and titulo in fuentes:
            puntos += 6
        if o['genero'] in generos_pedidos or any(o['genero'].startswith(g) for g in generos_pedidos):
            puntos += 2
        puntuadas.append((puntos, o))
    def orden_natural(texto):
        return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', _sin_tildes(texto))]

    # Reparto por turnos entre compositores: cada uno aporta primero sus obras mejor puntuadas,
    # para que ningún autor con muchas obras en el corpus desplace a los demás.
    por_compositor: dict[str, list] = {}
    for puntos, o in sorted(puntuadas, key=lambda par: (-par[0], orden_natural(par[1]['obra']))):
        por_compositor.setdefault(o['compositor'], []).append((puntos, o))
    colas = sorted(por_compositor.values(), key=lambda lista: -lista[0][0])
    elegidas = []
    while colas and len(elegidas) < limite:
        for cola in list(colas):
            if not cola:
                colas.remove(cola)
                continue
            elegidas.append(cola.pop(0)[1])
            if len(elegidas) >= limite:
                break
    return elegidas


def resumen_para_llm(obras: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Forma compacta que se envía al modelo: identificador, autor, obra, género y movimientos."""
    res = []
    for o in obras:
        item = {'id': o['id'], 'compositor': o['compositor'], 'obra': o['obra'], 'genero': o['genero']}
        if o.get('voces'):
            item['voces'] = o['voces']
        if o['movimientos']:
            item['movimientos'] = o['movimientos']
        res.append(item)
    return res


def resolver_obra(obra_id: str, movimiento: str | None = None, entradas=None) -> dict[str, Any] | None:
    """Devuelve el archivo concreto (movimiento) de una obra del catálogo o None si no existe."""
    obras = obras_del_indice(entradas)
    o = obras.get((obra_id or '').strip())
    if not o:
        return None
    mov_pedido = _sin_tildes(movimiento or '')
    elegido = None
    if o['movimientos']:
        for mov in o['movimientos']:
            if mov_pedido and _sin_tildes(mov).split()[0] in mov_pedido:
                elegido = o['archivos'][mov]
                break
        if elegido is None:
            elegido = o['archivos'][o['movimientos'][0]]
    else:
        elegido = next(iter(o['archivos'].values()))
    return {**elegido, 'obra_id': o['id']}


def ruta_archivo(rep_id: str) -> Path | None:
    """Ruta absoluta de un identificador ``rep:<archivo_corpus>`` validada contra el índice."""
    if not rep_id or not rep_id.startswith('rep:'):
        return None
    rel = rep_id[4:]
    if not any(ent['archivo_corpus'] == rel for ent in cargar_indice()):
        return None
    base = _corpus_dir()
    ruta = (base / rel).resolve()
    if not ruta.is_relative_to(base) or not ruta.is_file():
        return None
    return ruta


# ---------------------------------------------------------------------------
# Análisis calculado de un fragmento (entradas de las voces y textura)
# ---------------------------------------------------------------------------

def cargar_partitura(ruta: Path | str):
    """Carga una partitura con music21; las colecciones ABC de una voz por pieza se fusionan en una partitura."""
    from docente_ai.music.lazy import get_music21
    m21 = get_music21()
    s = m21.converter.parse(str(ruta))
    if isinstance(s, m21.stream.Opus):
        s = s.mergeScores()
    return s


def analizar_fragmento(ruta: Path | str, compas_inicio: int = 1, compas_fin: int = 8,
                       nombres_voces: list[str] | None = None) -> dict[str, Any]:
    """Calcula, sobre el archivo real, el orden de entrada de las voces y el grado de homorritmia.

    Devuelve datos objetivos (compás y nota de entrada de cada voz, proporción de ataques
    simultáneos) que permiten describir la textura sin que el modelo de lenguaje lo invente.
    """
    s = cargar_partitura(ruta)
    partes = [p for p in s.parts if 'continuo' not in (p.partName or '').lower()]
    usar_nombres = nombres_voces if nombres_voces and len(nombres_voces) == len(partes) else None
    entradas_voces = []
    ataques_por_voz: list[set[float]] = []
    for idx, parte in enumerate(partes):
        nombre = (usar_nombres[idx] if usar_nombres else parte.partName) or f'Voz {idx + 1}'
        ataques = set()
        primera = None
        for compas in parte.getElementsByClass('Measure'):
            num = compas.number or 0
            if num < compas_inicio or num > compas_fin:
                continue
            for n in compas.notes:
                off = round(float(compas.offset + n.offset), 3)
                ataques.add(off)
                if primera is None:
                    altura = n.pitches[0].nameWithOctave if n.pitches else ''
                    primera = {'voz': nombre.strip(), 'compas': num,
                               'nota': altura.replace('-', '♭').replace('#', '♯'), '_off': off}
        ataques_por_voz.append(ataques)
        if primera:
            entradas_voces.append(primera)
    entradas_voces.sort(key=lambda x: (x['_off'], x['voz']))
    escalonadas = len({e['_off'] for e in entradas_voces}) > 1

    # Proporción media de voces activas que atacan juntas en cada punto de ataque, contando
    # solo desde que todas las voces han entrado (para no confundir la exposición imitativa).
    inicio_pleno = max((e['_off'] for e in entradas_voces), default=0.0)
    for e in entradas_voces:
        e.pop('_off', None)
    activos = [v for v in ataques_por_voz if v]
    puntos = sorted(t for t in set().union(*activos) if t >= inicio_pleno) if activos else []
    if puntos and len(activos) > 1:
        media = sum(sum(1 for v in activos if t in v) / len(activos) for t in puntos) / len(puntos)
        simultaneidad = round(100 * media)
    else:
        simultaneidad = 0

    if escalonadas and simultaneidad <= 45:
        textura = 'entradas escalonadas y ritmos independientes entre las voces (escritura imitativa o contrapuntística)'
    elif simultaneidad >= 70:
        textura = 'las voces atacan mayoritariamente a la vez (escritura homorrítmica, en bloques de acordes)'
    else:
        textura = 'textura mixta: alternan ataques en bloque y ritmos independientes'
    return {
        'compases': f'{compas_inicio}-{compas_fin}',
        'entradas': entradas_voces,
        'entradas_escalonadas': escalonadas,
        'porcentaje_ataques_simultaneos': simultaneidad,
        'textura_calculada': textura,
    }
