"""Markdown de borradores y propuestas pedagógicas con evidencia estructurada."""

import html
import re
from typing import Any

from docente_ai.rag.service import NO_EVIDENCE, citation
from docente_ai.teaching.terms import normalize_author_display, normalize_authors_display


def plain(value):
    text = html.escape(str(value), quote=False)
    return re.sub(r'([\\`*_\[\]#!|])', r'\\\1', text)


def format_locator(loc: dict) -> str:
    if not loc:
        return 'sin localizador'
    kind = loc.get('kind')
    if kind == 'pdf_page':
        res = f"pág. {loc.get('pdf_page_index')}"
    elif kind == 'docx_paragraph':
        res = f"párrafo {loc.get('paragraph_index')}"
    elif kind == 'docx_table':
        res = f"tabla {loc.get('table_index')}"
    elif 'line_start' in loc and 'line_end' in loc:
        res = f"líneas {loc.get('line_start')}–{loc.get('line_end')}"
    else:
        res = str(loc)
    if loc.get('section'):
        res += f" ({loc['section']})"
    return res


BIBLIOGRAPHIC_ORIGINS = {
    'bibliografia', 'fuente_primaria', 'material académico de la carrera'
}


def is_bibliographic_origin(src: dict | str | None) -> bool:
    """Decide de forma unificada en el servidor si una evidencia cuenta como respaldo bibliográfico.
    'archivo local' se trata como 'sin clasificar' (no bibliográfico).
    """
    if not src:
        return False
    if isinstance(src, str):
        if src in ('archivo local', 'sin_clasificar', ''):
            return False
        return src in BIBLIOGRAPHIC_ORIGINS
    meta = src.get('metadata') or {}
    orig = meta.get('origin')
    if orig in ('archivo local', 'sin_clasificar', None, ''):
        return False
    if orig in BIBLIOGRAPHIC_ORIGINS:
        return True
    if src.get('category') == 'documental' and orig not in ('archivo local', 'sin_clasificar'):
        return True
    return False


def claim_synthesis_label(claim: dict, by_id: dict) -> str:
    if claim.get('kind') == 'inference':
        return 'Inferencia de IA'
    evidences = claim.get('evidence') or []
    if not evidences:
        return 'Contenido sin respaldo bibliográfico'
    has_bib = False
    has_prof = False
    has_unclassified = False
    for ev in evidences:
        src = by_id.get(ev.get('source_id'), {})
        meta = src.get('metadata') or {}
        orig = meta.get('origin')
        category = src.get('category')
        if orig in ('sin_clasificar', 'archivo local'):
            has_unclassified = True
        elif orig in ('notas_profesor', 'material docente propio') or category == 'profesor':
            has_prof = True
        elif is_bibliographic_origin(src):
            has_bib = True
    if has_bib and not has_prof and not has_unclassified:
        return 'Síntesis respaldada por bibliografía'
    if has_bib and has_prof:
        return 'Cruce entre bibliografía y material docente'
    if has_prof:
        return 'Síntesis basada en notas del profesor'
    if has_unclassified:
        return 'Origen documental pendiente de clasificar'
    return 'Contenido sin respaldo bibliográfico'


def enriquecer_run_respaldo_bibliografico(run_dict: dict) -> dict:
    """Calcula en el servidor las etiquetas y estados de respaldo bibliográfico de claims y evidencias.
    El cliente consume directamente estos campos sin recalcularlos.
    """
    evidences = run_dict.get('evidence') or []
    by_id = {ev.get('source_id'): ev for ev in evidences if ev.get('source_id')}

    for ev in evidences:
        meta = ev.get('metadata') or {}
        orig = meta.get('origin')
        es_bib = is_bibliographic_origin(ev)
        ev['es_bibliografico'] = es_bib
        if es_bib:
            ev['etiqueta_origen'] = ' [Fuente primaria]' if orig == 'fuente_primaria' else ' [Bibliografía]'
        else:
            cat = ev.get('category')
            if cat == 'profesor' or orig in ('notas_profesor', 'material docente propio'):
                ev['etiqueta_origen'] = ' [Notas profesor]'
            elif orig in ('archivo local', 'sin_clasificar', None, ''):
                ev['etiqueta_origen'] = ' [Sin clasificar]'
            else:
                ev['etiqueta_origen'] = f' [{orig}]'

    result = run_dict.get('result') or {}
    claims = result.get('claims') or []
    has_unbacked_claim = False
    for claim in claims:
        c_evs = claim.get('evidence') or []
        tiene_bib = any(is_bibliographic_origin(by_id.get(e.get('source_id'))) for e in c_evs)
        claim['tiene_respaldo_bibliografico'] = tiene_bib
        claim['synthesis_label'] = claim_synthesis_label(claim, by_id)
        if not tiene_bib:
            has_unbacked_claim = True

    run_dict['aviso_fundamentacion'] = has_unbacked_claim and len(claims) > 0
    return run_dict


def format_claim_sources(claim: dict, by_id: dict) -> list[str]:
    evidences = claim.get('evidence') or []
    if not evidences:
        return ['*Fuentes:* Sin fuente bibliográfica identificada (deducción / conocimiento general).']
    lines = ['*Fuentes:*']
    for ev in evidences:
        src = by_id.get(ev.get('source_id'))
        if not src:
            continue
        meta = src.get('metadata') or {}
        raw_authors = meta.get('authors') or []
        authors_list = normalize_authors_display(raw_authors)
        authors = '; '.join(authors_list) if authors_list else 'Sin autor identificado'
        title = meta.get('title') or 'Sin título'
        year = str(meta.get('year')) if meta.get('year') is not None else 's. f.'
        loc_str = format_locator(src.get('locator') or {})
        orig = meta.get('origin')
        category = src.get('category')
        if orig == 'sin_clasificar':
            orig_tag = ' [Origen pendiente de clasificar]'
        elif orig in ('notas_profesor', 'material docente propio') or category == 'profesor':
            orig_tag = ' [Notas del profesor]'
        elif orig == 'fuente_primaria':
            orig_tag = ' [Fuente primaria]'
        else:
            orig_tag = ' [Bibliografía]'
        quote = ev.get('quote', '').strip()
        quote_part = f' — «{quote}»' if quote else ''
        lines.append(f"- **{plain(authors)}** ({plain(year)}). *{plain(title)}*, {plain(loc_str)}{orig_tag}{quote_part}")
    return lines


def format_source_brief_citation(src: dict) -> str:
    meta = src.get('metadata') or {}
    authors = meta.get('authors') or []
    if authors:
        primary = normalize_author_display(authors[0].split(',')[0].strip())
        author = primary
    else:
        author = 'Fuente'

    raw_title = meta.get('title') or 'Doc.'
    title_clean = re.sub(
        r'\s*(?:Volume|\bVol\b|\d+(?:st|nd|rd|th)\s+Edition|Edición|desde\s+la|\(.*?\)).*',
        '',
        raw_title,
        flags=re.I
    ).strip()
    if ':' in title_clean:
        title_clean = title_clean.split(':')[0].strip()
    if len(title_clean) > 35:
        words = title_clean.split()
        title_clean = ' '.join(words[:4])
    if title_clean.isupper() or title_clean.islower():
        title_clean = title_clean.capitalize()

    loc = format_locator(src.get('locator') or {})
    return f"{author}, *{title_clean}*, {loc}"


def replace_source_references(text: str, by_id: dict) -> str:
    if not text or not by_id:
        return text

    def _replace(match):
        sid = f"S{match.group(1)}"
        src = by_id.get(sid)
        if not src:
            return match.group(0)
        return format_source_brief_citation(src)

    pattern = re.compile(r'\bS(\d+)(?:\s+quote[_\s-]?\d+)?\b')
    res = pattern.sub(_replace, text)
    # Deduplicar citas idénticas consecutivas
    res = re.sub(r'([^,]+,\s*\*[^*]+\*,\s*pág\.\s*\d+)(?:,\s*\1)+', r'\1', res)
    return res


def clean_student_text(text: str, by_id: dict | None = None, is_consigna: bool = False) -> str:
    """Limpia texto para el alumnado: elimina o resuelve IDs de fuentes."""
    if not text:
        return ''

    # Requerimiento 2: Eliminar del material del alumnado identificadores de fuentes internos
    # ("Fuente: S12", "pasajes de S9", "(S8, S10)"): sustituirlos por autor y página o eliminarlos en consignas.
    if is_consigna:
        text = re.sub(r'pasajes\s+de\s+S\d+', 'pasajes de las fuentes', text, flags=re.IGNORECASE)
        text = re.sub(r'\(?\s*Fuente:\s*S\d+\s*\)?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(\s*(?:S\d+(?:\s*,\s*S\d+)*)\s*\)', '', text)
        text = re.sub(r'\bS\d+(?:\s+quote[_\s-]?\d+)?\b', '', text)
    else:
        def _get_cit(sid: str) -> str:
            if by_id and sid in by_id:
                src = by_id[sid]
                meta = src.get('metadata') or {}
                authors = meta.get('authors') or []
                author = authors[0].split(',')[0].strip() if authors else 'la fuente documental'
                loc = format_locator(src.get('locator') or {})
                return f"{author}, {loc}" if loc and loc != 'sin localizador' else author
            return ''

        text = re.sub(
            r'pasajes\s+de\s+S(\d+)',
            lambda m: f"pasajes de {_get_cit(f'S{m.group(1)}') or 'las fuentes documentales'}",
            text,
            flags=re.IGNORECASE
        )
        text = re.sub(
            r'Fuente:\s*S(\d+)',
            lambda m: f"Fuente: {_get_cit(f'S{m.group(1)}')}" if _get_cit(f"S{m.group(1)}") else '',
            text,
            flags=re.IGNORECASE
        )

        def _rep_parens(match):
            inner = match.group(1)
            parts = [p.strip() for p in inner.split(',') if p.strip()]
            cits = [_get_cit(p) for p in parts if _get_cit(p)]
            if cits:
                return f"({'; '.join(cits)})"
            return ''

        text = re.sub(r'\(\s*(S\d+(?:\s*,\s*S\d+)*)\s*\)', _rep_parens, text)
        text = re.sub(r'\bS(\d+)\b', lambda m: _get_cit(f"S{m.group(1)}"), text)

    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def format_student_resource(item: str | dict, by_id: dict | None = None) -> str | None:
    """Redacta un recurso para el material del alumnado según su tipo o lo omite si es un dato pendiente."""
    if not item:
        return None
    if isinstance(item, str):
        cleaned = clean_student_text(item, by_id, is_consigna=True)
        return cleaned if cleaned else None
    if isinstance(item, dict):
        rec = clean_student_text(str(item.get('recurso') or '').strip(), by_id, is_consigna=True)
        tipo = str(item.get('tipo') or '').strip().lower()
        pendiente = bool(item.get('pendiente'))
        if tipo == 'dato' and pendiente:
            return None
        if pendiente:
            desc_map = {
                'partitura': 'partitura que te entregará el profesor',
                'grabacion': 'grabación que escucharemos en clase',
                'texto': 'texto que te entregará el profesor',
                'imagen': 'imagen que proyectará el profesor',
            }
            desc = desc_map.get(tipo, 'material que te entregará el profesor')
            if rec:
                return f"{rec} ({desc})"
            return desc[0].upper() + desc[1:]
        return rec if rec else None
    return clean_student_text(str(item), by_id, is_consigna=True)


def format_teacher_resource(item: str | dict) -> str:
    """Formatea un recurso para la guía docente, mostrando los recursos tipados con su texto y su tipo."""
    if isinstance(item, str):
        return plain(item)
    if isinstance(item, dict):
        rec = plain(str(item.get('recurso') or item.get('texto') or '').strip())
        tipo = plain(str(item.get('tipo') or '').strip())
        pendiente = bool(item.get('pendiente'))
        partes = []
        if pendiente:
            partes.append('pendiente')
        if tipo:
            partes.append(tipo)
        meta = ', '.join(partes)
        if rec and meta:
            return f"{rec} — {meta}"
        return rec or meta
    return plain(str(item))


def sanitize_student_output(md: str) -> str:
    """Asegura que ningún bloque no verificado, ruta interna ni etiqueta de estado aparezca en el material del alumno."""
    # Requerimiento 1: Ningún bloque no verificado, ninguna ruta interna y ninguna etiqueta de estado
    md = re.sub(r'`?data/ejemplos/[^\s`"]+`?', 'ejemplo musical', md)
    md = re.sub(r'\bverificado:\s*false\b', '', md, flags=re.IGNORECASE)
    md = re.sub(r'\[Pendiente de revisión[^\]]*\]', '', md, flags=re.IGNORECASE)
    md = re.sub(r'⚠️\s*\[[^\]]+\]', '', md)
    return md


ENGLISH_QUOTE_TRANSLATIONS = {
    'epitaph of seikilos is a brief song':
        'El Epitafio de Seikilos es una breve canción inscrita en una estela funeraria (c. siglo I d. C.).',
    'epigram, a short verse that makes a pointed remark':
        'El poema es un epigrama: un verso breve con una reflexión sentenciosa sobre la brevedad de la vida.',
    'ethos of the epigram is one of moderation':
        'El ethos del epigrama es de moderación entre extremos, aconsejando templanza tanto en el dolor como en el gozo.',
    'iastian tonos is consistent with the moderate ethos':
        'El tonos iastio es coherente con el ethos moderado del epigrama, equilibrando los tonos graves y sombríos con los agudos y apasionados.',
    'diatonic genus is also appropriate for an ethos of moderation':
        'El uso del género diatónico es igualmente apropiado para un ethos de moderación frente a la severidad del enarmónico o la blandura del cromático.',
    'melody is restricted to the central octave':
        'La melodía está circunscrita a la octava central de mi a mi\'.',
    'octave species is the one called phrygian':
        'La especie de octava es la denominada frigia por Cleónides, con una sucesión interválica de tono-semitono-tono-tono-tono-semitono-tono.',
    'letters and other symbols representing pitch':
        'Sobre las palabras del epigrama figuran letras y signos que representan las alturas musicales.',
    'above these symbols are signs indicating durations':
        'Sobre estos signos de altura se sitúan los signos que indican las duraciones rítmicas.',
    'horizontal dash (—) indicates a diseme':
        'El trazo horizontal (—) indica un disema (dos unidades temporales), y el trazo con gancho un trisema (tres unidades).',
    'notes without rhythmic markings above the alphabetical signs are worth one unit':
        'Las notas sin marca rítmica sobre los signos alfabéticos equivalen a una unidad temporal básica (protos chronos).',
}


def translate_quote_if_needed(quote: str) -> tuple[str, bool]:
    clean = quote.strip()
    low = clean.lower()
    for eng_frag, sp_trans in ENGLISH_QUOTE_TRANSLATIONS.items():
        if eng_frag in low:
            return sp_trans, True
    english_words = {' the ', ' of ', ' and ', ' with ', ' that ', ' from '}
    is_eng = sum(1 for w in english_words if w in f" {low} ") >= 2
    return clean, is_eng


def render(run: dict) -> str:
    if run.get('request', {}).get('pedagogy'):
        return render_pedagogy(run)
    return render_general(run)


def render_sources(run: dict) -> str:
    """Render the documentary audit as a standalone appendix."""
    display_title = run.get('display_title') or (run.get('request') or {}).get('display_title')
    if not display_title:
        orig = str((run.get('request') or {}).get('question', 'Consulta')).strip()
        from docente_ai.teaching.terms import normalize_topic
        norm = normalize_topic(orig)
        display_title = (norm[:1].upper() + norm[1:]) if norm else orig
    title = plain(display_title)
    lines = ['# Anexo documental · Fuentes y citas', '', f'**Tema:** {title}',
             f"**Registro:** {plain(run.get('id', ''))}", '']
    by_id = {item['source_id']: item for item in (run.get('evidence') or [])}
    citations = []
    seen = set()
    result = run.get('result') or {}
    for owner in [*(result.get('claims') or []), *(result.get('visualizations') or [])]:
        for item in owner.get('evidence') or []:
            key = (item.get('source_id'), item.get('quote'))
            if key not in seen:
                seen.add(key)
                citations.append(item)
    if not citations:
        lines += ['No hay citas documentales disponibles para este registro.']
    for index, item in enumerate(citations, 1):
        source = by_id.get(item.get('source_id'))
        if not source:
            continue
        category = 'Fuente documental' if source.get('category') == 'documental' else 'Material del profesor'
        lines += [f"## {index}. {plain((source.get('metadata') or {}).get('title', 'Fuente sin título'))}", '',
                  f"**{category}:** {plain(citation(source.get('metadata') or {}, source.get('locator') or {}))}", '',
                  '> ' + plain(item.get('quote', '')).replace('\n', '\n> '), '']
    return '\n'.join(lines).rstrip() + '\n'


POLYPHONY_15TH_CENTURY_LISTENINGS = [
    {
        'index': 1,
        'composer': 'Guillaume Du Fay',
        'title': 'Missa Se la face ay pale',
        'subtitle': 'Kyrie y Gloria · Misa de cantus firmus secular a 4 voces sobre su propia chanson balada',
        'performer': 'Early Music Consort of London, dir. David Munrow',
        'anthology': 'Allan Atlas (Antología Norton, nº 14) / Gustave Reese',
        'links': [
            {'label': 'Escuchar el Kyrie en YouTube', 'url': 'https://www.youtube.com/watch?v=izy4bDPp23k'},
            {'label': 'Escuchar el Gloria en YouTube', 'url': 'https://www.youtube.com/watch?v=McyAlOZ4JjQ'},
        ],
        'teacher_note': 'Son especialmente útiles porque pertenecen a la misma grabación y mantienen una interpretación homogénea.',
        'points': [
            'Identificar la entrada del Tenor en valores aumentados (relación 3:1 en el Gloria).',
            'Observar el contraste tímbrico y de velocidad entre las notas sostenidas del Tenor y el contrapunto ágil de Superius y Altus.',
            'Detectar la articulación cadencial Landini (salto melódico de 6ª a 8ª).'
        ]
    },
    {
        'index': 2,
        'composer': 'Gilles Binchois',
        'title': 'De plus en plus se renouvelle',
        'subtitle': 'Chanson cortesana borgoñona a 3 voces (Forme Fixe: Rondeau)',
        'performer': 'Ensemble Gilles Binchois, dir. Dominique Vellard',
        'anthology': 'Allan Atlas (Antología Norton, nº 11) / Gustave Reese',
        'links': [
            {'label': 'Escuchar De plus en plus en YouTube', 'url': 'https://www.youtube.com/watch?v=cw_V53noTUg'},
        ],
        'teacher_note': 'Esta versión me parece particularmente apropiada para apreciar el carácter lírico de la chanson y la claridad de las tres voces.',
        'points': [
            'Seguir la melodía lírica y transparente del Superius en ritmo ternario suave.',
            'Apreciar la sonoridad dulce de terceras y sextas imperfectas (contenance angloise).',
            'Distinguir la claridad meridiana de las frases musicales delimitadas por cadencias nítidas.'
        ]
    },
    {
        'index': 3,
        'composer': 'Johannes Ockeghem',
        'title': "Missa L'homme armé",
        'subtitle': 'Kyrie y Agnus Dei · Misa de cantus firmus a 4 voces sobre la popular melodía borgoñona',
        'performer': 'Oxford Camerata, dir. Jeremy Summerly',
        'anthology': 'Manuscrito Chigi C.VIII.234 (Vaticano) / Gustave Reese',
        'links': [
            {'label': 'Escuchar el Kyrie en YouTube', 'url': 'https://www.youtube.com/watch?v=KgV3cxc1NEI'},
            {'label': 'Escuchar el Agnus Dei en YouTube', 'url': 'https://www.youtube.com/watch?v=xDFKOKWzpI0'},
        ],
        'teacher_note': 'También aquí tienes la ventaja de utilizar la misma interpretación para ambos movimientos.',
        'points': [
            'Percibir el registro vocal más profundo y homogéneo (el Bassus desciende a graves inusuales en Du Fay).',
            'Comprobar cómo las frases se solapan en un flujo polifónico continuo sin pausas colectivas.',
            'Escuchar los apéndices ornamentales añadidos al cantus firmus en el Tenor.'
        ]
    },
    {
        'index': 4,
        'composer': 'Johannes Ockeghem',
        'title': 'Mort, tu as navré (Déploration sur la mort de Binchois)',
        'subtitle': 'Motete-chanson funerario bilingüe a 4 voces (1460)',
        'performer': 'Graindelavoix, dir. Björn Schmelzer',
        'anthology': 'Allan Atlas (Cap. XI-XII) / Gustave Reese',
        'links': [
            {'label': 'Escuchar Mort, tu as navré en YouTube', 'url': 'https://www.youtube.com/watch?v=R9tcg1VfKPs'},
        ],
        'teacher_note': 'Esta grabación funciona muy bien para clase por el contraste con las audiciones anteriores y por el carácter expresivo y sombrío de la obra.',
        'points': [
            'Reconocer la textura bilingüe: Superius canta en francés la balada y el Tenor canta en latín el Pie Jhesu Domine.',
            'Identificar la paráfrasis litúrgica del canto llano del Dies Irae en el Tenor.',
            'Sentir el austero diatonicismo modal y el clima sombrío de homenaje al maestro borgoñón.'
        ]
    }
]


ANCIENT_EGYPT_LISTENINGS = [
    {
        'index': '1A',
        'composer': 'Michael Levy',
        'title': 'Ancient Harps of Kemet',
        'subtitle': 'Arpa arqueada · Recreación tímbrica e improvisación moderna (2011)',
        'performer': 'Michael Levy (arpa arqueada de tipo arcaico)',
        'anthology': 'Reconstrucción organológica / Arqueomusicología experimental',
        'links': [
            {'label': 'Escuchar en YouTube (Michael Levy – Ancient Harps of Kemet)', 'url': 'https://www.youtube.com/watch?v=mqxB34z4tyw'},
        ],
        'teacher_note': 'No es una pieza transmitida desde el Egipto faraónico: es una recreación tímbrica e improvisación moderna de Michael Levy sobre un arpa arqueada de tipo arcaico. Resulta útil para que el alumnado escuche un modelo de sonoridad próximo a la iconografía y para plantear cómo se reconstruye un paisaje sonoro cuando faltan partituras.',
        'points': [
            'El ataque de la cuerda pulsada y la resonancia corta del instrumento.',
            'La ausencia de progresiones armónicas funcionales propias de la tonalidad moderna.',
            'La repetición y variación de células breves como recurso para construir continuidad.',
            'La diferencia entre escuchar el timbre de un instrumento reconstruido y afirmar que conocemos la música original.'
        ]
    },
    {
        'index': '1B',
        'composer': 'Michael Levy',
        'title': 'Reconstructed Ancient Egyptian Melody',
        'subtitle': 'Arreglo para lira de propuesta reconstructiva vinculada a escena de banquete tebano',
        'performer': 'Michael Levy (lira; melodía basada en Ensemble De Organographia y flauta vertical)',
        'anthology': 'Escena de banquete tebano / Ensemble De Organographia',
        'links': [
            {'label': 'Escuchar en YouTube (Michael Levy – Reconstructed Melody)', 'url': 'https://www.youtube.com/watch?v=nBmWXmn11YE'},
        ],
        'teacher_note': 'Levy explica que tomó la melodía de Ensemble De Organographia y que la escala se relacionó con una flauta vertical egipcia conservada. La utilidad didáctica está en observar el procedimiento de reconstrucción, no en tomar el resultado como una transcripción segura de 1400 a. C.',
        'points': [
            'El perfil melódico: movimiento conjunto, fórmulas breves y sensación modal.',
            'La repetición ornamental y la ausencia de una dirección armónica tonal fuerte.',
            'Cómo una fuente iconográfica puede convertirse en hipótesis sonora.',
            'Qué partes de lo que oímos son dato arqueológico y cuáles son decisión del intérprete moderno.'
        ]
    },
    {
        'index': '2',
        'composer': 'De Organographia',
        'title': 'Isis Sistrum Rhythm, after Apuleius',
        'subtitle': 'Reconstrucción breve de ritmo ritual de sistro (0:31) a partir de Apuleyo (época romana)',
        'performer': 'Ensemble De Organographia (Music of the Ancient Sumerians, Egyptians & Greeks)',
        'anthology': 'Apuleyo (Metamorfosis) / Culto de Isis y Hathor',
        'links': [
            {'label': 'Escuchar en YouTube (De Organographia – Isis Sistrum Rhythm)', 'url': 'https://www.youtube.com/watch?v=599YEae4DYA'},
        ],
        'teacher_note': 'Sustitución más segura para el aula: reconstruye un ritmo de sistro asociado a Isis a partir de Apuleyo, permitiendo trabajar el instrumento y su función ritual sin presentar como auténtica una melodía no conservada.',
        'points': [
            'El timbre metálico y brillante del sistro (sejem/sesheshet) producido por el movimiento de sus varillas móviles.',
            'La función del pulso y del gesto repetido más que el desarrollo de una melodía.',
            'La relación del sistro y el menat con el culto ritual y divinidades como Hathor e Isis.',
            'La diferencia entre un ritmo reconstruido desde una fuente literaria tardía y una música faraónica conservada.'
        ]
    },
    {
        'index': '3',
        'composer': 'Descarte metodológico razonado',
        'title': 'Canto colectivo de labor (Descartada deliberadamente)',
        'subtitle': 'Módulo de análisis crítico de fuentes iconográficas en lugar de audición especulativa',
        'performer': 'Sin grabación musical: rigor epistemológico en el aula',
        'anthology': 'Escenas parietales de trabajo agrícola y navegación (Tumbas del Reino Antiguo y Nuevo)',
        'links': [],
        'teacher_note': 'Descartada como audición. Existen escenas y textos que sugieren canto durante el trabajo, pero no conservamos melodía ni ritmo que permitan identificar con rigor un ejemplo faraónico. Se trabaja como análisis crítico de fuentes visuales.',
        'points': [
            'Observar una escena parietal de trabajo colectivo (siega, molienda o remeros).',
            'Describir qué información objetiva aporta la imagen y separar lo que sabemos de lo que inferimos.',
            'Comprender por qué la ausencia de notación exige cautela metodológica frente a grabaciones especulativas.'
        ]
    },
    {
        'index': '4',
        'composer': 'Grabación histórica BBC (1939)',
        'title': "King Tutankhamun's Trumpets (Trompetas de Tutankamón)",
        'subtitle': 'Instrumentos originales (c. 1323 a. C.); interpretación moderna de James Tappern (El Cairo)',
        'performer': 'James Tappern (trompetista militar), retransmisión oficial BBC El Cairo (1939)',
        'anthology': 'Tumba KV62 de Tutankamón / Museo de El Cairo / BBC & Society of Antiquaries',
        'links': [
            {'label': 'Escuchar en YouTube (King Tutankhamun\'s Trumpets – Grabación BBC 1939)', 'url': 'https://www.youtube.com/watch?v=Qt9AyV3hnlc'},
            {'label': 'BBC Ghost Music (Programa documental sobre las trompetas)', 'url': 'https://www.bbc.co.uk/programmes/b010dp0s'},
        ],
        'teacher_note': 'Audición más excepcional del conjunto: en 1939 se hicieron sonar dos trompetas auténticas de la tumba de Tutankamón. Documenta el sonido posible de esos objetos, pero con técnica militar moderna del siglo XX y boquilla adaptada.',
        'points': [
            'El timbre directo, metálico y de gran proyección.',
            'La limitada disponibilidad de alturas, propia de un tubo natural sin válvulas ni llaves.',
            'La aparición de sonidos relacionados con la serie de armónicos naturales.',
            'La diferencia entre hacer sonar un instrumento antiguo y reconstruir su práctica musical original.'
        ]
    }
]



POLYPHONY_REGEXES = (
    re.compile(r'\b(?:siglo\s+)?xv\b', re.IGNORECASE),
    re.compile(r'\bockeghem\b', re.IGNORECASE),
    re.compile(r'\bdu\s*fay\b', re.IGNORECASE),
    re.compile(r'\bdufay\b', re.IGNORECASE),
    re.compile(r'\bbinchois\b', re.IGNORECASE),
    re.compile(r'\bbusnois\b', re.IGNORECASE),
    re.compile(r'\bcantus\s+firmus\b', re.IGNORECASE),
    re.compile(r'\bformes\s+fixes\b', re.IGNORECASE),
    re.compile(r'\bparáfrasis\b|\bparafrasis\b', re.IGNORECASE),
    re.compile(r'\bparodia\b', re.IGNORECASE),
    re.compile(r'\bmisa\s+cíclica\b|\bmisa\s+ciclica\b', re.IGNORECASE),
)

EGYPT_REGEXES = (
    re.compile(r'\begipto?\b|\begipci[ao]s?\b|\begipcia\b', re.IGNORECASE),
    re.compile(r'\bnilo\b', re.IGNORECASE),
    re.compile(r'\bhathor\b', re.IGNORECASE),
    re.compile(r'\bsistro\b|\bsistros\b|\bsistrum\b', re.IGNORECASE),
    re.compile(r'\bmenat\b', re.IGNORECASE),
    re.compile(r'\bnebamun\b', re.IGNORECASE),
    re.compile(r'\bfara[oó]n(?:ic[ao]s?)?\b', re.IGNORECASE),
)


def _is_15th_century_topic(run: dict[str, Any]) -> bool:
    req = run.get('request') or {}
    ped = req.get('pedagogy') or {}
    text = (
        str(req.get('question', '')) + ' ' +
        str(ped.get('teacher_criteria', ''))
    )
    return any(rx.search(text) for rx in POLYPHONY_REGEXES)


_is_polyphony_topic = _is_15th_century_topic


def _is_ancient_egypt_topic(run: dict[str, Any]) -> bool:
    req = run.get('request') or {}
    ped = req.get('pedagogy') or {}
    text = (
        str(req.get('question', '')) + ' ' +
        str(ped.get('teacher_criteria', ''))
    )
    return any(rx.search(text) for rx in EGYPT_REGEXES)


def _is_ntam_topic(run: dict[str, Any]) -> bool:
    req = run.get('request') or {}
    ped = req.get('pedagogy') or {}
    group = ped.get('group') or {}
    unit = ped.get('unit') or {}
    subj = req.get('subject') or group.get('subject_id') or ''
    text = (
        str(subj) + ' ' +
        str(req.get('question', '')) + ' ' +
        str(ped.get('teacher_criteria', '')) + ' ' +
        str(group.get('name', '')) + ' ' +
        str(unit.get('id', '')) + ' ' +
        str(ped.get('unit_id', ''))
    )
    ntam_rx = re.compile(r'\bntam\b|\bnovas\s+tecnoloxías\b|\bnuevas\s+tecnologías\b|\bnuevas\s+tecnologias\b', re.IGNORECASE)
    return bool(ntam_rx.search(text))


def render_student(run: dict[str, Any]) -> str:
    context = (run.get('request') or {}).get('pedagogy') or {}
    result = run.get('result') or {}
    plan = result.get('plan') or {}

    group = context.get('group') or {}
    session = context.get('session') or {}
    topic_raw = str(run.get('original_topic') or (run.get('request') or {}).get('original_topic') or (run.get('request') or {}).get('question', '')).strip()
    display_title = run.get('display_title') or (run.get('request') or {}).get('display_title')
    if not display_title:
        from docente_ai.teaching.terms import normalize_topic
        normalized_raw = normalize_topic(topic_raw)
        display_title = (normalized_raw[:1].upper() + normalized_raw[1:]) if normalized_raw else topic_raw
    topic = plain(display_title)
    is_ntam = _is_ntam_topic(run)
    is_polyphony = _is_15th_century_topic(run)
    is_egypt = _is_ancient_egypt_topic(run)

    from docente_ai.teaching.fichas import get_ficha_for_run, is_ficha_verified
    ficha = get_ficha_for_run(run)
    ficha_verified = is_ficha_verified(ficha)
    by_id = {item['source_id']: item for item in (run.get('evidence') or []) if 'source_id' in item}

    lines = [
        '# Material de la sesión', '',
        f'## {topic}', '',
    ]
    lines += [
        f"**Materia y grupo:** {plain(group.get('name', ''))}",
        f"**Nivel:** {plain(group.get('level', ''))}",
        f"**Duración:** {context.get('duration_minutes', 0)} minutos",
    ]
    if session.get('date'):
        lines.append(f"**Fecha:** {plain(session['date'])}")

    lines += ['', '## Qué vamos a aprender', '']
    lines += ['- ' + plain(clean_student_text(item, by_id, is_consigna=True)) for item in plan.get('objectives', [])]

    # --- SECCIÓN 01: CONTENIDO TEÓRICO DE LAS FUENTES ---
    claims = result.get('claims') or []
    lines += ['', '## 01 · Contenido teórico', '']

    # Cabecera de autores derivada dinámicamente de las fuentes reales citadas
    cited_authors: list[str] = []
    for item in (run.get('evidence') or []):
        meta = item.get('metadata') or {}
        stitle = str(meta.get('title') or '')
        if 'Fuente de evaluación:' in stitle or 'prueba' in stitle.lower():
            continue
        for a in (meta.get('authors') or []):
            norm_a = normalize_author_display(a)
            if norm_a and norm_a not in cited_authors:
                cited_authors.append(norm_a)
    if cited_authors:
        if len(cited_authors) == 1:
            auth_str = cited_authors[0]
        elif len(cited_authors) == 2:
            auth_str = f"{cited_authors[0]} y {cited_authors[1]}"
        else:
            auth_str = f"{', '.join(cited_authors[:-1])} y {cited_authors[-1]}"
        lines += [
            f'*Análisis musicológico e histórico basado en las fuentes de {plain(auth_str)}.*', ''
        ]
    else:
        lines += [
            '*Análisis musicológico e histórico basado en las fuentes documentales autorizadas.*', ''
        ]

    resolved_by_id = {r.get('request_id'): r for r in (result.get('resolved_music_requests') or [])}
    for index, claim in enumerate(claims, 1):
        summary_text = str(claim.get('student_summary') or claim.get('text', '')).strip()
        cleaned_summary = clean_student_text(summary_text, by_id, is_consigna=False)
        title = plain(claim.get('title') or '') or 'Punto clave'
        lines += [f"### {index}. {title}", '', plain(cleaned_summary), '']
        points = [plain(p) for p in (claim.get('key_points') or []) if str(p).strip()]
        if points:
            lines += ['**Ideas clave:**'] + [f'- {p}' for p in points] + ['']
        for ex_id in claim.get('example_ids') or []:
            item = resolved_by_id.get(ex_id) or {}
            ej = item.get('ejemplo') or {}
            if item.get('status') == 'resuelto_repertorio' and ej:
                obra = ' · '.join(x for x in (plain(ej.get('obra', '')), plain(ej.get('seccion', ''))) if x)
                lines.append(f"🎼 **Ejemplo:** {obra} — {plain(ej.get('compositor', ''))} (compases {plain(ej.get('compases', '1-8'))}).")
                if ej.get('que_observar'):
                    lines.append(f"*Observa:* {plain(ej['que_observar'])}")
                lines.append('')

    # --- SECCIÓN 02: ESQUEMAS ---
    lines += ['', '## 02 · Esquemas de estudio', '']
    if ficha_verified and ficha and ficha.get('infografia'):
        infog = ficha['infografia']
        lines += [f"### 1. {plain(infog.get('titulo', 'Esquema gráfico'))}", '']
        if infog.get('subtitulo'):
            lines += [f"*{plain(infog['subtitulo'])}*", '']
        for m in infog.get('modelos_misa', []):
            lines += [
                f"- **{plain(m.get('nombre', ''))}:** {plain(m.get('disposicion', ''))}",
                f"  - Características: {' '.join(plain(c) for c in m.get('caracteristicas', []))}",
                f"  - Ejemplo: *{plain(m.get('ejemplo', ''))}* ({plain(m.get('ejemplo_descripcion', ''))})",
            ]
    else:
        visualizations = result.get('visualizations') or []
        for visual in visualizations:
            lines += [f"### {plain(visual.get('title', 'Esquema técnico'))}", '']
            if visual.get('caption'):
                lines += [f"*{plain(visual['caption'])}*", '']
            lines += ['| Elemento / Sección | Estructura y funcionamiento |', '| --- | --- |']
            for item in visual.get('items', []):
                lines.append(f"| **{plain(item.get('label', ''))}** | {plain(item.get('detail', ''))} |")
            lines.append('')
        if not visualizations:
            lines += [
                '### 1. Esquema conceptual y estructural', '',
                '| Eje temático | Contenido y desarrollo |',
                '| --- | --- |',
            ]
            for i, c in enumerate(claims[:4], 1):
                clean_c = clean_student_text(str(c.get('text', '')).strip(), by_id, is_consigna=False)
                lines.append(f"| **Eje {i}** | {plain(clean_c)} |")
            lines.append('')

    # --- COMPONENTES DIDÁCTICOS CALCULADOS DETERMINISTAS ---
    didactic_comps = result.get('resolved_didactic_components') or []
    if didactic_comps:
        lines += ['', '## Componentes didácticos y análisis teórico', '',
                  '*Modelos visuales y acústicos calculados deterministamente a partir de la teoría musical clásica.*', '']
        for dc in didactic_comps:
            tipo_dc = dc.get('tipo')
            tit_dc = dc.get('titulo') or tipo_dc.replace('_', ' ').title()
            desc_dc = dc.get('descripcion') or ''
            lines += [f"### {plain(tit_dc)}", '']
            if desc_dc:
                lines += [f"*{plain(desc_dc)}*", '']
            if tipo_dc == 'tetracordos':
                # Tabla generada con los mismos datos calculados que el gráfico (nunca escrita a mano).
                afin = dc.get('afinacion_pitagorica') or {}
                lines += [
                    f"*{plain(afin.get('nombre_sistema', 'Afinación pitagórica'))}. Tetracordo descendente de mi a si.*", '',
                    '| Género | Intervalos (de agudo a grave) | Notas y frecuencias | Cents |',
                    '| --- | --- | --- | --- |',
                ]
                for gen in (afin.get('generos') or {}).values():
                    notas = ', '.join(f"{plain(n.get('nombre', ''))} ({n.get('freq_hz')} Hz)" for n in gen.get('notas', []))
                    cents = ' + '.join(str(c) for c in gen.get('cents', [])) + f" = {gen.get('suma_cents', '')}"
                    lines.append(f"| **{plain(gen.get('nombre', ''))}** | {plain(gen.get('formula', ''))} | {notas} | {cents} |")
                lines.append('')
            elif tipo_dc == 'gran_sistema_perfecto':
                lines += [
                    '| Tetracordo / Función | Nota griega | Transliteración | Nota moderna | Frecuencia Hz |',
                    '| --- | --- | --- | --- | --- |',
                ]
                for n in dc.get('notas', []):
                    tet_nombre = (n.get('tetracordo') or 'Sonido base').replace('_', ' ').capitalize()
                    lines.append(f"| {plain(tet_nombre)} | **{plain(n.get('nombre_griego', ''))}** | {plain(n.get('transliteracion', ''))} | {plain(n.get('nota_moderna', ''))} | {n.get('freq_hz', 0):.1f} Hz |")
                lines.append('')
            elif tipo_dc == 'monocordio':
                lines += [
                    '| Longitud de cuerda | Proporción acústica | Intervalo consonante | Frecuencia (base Do3 = 130.8 Hz) |',
                    '| --- | --- | --- | --- |',
                ]
                for div in dc.get('divisiones', []):
                    lines.append(f"| **{div.get('fraccion', '')}** | {div.get('proporcion', '')} | {plain(div.get('intervalo_moderno', ''))} | {div.get('freq_hz', 0):.1f} Hz |")
                lines.append('')
            elif tipo_dc == 'escalera_intervalos':
                lines += [
                    '| Género | Intervalo 1 (Grave) | Intervalo 2 (Medio) | Intervalo 3 (Agudo) | Ámbito total |',
                    '| --- | --- | --- | --- | --- |',
                    '| **Diatónico** | Semitono diatónico (100 c) | Tono entero (200 c) | Tono entero (200 c) | Cuarta justa (500 c) |',
                    '| **Cromático** | Semitono cromático (100 c) | Semitono diatónico (100 c) | Trihemitono (300 c) | Cuarta justa (500 c) |',
                    '| **Enarmónico** | Cuarto de tono / Díesis (50 c) | Cuarto de tono / Díesis (50 c) | Ditono mayor (400 c) | Cuarta justa (500 c) |',
                    '',
                ]
            elif tipo_dc == 'linea_temporal':
                lines += [
                    '| Siglo / Época | Teórico / Autor | Tratado o contribución principal | Datación |',
                    '| --- | --- | --- | --- |',
                ]
                for hito in dc.get('hitos', []):
                    aprox = ' *(aprox.)*' if hito.get('aproximado') else ''
                    lines.append(f"| {plain(hito.get('epoca', ''))} | **{plain(hito.get('autor', ''))}** | {plain(hito.get('obra', ''))} | {plain(hito.get('fechas', ''))}{aprox} |")
                lines.append('')


    # --- CHEAT SHEET DE PRÁCTICA ---
    lines += ['## Cheat sheet de práctica', '',
              'Consulta rápida para tener a mano durante el trabajo de hoy.', '']
    if ficha_verified and ficha and ficha.get('conceptos'):
        lines += ['| Concepto | Definición |', '| --- | --- |']
        for c in ficha['conceptos']:
            lines.append(f"| **{plain(c.get('termino', ''))}** | {plain(c.get('definicion', ''))} |")

    else:
        cheat_items = [
            item
            for visual in (result.get('visualizations') or [])
            for item in (visual.get('items') or [])
        ][:10]
        if cheat_items:
            lines += ['| Elemento | Para qué sirve |', '| --- | --- |']
            lines += [f"| {plain(item.get('label', ''))} | {plain(item.get('detail', ''))} |"
                      for item in cheat_items]
        else:
            for index, claim in enumerate(claims[:4], 1):
                clean_c = clean_student_text(str(claim.get('text', '')).strip(), by_id, is_consigna=False)
                lines.append(f"- **Clave {index}:** {plain(clean_c)}")

    lines += ['', '### Secuencia rápida de hoy', '']
    time_suffix_rx = re.compile(
        r'\s*[\(\[]\s*(?:\d+\s*(?:[-–—]|a)\s*)?\d+\s*(?:min(?:utos?)?|m|min\.)\s*[\)\]]\s*$',
        re.IGNORECASE
    )
    for index, activity in enumerate(plan.get('activities', []), 1):
        raw_title = str(activity.get('title', '')).strip()
        clean_title = time_suffix_rx.sub('', raw_title).strip()
        lines.append(
            f"- **{index}. {plain(clean_title)}** · "
            f"{activity.get('minutes', 0)} min"
        )

    # --- SECCIÓN DE AUDICIONES COMENTADAS ---
    listenings_to_render = []
    if is_polyphony:
        listenings_to_render = POLYPHONY_15TH_CENTURY_LISTENINGS
    elif is_egypt:
        listenings_to_render = ANCIENT_EGYPT_LISTENINGS
    elif not is_ntam:
        from docente_ai.teaching.audiciones import find_audiciones_for_topic, is_audicion_verified
        crit = str(context.get('teacher_criteria', ''))
        cat_matches = find_audiciones_for_topic(topic_raw, crit, limit=4)
        if cat_matches:
            for item in cat_matches:
                if not is_audicion_verified(item):
                    continue
                links = [{'label': 'Escuchar en YouTube', 'url': item['url']}] if item.get('url') and 'youtube' in item['url'] else []
                listenings_to_render.append({
                    'index': len(listenings_to_render) + 1,
                    'composer': item.get('compositor') or 'Tradicional / Anónimo',
                    'title': item.get('obra') or 'Pieza de estudio',
                    'subtitle': item.get('movimiento') or '',
                    'performer': item.get('interprete') or 'Grabación recomendada',
                    'anthology': item.get('bibliografia') or 'Catálogo de audiciones verificadas de Arkhé',
                    'links': links,
                    'teacher_note': item.get('comentario_docente') or '',
                    'points': item.get('puntos_escucha') or ['Audición atenta y análisis formal guiado.']
                })

    has_listenings = bool(listenings_to_render)
    if has_listenings:
        lines += ['', '## 04 · Relación de audiciones comentadas', '']
        for item in listenings_to_render:
            lines += [
                f"### Audición {item['index']}: {plain(item['composer'])} — *{plain(item['title'])}*",
            ]
            if item.get('subtitle'):
                lines.append(f"- **Tipo / Contexto:** {plain(item['subtitle'])}.")
            if item.get('performer'):
                lines.append(f"- **Grabación e intérpretes:** {plain(item['performer'])}.")
            if item.get('links'):
                lines.append(f"- **Enlaces YouTube:** " + ' · '.join(f"[{plain(l['label'])}]({l['url']})" for l in item['links']))
            if item.get('teacher_note'):
                lines.append(f"- **Criterio didáctico del profesor:** *{plain(item['teacher_note'])}*")
            if item.get('anthology'):
                lines.append(f"- **Fuente / Antología:** {plain(item['anthology'])}.")
            if item.get('points'):
                lines.append(f"- **Guía de escucha activa:** " + ' '.join(plain(p) for p in item['points']))
            lines.append('')

    # --- TRABAJO EN CLASE (Única lista de tareas de aula) ---
    lines += ['', '## Trabajo en clase', '']
    elapsed = 0
    time_suffix_rx = re.compile(
        r'\s*[\(\[]\s*(?:\d+\s*(?:[-–—]|a)\s*)?\d+\s*(?:min(?:utos?)?|m|min\.)\s*[\)\]]\s*$',
        re.IGNORECASE
    )
    grouping_labels = {
        'individual': 'Individual',
        'grupo': 'En grupo',
        'colectivo': 'Colectivo',
    }
    for index, activity in enumerate(plan.get('activities', []), 1):
        minutes = activity.get('minutes', 0)
        raw_title = str(activity.get('title', '')).strip()
        clean_title = time_suffix_rx.sub('', raw_title).strip()
        grouping_key = activity.get('grouping')
        mode_tag = f" [{grouping_labels.get(grouping_key, grouping_key.capitalize())}]" if grouping_key else ""
        lines += [
            f"### {index}. {plain(clean_title)}{mode_tag} · {elapsed}–{elapsed + minutes} min", '',
        ]
        task_text = clean_student_text(activity.get('student_task') or activity.get('instructions', ''), by_id, is_consigna=True)
        if task_text:
            lines += [f"- **Tarea:** {plain(task_text)}"]
        if activity.get('deliverable'):
            deliv_text = clean_student_text(str(activity['deliverable']), by_id, is_consigna=True)
            lines += [f"- **Entregable:** {plain(deliv_text)}"]
        lines.append('')
        elapsed += minutes

    # Tareas adicionales para casa solo si la ficha está verificada (sin sumar a los 60 minutos de clase)
    if ficha_verified and ficha and ficha.get('tareas_adicionales_casa'):
        lines += ['### Tareas adicionales para casa', '']
        for t in ficha.get('tareas_adicionales_casa', []):
            lines += [
                f"- **{plain(t.get('titulo', ''))}** [{plain(t.get('tag', ''))}]: {plain(t.get('objetivo', ''))}",
            ]
        lines.append('')

    lines += ['## Material necesario', '']
    rendered_resources = []
    for item in plan.get('resources', []):
        formatted = format_student_resource(item, by_id)
        if formatted:
            rendered_resources.append(formatted)
    lines += ['- ' + plain(r) for r in rendered_resources]

    # Bibliografía del alumno generada solo con fuentes realmente citadas, deduplicadas por autor
    seen_authors = set()
    student_sources = []
    for item in run.get('evidence') or []:
        meta = item.get('metadata') or {}
        stitle = str(meta.get('title') or '')
        if not stitle or 'Fuente de evaluación:' in stitle or 'prueba' in stitle.lower():
            continue
        raw_authors = list(meta.get('authors') or [])
        norm_authors = tuple(normalize_authors_display(raw_authors))
        primary_author = norm_authors[0].lower().strip() if norm_authors else None
        if primary_author and primary_author in seen_authors:
            continue
        if primary_author:
            seen_authors.add(primary_author)
        student_sources.append((stitle, norm_authors, meta.get('year')))

    if student_sources:
        lines += ['', '## Fuentes de consulta', '']
        for title, authors, year in student_sources:
            detail = ', '.join(authors) if authors else ''
            if year:
                detail += (' · ' if detail else '') + str(year)
            lines.append(f"- {plain(title or 'Fuente sin título')}{' — ' + plain(detail) if detail else ''}")

    # --- ANEXO: TEXTOS PARA TRABAJAR ---
    candidate_quotes = []
    seen_q = set()
    for claim in claims:
        for ev in claim.get('evidence', []):
            q = (ev.get('quote') or '').strip()
            sid = ev.get('source_id')
            if q and len(q) >= 20 and q not in seen_q:
                seen_q.add(q)
                candidate_quotes.append((sid, q))
    if not candidate_quotes:
        for ev in (run.get('evidence') or []):
            for p in ev.get('passages', []):
                q = (p.get('text') or '').strip()
                if q and len(q) >= 20 and q not in seen_q:
                    seen_q.add(q)
                    candidate_quotes.append((ev.get('source_id'), q))

    if candidate_quotes:
        selected_quotes = candidate_quotes[:6]
        lines += ['', '## Anexo · Textos para trabajar', '',
                  'Pasajes seleccionados de las fuentes para el análisis activo, comentario y debate en el aula:', '']
        by_id_student = {item['source_id']: item for item in (run.get('evidence') or [])}
        for idx, (sid, raw_quote) in enumerate(selected_quotes, 1):
            src = by_id_student.get(sid, {})
            cit = format_source_brief_citation(src)
            trans_text, was_trans = translate_quote_if_needed(raw_quote)
            trans_tag = ' *(Traducción del original inglés)*' if was_trans else ''
            lines += [
                f"### Texto {idx}: {plain(cit)}",
                f"> «{plain(clean_student_text(trans_text, by_id, is_consigna=False))}»{trans_tag}",
                ''
            ]

    return clean_terminologia_output(sanitize_student_output('\n'.join(lines).rstrip() + '\n'))


def _build_presentation_slides(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Construye la secuencia estructurada de diapositivas para proyección pedagógica."""
    context = (run.get('request') or {}).get('pedagogy') or {}
    result = run.get('result') or {}
    plan = result.get('plan') or {}
    group = context.get('group') or {}
    session = context.get('session') or {}
    topic_raw = str(run.get('original_topic') or (run.get('request') or {}).get('original_topic') or (run.get('request') or {}).get('question', '')).strip()
    display_title = run.get('display_title') or (run.get('request') or {}).get('display_title')
    if not display_title:
        from docente_ai.teaching.terms import normalize_topic
        norm = normalize_topic(topic_raw)
        display_title = (norm[:1].upper() + norm[1:]) if norm else topic_raw
    topic = display_title or 'Presentación pedagógica'

    by_id = {item['source_id']: item for item in (run.get('evidence') or []) if 'source_id' in item}
    slides: list[dict[str, Any]] = []

    # 1. Diapositiva de Portada
    meta_badges: list[str] = []
    if group.get('name'):
        lvl = f" ({group['level']})" if group.get('level') else ""
        meta_badges.append(f"{group['name']}{lvl}")
    if context.get('duration_minutes'):
        meta_badges.append(f"{context['duration_minutes']} min")
    if session.get('date'):
        meta_badges.append(str(session['date']))

    slides.append({
        'tipo': 'portada',
        'kicker': 'Presentación pedagógica · Arkhé',
        'titulo': topic,
        'subtitulo': 'Material docente estructurado para proyección en el aula',
        'metadatos': meta_badges,
    })

    # 2. Hoja de ruta / Objetivos
    objectives = [
        clean_student_text(item, by_id, is_consigna=True)
        for item in plan.get('objectives', [])
        if str(item).strip()
    ]
    if objectives:
        slides.append({
            'tipo': 'objetivos',
            'kicker': 'Hoja de ruta',
            'titulo': '¿Qué vamos a trabajar hoy?',
            'subtitulo': 'Objetivos de aprendizaje de la sesión',
            'items': objectives,
        })

    # 3. Conceptos teóricos y contenidos clave (claims)
    claims = result.get('claims') or []
    resolved_by_id = {r.get('request_id'): r for r in (result.get('resolved_music_requests') or [])}
    for idx, claim in enumerate(claims, 1):
        ctitle = claim.get('title') or f"Concepto {idx}"
        csummary = str(claim.get('student_summary') or claim.get('text', '')).strip()
        cleaned_summary = clean_student_text(csummary, by_id, is_consigna=False)
        pts = [str(p).strip() for p in (claim.get('key_points') or []) if str(p).strip()]

        ejemplo_info = None
        for ex_id in claim.get('example_ids') or []:
            item = resolved_by_id.get(ex_id) or {}
            ej = item.get('ejemplo') or {}
            if item.get('status') == 'resuelto_repertorio' and ej:
                obra = ' · '.join(x for x in (ej.get('obra', ''), ej.get('seccion', '')) if x)
                ejemplo_info = {
                    'obra': obra,
                    'compositor': ej.get('compositor', ''),
                    'compases': ej.get('compases', '1-8'),
                    'que_observar': ej.get('que_observar', ''),
                }
                break

        slides.append({
            'tipo': 'concepto',
            'kicker': f'Contenido clave {idx:02d}',
            'titulo': ctitle,
            'resumen': cleaned_summary,
            'puntos_clave': pts,
            'ejemplo': ejemplo_info,
        })

    # 4. Esquemas didácticos y visualizaciones
    visualizations = result.get('visualizations') or []
    for visual in visualizations:
        slides.append({
            'tipo': 'esquema',
            'kicker': 'Esquema conceptual',
            'titulo': visual.get('title', 'Estructura'),
            'caption': visual.get('caption', ''),
            'items': visual.get('items', []),
        })

    didactic_comps = result.get('resolved_didactic_components') or []
    for dc in didactic_comps:
        tipo_dc = dc.get('tipo', '')
        tit_dc = dc.get('titulo') or tipo_dc.replace('_', ' ').title()
        items_dc = []
        if tipo_dc == 'monocordio':
            for div in dc.get('divisiones', [])[:6]:
                items_dc.append({
                    'label': f"{div.get('fraccion', '')} ({div.get('proporcion', '')})",
                    'detail': f"{div.get('intervalo_moderno', '')} · {div.get('freq_hz', 0):.1f} Hz",
                })
        elif tipo_dc == 'tetracordos':
            afin = dc.get('afinacion_pitagorica') or {}
            for gen in (afin.get('generos') or {}).values():
                items_dc.append({
                    'label': gen.get('nombre', ''),
                    'detail': f"{gen.get('formula', '')} (cents: {' + '.join(str(c) for c in gen.get('cents', []))})",
                })
        else:
            items_dc.append({
                'label': 'Modelo acústico',
                'detail': dc.get('descripcion', 'Cálculo determinista de teoría musical'),
            })

        slides.append({
            'tipo': 'componente_didactico',
            'kicker': 'Modelo didáctico determinista',
            'titulo': tit_dc,
            'caption': dc.get('descripcion', ''),
            'items': items_dc,
        })

    # 5. Audiciones comentadas
    listenings: list[dict[str, Any]] = []
    if _is_15th_century_topic(run):
        listenings = POLYPHONY_15TH_CENTURY_LISTENINGS
    elif _is_ancient_egypt_topic(run):
        listenings = ANCIENT_EGYPT_LISTENINGS
    else:
        from docente_ai.teaching.audiciones import find_audiciones_for_topic, is_audicion_verified
        cat = find_audiciones_for_topic(topic_raw, str(context.get('teacher_criteria', '')), limit=4)
        listenings = [item for item in cat if is_audicion_verified(item)]

    if listenings:
        items_aud = []
        for l in listenings:
            obra = l.get('obra') or l.get('title') or l.get('titulo') or ''
            comp = l.get('compositor') or l.get('composer') or ''
            fecha = f" ({l['ano_periodo']})" if l.get('ano_periodo') else ""
            guia = l.get('criterios_escucha') or l.get('que_escuchar') or l.get('aspectos_clave') or l.get('subtitle') or ''
            items_aud.append({
                'obra': f"{obra} — {comp}{fecha}".strip(' —'),
                'guia': guia,
            })
        slides.append({
            'tipo': 'audiciones',
            'kicker': 'Audición activa',
            'titulo': 'Repertorio y audiciones comentadas',
            'subtitulo': 'Aspectos clave a observar durante la audición en clase',
            'audiciones': items_aud,
        })

    # 6. Actividades prácticas de aula
    activities = plan.get('activities') or []
    for idx, act in enumerate(activities, 1):
        atitle = act.get('title') or f"Actividad {idx}"
        mins = act.get('minutes', 0)
        grouping = act.get('grouping') or 'En el aula'
        task = clean_student_text(act.get('student_task') or act.get('instructions', ''), by_id, is_consigna=True)
        slides.append({
            'tipo': 'actividad',
            'numero': idx,
            'kicker': f'Actividad {idx:02d} · {mins} min',
            'titulo': atitle,
            'agrupamiento': grouping,
            'minutos': mins,
            'consigna': task,
            'recursos': act.get('materials') or act.get('resources') or [],
        })

    # 7. Diapositiva de Cierre
    slides.append({
        'tipo': 'cierre',
        'kicker': 'Cierre de la sesión',
        'titulo': 'Conclusiones y balance',
        'subtitulo': 'Puntos esenciales fijados en el aula',
        'items': [
            'Puesta en común de dudas y resultados del trabajo práctico.',
            'Síntesis de los conceptos clave abordados.',
            'Orientaciones y entrega para la siguiente sesión.',
        ],
    })

    return slides


def render_presentation_md(run: dict[str, Any]) -> str:
    """Genera diapositivas en Markdown delimitadas por --- para proyectar en el aula."""
    slides_data = _build_presentation_slides(run)
    md_slides: list[str] = []

    for s in slides_data:
        stype = s.get('tipo')
        if stype == 'portada':
            kicker_str = f"{s.get('kicker')} · " if s.get('kicker') else ""
            lines = [
                f"# {plain(s['titulo'])}",
                f"### {plain(kicker_str)}{plain(s['subtitulo'])}",
                "",
                *[f"- **{plain(m)}**" for m in s.get('metadatos', [])],
            ]
        elif stype == 'objetivos':
            lines = [
                f"## {plain(s['titulo'])}",
                f"### {plain(s['subtitulo'])}",
                "",
                *[f"- {plain(item)}" for item in s.get('items', [])],
            ]
        elif stype == 'concepto':
            lines = [
                f"## {plain(s['titulo'])}",
                "",
                f"> {plain(s['resumen'])}",
            ]
            if s.get('puntos_clave'):
                lines.extend(["", "**Aspectos clave:**", *[f"- {plain(p)}" for p in s['puntos_clave']]])
            ej = s.get('ejemplo')
            if ej:
                lines.extend([
                    "",
                    f"🎼 **Ejemplo:** {plain(ej['obra'])} — {plain(ej['compositor'])} (c. {plain(ej['compases'])})",
                ])
                if ej.get('que_observar'):
                    lines.append(f"*Qué observar:* {plain(ej['que_observar'])}")
        elif stype in ('esquema', 'componente_didactico'):
            lines = [f"## {plain(s['titulo'])}"]
            if s.get('caption'):
                lines.extend(["", f"*{plain(s['caption'])}*"])
            lines.append("")
            for itm in s.get('items', []):
                lines.append(f"- **{plain(itm.get('label', ''))}:** {plain(itm.get('detail', ''))}")
        elif stype == 'audiciones':
            lines = [
                f"## {plain(s['titulo'])}",
                f"### {plain(s['subtitulo'])}",
                "",
            ]
            for aud in s.get('audiciones', []):
                lines.append(f"- 🎧 **{plain(aud['obra'])}**")
                if aud.get('guia'):
                    lines.append(f"  *En qué fijarse:* {plain(aud['guia'])}")
        elif stype == 'actividad':
            lines = [
                f"## Actividad {s.get('numero', 1)} · {plain(s['titulo'])}",
                f"### ⏱️ {s.get('minutos', 0)} min · Modalidad: {plain(s.get('agrupamiento', ''))}",
                "",
                "**Consigna:**",
                plain(s.get('consigna', '')),
            ]
        elif stype == 'cierre':
            kicker_str = f"{s.get('kicker')} · " if s.get('kicker') else ""
            lines = [
                f"## {plain(kicker_str)}{plain(s['titulo'])}",
                f"### {plain(s['subtitulo'])}",
                "",
                *[f"- {plain(item)}" for item in s.get('items', [])],
            ]
        else:
            lines = [f"## {plain(s.get('titulo', 'Diapositiva'))}", "", plain(s.get('resumen', ''))]

        md_slides.append('\n'.join(lines).strip())

    raw_output = '\n\n---\n\n'.join(md_slides)
    return clean_terminologia_output(sanitize_student_output(raw_output + '\n'))


def render_presentation_html(run: dict[str, Any]) -> str:
    """Genera una presentación HTML interactiva y autónoma para proyectar en el aula."""
    slides_data = _build_presentation_slides(run)
    context = (run.get('request') or {}).get('pedagogy') or {}
    group = context.get('group') or {}
    group_name = html.escape(group.get('name') or 'Espacio docente', quote=True)
    main_title = html.escape(slides_data[0]['titulo'] if slides_data else 'Presentación', quote=True)

    deck_html_parts: list[str] = []
    for idx, s in enumerate(slides_data):
        active_cls = ' active' if idx == 0 else ''
        stype = s.get('tipo')
        kicker_html = f"<div class=\"slide-kicker\">{html.escape(s.get('kicker', ''), quote=False)}</div>" if s.get('kicker') else ""
        title_html = f"<h1 class=\"slide-title\">{html.escape(s.get('titulo', ''), quote=False)}</h1>"

        body_lines: list[str] = []
        if stype == 'portada':
            if s.get('subtitulo'):
                body_lines.append(f"<p class=\"slide-lead\">{html.escape(s['subtitulo'], quote=False)}</p>")
            meta_chips = ''.join(f"<span class=\"slide-chip\">{html.escape(m, quote=False)}</span>" for m in s.get('metadatos', []))
            if meta_chips:
                body_lines.append(f"<div class=\"slide-chips\">{meta_chips}</div>")
        elif stype == 'objetivos':
            if s.get('subtitulo'):
                body_lines.append(f"<p class=\"slide-lead\">{html.escape(s['subtitulo'], quote=False)}</p>")
            items_li = ''.join(f"<li><span class=\"bullet-icon\">✓</span><div>{html.escape(item, quote=False)}</div></li>" for item in s.get('items', []))
            body_lines.append(f"<ul class=\"slide-objectives\">{items_li}</ul>")
        elif stype == 'concepto':
            if s.get('resumen'):
                body_lines.append(f"<div class=\"slide-quote\"><p>{html.escape(s['resumen'], quote=False)}</p></div>")
            if s.get('puntos_clave'):
                pts_li = ''.join(f"<li>{html.escape(p, quote=False)}</li>" for p in s['puntos_clave'])
                body_lines.append(f"<div class=\"slide-keypoints\"><h3>Aspectos clave</h3><ul>{pts_li}</ul></div>")
            ej = s.get('ejemplo')
            if ej:
                obs_html = f"<p class=\"example-obs\"><strong>Qué observar:</strong> {html.escape(ej['que_observar'], quote=False)}</p>" if ej.get('que_observar') else ""
                body_lines.append(
                    f"<div class=\"slide-example-box\">"
                    f"<div class=\"example-head\">🎼 <strong>{html.escape(ej['obra'], quote=False)}</strong> — {html.escape(ej['compositor'], quote=False)} (c. {html.escape(ej['compases'], quote=False)})</div>"
                    f"{obs_html}"
                    f"</div>"
                )
        elif stype in ('esquema', 'componente_didactico'):
            if s.get('caption'):
                body_lines.append(f"<p class=\"slide-lead\">{html.escape(s['caption'], quote=False)}</p>")
            cards = ''.join(
                f"<div class=\"slide-schema-card\"><strong>{html.escape(itm.get('label', ''), quote=False)}</strong><p>{html.escape(itm.get('detail', ''), quote=False)}</p></div>"
                for itm in s.get('items', [])
            )
            body_lines.append(f"<div class=\"slide-schema-grid\">{cards}</div>")
        elif stype == 'audiciones':
            if s.get('subtitulo'):
                body_lines.append(f"<p class=\"slide-lead\">{html.escape(s['subtitulo'], quote=False)}</p>")
            aud_cards = []
            for aud in s.get('audiciones', []):
                guia_html = f"<p>{html.escape(aud['guia'], quote=False)}</p>" if aud.get('guia') else ""
                aud_cards.append(f"<div class=\"slide-listening-card\"><div class=\"aud-icon\">🎧</div><div><h4>{html.escape(aud['obra'], quote=False)}</h4>{guia_html}</div></div>")
            body_lines.append(f"<div class=\"slide-listening-grid\">{''.join(aud_cards)}</div>")
        elif stype == 'actividad':
            body_lines.append(
                f"<div class=\"slide-activity-meta\">"
                f"<span class=\"slide-chip highlight\">⏱️ {s.get('minutos', 0)} minutos</span>"
                f"<span class=\"slide-chip\">Modalidad: {html.escape(s.get('agrupamiento', 'En el aula'), quote=False)}</span>"
                f"</div>"
            )
            body_lines.append(f"<div class=\"slide-activity-task\"><h3>Consigna de trabajo</h3><p>{html.escape(s.get('consigna', ''), quote=False)}</p></div>")
            if s.get('recursos'):
                recs_str = ', '.join(html.escape(str(r), quote=False) for r in s['recursos'])
                body_lines.append(f"<p class=\"slide-resources\"><strong>Recursos:</strong> {recs_str}</p>")
        elif stype == 'cierre':
            if s.get('subtitulo'):
                body_lines.append(f"<p class=\"slide-lead\">{html.escape(s['subtitulo'], quote=False)}</p>")
            items_li = ''.join(f"<li><span class=\"bullet-icon\">✦</span><div>{html.escape(item, quote=False)}</div></li>" for item in s.get('items', []))
            body_lines.append(f"<ul class=\"slide-objectives\">{items_li}</ul>")
        else:
            if s.get('resumen'):
                body_lines.append(f"<p>{html.escape(s['resumen'], quote=False)}</p>")

        body_html = '\n'.join(body_lines)
        deck_html_parts.append(
            f"<section class=\"slide{active_cls}\" data-slide=\"{idx + 1}\" aria-label=\"Diapositiva {idx + 1}\">\n"
            f"  <div class=\"slide-header\">{kicker_html}{title_html}</div>\n"
            f"  <div class=\"slide-content\">{body_html}</div>\n"
            f"  <footer class=\"slide-footer\"><span>Arkhé · {group_name}</span><span>{idx + 1} / {len(slides_data)}</span></footer>\n"
            f"</section>"
        )

    deck_html = '\n'.join(deck_html_parts)
    total_slides = len(slides_data)

    page_html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{main_title} · Presentación Arkhé</title>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --ink: #f8fafc;
      --ink-muted: #94a3b8;
      --accent: #0f766e;
      --accent-light: #2dd4bf;
      --gold: #f59e0b;
      --border: #1f2937;
      --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --serif: Baskerville, Georgia, serif;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      width: 100%; height: 100%;
      background: var(--bg);
      color: var(--ink);
      font-family: var(--sans);
      overflow: hidden;
      user-select: none;
    }}
    .presentation-container {{
      width: 100vw; height: 100vh;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      position: relative;
    }}
    .slide-deck {{
      width: 94vw; max-width: 1400px;
      height: 86vh; max-height: 840px;
      aspect-ratio: 16 / 9;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
      display: flex; flex-direction: column;
      position: relative; overflow: hidden;
    }}
    .slide {{
      display: none; width: 100%; height: 100%;
      padding: 3rem 4rem 2.5rem;
      flex-direction: column; justify-content: space-between;
      animation: fadeIn 0.25s ease-out;
    }}
    .slide.active {{ display: flex; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .slide-header {{ margin-bottom: 1.5rem; }}
    .slide-kicker {{
      font-size: 0.95rem; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.08em; color: var(--accent-light); margin-bottom: 0.5rem;
    }}
    .slide-title {{
      font-family: var(--serif);
      font-size: clamp(2rem, 3.8vw, 3.2rem);
      line-height: 1.15; color: var(--ink);
      letter-spacing: -0.02em;
    }}
    .slide-lead {{
      font-size: clamp(1.15rem, 1.8vw, 1.45rem);
      color: var(--ink-muted); margin-bottom: 1.5rem; line-height: 1.4;
    }}
    .slide-content {{
      flex: 1; display: flex; flex-direction: column;
      justify-content: center; min-height: 0; overflow-y: auto;
    }}
    .slide-chips {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1.5rem; }}
    .slide-chip {{
      padding: 0.4rem 1rem; border-radius: 9999px; font-size: 1rem;
      background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border); color: var(--ink);
    }}
    .slide-chip.highlight {{ background: rgba(45, 212, 191, 0.15); border-color: var(--accent-light); color: var(--accent-light); font-weight: 600; }}
    .slide-objectives {{ list-style: none; display: flex; flex-direction: column; gap: 1rem; }}
    .slide-objectives li {{
      display: flex; align-items: flex-start; gap: 1rem;
      font-size: clamp(1.2rem, 2vw, 1.6rem); line-height: 1.4;
    }}
    .bullet-icon {{ color: var(--accent-light); font-weight: bold; flex-shrink: 0; }}
    p {{ color: var(--ink); }}
    .slide-quote {{
      border-left: 5px solid var(--accent-light);
      padding: 1.25rem 1.75rem; background: rgba(15, 118, 110, 0.28);
      border-radius: 0 10px 10px 0; font-size: clamp(1.2rem, 2vw, 1.55rem);
      line-height: 1.55; margin-bottom: 1.5rem;
      border-top: 1px solid rgba(45, 212, 191, 0.2);
      border-right: 1px solid rgba(45, 212, 191, 0.2);
      border-bottom: 1px solid rgba(45, 212, 191, 0.2);
    }}
    .slide-quote p {{
      color: #ffffff !important;
      font-weight: 500;
    }}
    .slide-keypoints {{ margin-top: 0.5rem; }}
    .slide-keypoints h3 {{ font-size: 1.15rem; color: var(--gold); margin-bottom: 0.5rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }}
    .slide-keypoints ul {{ list-style: square; padding-left: 1.5rem; display: flex; flex-direction: column; gap: 0.45rem; }}
    .slide-keypoints li {{ font-size: clamp(1.1rem, 1.6vw, 1.35rem); color: #f8fafc; line-height: 1.45; }}
    .slide-example-box {{
      margin-top: 1rem; padding: 1rem 1.35rem;
      background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.5);
      border-radius: 10px;
    }}
    .example-head {{ font-size: 1.15rem; color: var(--gold); margin-bottom: 0.25rem; font-weight: 600; }}
    .example-obs {{ font-size: 1.05rem; color: #f8fafc; }}
    .slide-schema-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }}
    .slide-schema-card {{
      background: rgba(255, 255, 255, 0.06); border: 1px solid var(--border);
      padding: 1.25rem; border-radius: 10px;
    }}
    .slide-schema-card strong {{ display: block; font-size: 1.2rem; color: var(--accent-light); margin-bottom: 0.4rem; }}
    .slide-schema-card p {{ font-size: 1.05rem; color: #f1f5f9; line-height: 1.45; }}
    .slide-listening-grid {{ display: flex; flex-direction: column; gap: 1rem; }}
    .slide-listening-card {{
      display: flex; align-items: center; gap: 1.25rem;
      background: rgba(255, 255, 255, 0.06); border: 1px solid var(--border);
      padding: 1.25rem; border-radius: 10px;
    }}
    .aud-icon {{ font-size: 2rem; }}
    .slide-listening-card h4 {{ font-size: 1.25rem; color: #ffffff; margin-bottom: 0.25rem; }}
    .slide-listening-card p {{ font-size: 1.05rem; color: #e2e8f0; }}
    .slide-activity-meta {{ display: flex; gap: 0.75rem; margin-bottom: 1.25rem; }}
    .slide-activity-task {{
      background: rgba(255, 255, 255, 0.06); border: 1px solid var(--border);
      padding: 1.75rem; border-radius: 12px; margin-bottom: 1rem;
    }}
    .slide-activity-task h3 {{ font-size: 1.1rem; color: var(--accent-light); margin-bottom: 0.6rem; text-transform: uppercase; letter-spacing: 0.04em; }}
    .slide-activity-task p {{ font-size: clamp(1.25rem, 2vw, 1.6rem); line-height: 1.5; color: #ffffff !important; font-weight: 500; }}
    .slide-resources {{ font-size: 1.05rem; color: #e2e8f0; }}
    .slide-footer {{
      display: flex; justify-content: space-between; align-items: center;
      padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 0.95rem; color: var(--ink-muted);
    }}
    .presentation-controls {{
      position: fixed; bottom: 1.5rem; display: flex; align-items: center;
      gap: 1rem; background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(12px);
      padding: 0.6rem 1.25rem; border-radius: 9999px; border: 1px solid var(--border);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5); z-index: 100;
    }}
    .presentation-controls button {{
      background: none; border: none; color: var(--ink); cursor: pointer;
      font-size: 1rem; padding: 0.35rem 0.65rem; border-radius: 6px;
      display: inline-flex; align-items: center; justify-content: center;
      transition: background 0.15s;
    }}
    .presentation-controls button:hover {{ background: rgba(255, 255, 255, 0.12); }}
    .slide-counter {{ font-size: 0.95rem; font-weight: 600; color: var(--ink-muted); min-width: 65px; text-align: center; }}
    .progress-bar-container {{
      position: fixed; bottom: 0; left: 0; width: 100%; height: 4px; background: rgba(255, 255, 255, 0.05);
    }}
    .progress-bar {{ height: 100%; width: {(1.0 / total_slides * 100) if total_slides else 0}%; background: var(--accent-light); transition: width 0.2s; }}
    @media print {{
      body, html {{ overflow: visible !important; background: #fff !important; color: #000 !important; }}
      .presentation-container {{ display: block !important; height: auto !important; }}
      .presentation-controls, .progress-bar-container {{ display: none !important; }}
      .slide-deck {{ width: 100% !important; height: auto !important; aspect-ratio: auto !important; border: none !important; box-shadow: none !important; background: #fff !important; }}
      .slide {{ display: flex !important; page-break-after: always; break-after: page; height: 100vh !important; padding: 2rem !important; color: #000 !important; background: #fff !important; }}
      .slide-title {{ color: #000 !important; }}
      .slide-lead, .slide-keypoints li, .slide-footer {{ color: #475569 !important; }}
      .slide-quote {{ background: #f1f5f9 !important; color: #000 !important; border-left-color: #0f766e !important; }}
      .slide-schema-card, .slide-activity-task, .slide-listening-card {{ background: #f8fafc !important; border-color: #cbd5e1 !important; color: #000 !important; }}
    }}
  </style>
</head>
<body>
  <div class="presentation-container">
    <main class="slide-deck">
{deck_html}
    </main>
    <nav class="presentation-controls" aria-label="Controles de la presentación">
      <button id="btn-prev" aria-label="Anterior diapositiva" title="Anterior (← o Espacio)">◀</button>
      <span class="slide-counter" id="counter">1 / {total_slides}</span>
      <button id="btn-next" aria-label="Siguiente diapositiva" title="Siguiente (→ o Espacio)">▶</button>
      <button id="btn-fs" aria-label="Pantalla completa" title="Pantalla completa (F)">⛶</button>
      <button id="btn-print" aria-label="Imprimir presentación" title="Imprimir / PDF">🖨️</button>
    </nav>
    <div class="progress-bar-container"><div class="progress-bar" id="progress"></div></div>
  </div>
  <script>
    (function() {{
      const slides = document.querySelectorAll('.slide');
      const counter = document.getElementById('counter');
      const progress = document.getElementById('progress');
      const total = slides.length;
      let current = 0;

      function update(idx) {{
        if (idx < 0) idx = 0;
        if (idx >= total) idx = total - 1;
        current = idx;
        slides.forEach((s, i) => s.classList.toggle('active', i === current));
        if (counter) counter.textContent = (current + 1) + ' / ' + total;
        if (progress) progress.style.width = (((current + 1) / total) * 100) + '%';
      }}

      document.getElementById('btn-prev').addEventListener('click', () => update(current - 1));
      document.getElementById('btn-next').addEventListener('click', () => update(current + 1));
      document.getElementById('btn-fs').addEventListener('click', () => {{
        if (!document.fullscreenElement) {{
          document.documentElement.requestFullscreen().catch(() => {{}});
        }} else {{
          document.exitFullscreen().catch(() => {{}});
        }}
      }});
      document.getElementById('btn-print').addEventListener('click', () => window.print());

      window.addEventListener('keydown', (e) => {{
        if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{
          e.preventDefault(); update(current + 1);
        }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
          e.preventDefault(); update(current - 1);
        }} else if (e.key === 'Home') {{
          e.preventDefault(); update(0);
        }} else if (e.key === 'End') {{
          e.preventDefault(); update(total - 1);
        }} else if (e.key === 'f' || e.key === 'F') {{
          if (!document.fullscreenElement) {{
            document.documentElement.requestFullscreen().catch(() => {{}});
          }} else {{
            document.exitFullscreen().catch(() => {{}});
          }}
        }} else if (e.key === 'p' && (e.ctrlKey || e.metaKey)) {{
          // Permitir atajo nativo
        }}
      }});
    }})();
  </script>
</body>
</html>"""

    return clean_terminologia_output(sanitize_student_output(page_html))


def clean_terminologia_output(text: str) -> str:
    """Normaliza variantes no canónicas en la salida renderizada (ej. jastio -> iastio)."""
    text = re.sub(r'\bjastio\b', 'iastio', text)
    text = re.sub(r'\bJastio\b', 'Iastio', text)
    return text



def render_general(run: dict) -> str:
    topic_raw = str(run.get('original_topic') or (run.get('request') or {}).get('original_topic') or (run.get('request') or {}).get('question', '')).strip()
    display_title = run.get('display_title') or (run.get('request') or {}).get('display_title')
    if not display_title:
        from docente_ai.teaching.terms import normalize_topic
        norm = normalize_topic(topic_raw)
        display_title = (norm[:1].upper() + norm[1:]) if norm else topic_raw
    topic_lines = [f"Tema: {plain(display_title)}"]
    if topic_raw and topic_raw.strip().lower() != display_title.strip().lower():
        topic_lines.append(f"Tema original: {plain(topic_raw)}")
    lines = ['# Consulta documentada', '', f"Registro: {run['id']}", '',
             *topic_lines, '']
    state = run.get('status', 'unknown')
    if state in ('failed', 'cancelled', 'running'):
        lines += [f'Estado: {state}. No hay una respuesta validada.', '', plain(run.get('error') or 'Operación incompleta.')]
        return '\n'.join(lines) + '\n'
    if state == 'abstained':
        lines.append(NO_EVIDENCE)
        return '\n'.join(lines) + '\n'

    by_id = {item['source_id']: item for item in (run.get('evidence') or [])}
    claims = (run.get('result') or {}).get('claims', [])

    has_unbacked = any(
        not any(
            is_bibliographic_origin(by_id.get(ev.get('source_id'), {}))
            for ev in claim.get('evidence', [])
        )
        for claim in claims
    )
    has_pending_ia = any(
        (by_id.get(ev.get('source_id'), {}).get('metadata') or {}).get('origin') == 'posible_generado_ia'
        for claim in claims for ev in claim.get('evidence', [])
    )

    review = run.get('review')
    if review and review.get('action') == 'approved':
        lines += ['**Propuesta aprobada por el profesor.**', '']
    else:
        disclaimer = 'Las referencias y citas textuales se han comprobado; eso no garantiza que cada afirmación sea correcta o esté suficientemente sustentada.'
        if has_unbacked:
            disclaimer += '\n\nAviso: algunos contenidos carecen de fuente bibliográfica en la biblioteca (se apoyan en notas del profesor o deducción de IA).'
        if has_pending_ia:
            disclaimer += '\n\nAviso: la propuesta utiliza fuentes pendientes de confirmar su origen (posible texto generado por IA).'
        lines += ['**Borrador generado por IA, pendiente de revisión del profesor.**', '', disclaimer, '']

    for index, claim in enumerate(claims, 1):
        label = claim_synthesis_label(claim, by_id)
        lines += [f"**Contenido {index} — {label}:** {plain(claim.get('text', ''))}", '']
        lines += format_claim_sources(claim, by_id) + ['']

    for visual in (run.get('result') or {}).get('visualizations', []):
        lines += ['## Esquema documentado', '', f"### {plain(visual.get('title', ''))}", '']
        if visual.get('type') == 'table':
            lines += ['| Elemento | Relación o función |', '| --- | --- |']
            lines += [f"| {plain(item.get('label', ''))} | {plain(item.get('detail', ''))} |" for item in visual.get('items', [])]
        else:
            connector = ' → ' if visual.get('type') == 'sequence' else ' ⇄ '
            lines.append(connector.join(f"**{plain(item.get('label', ''))}** ({plain(item.get('detail', ''))})" for item in visual.get('items', [])))
        lines += ['', plain(visual.get('caption', '')), '']

    lines += ['## Fuentes documentales y citas contrastadas', '']
    all_citations = []
    seen = set()
    for claim in claims:
        for item in claim.get('evidence', []):
            key = (item.get('source_id'), item.get('quote'))
            if key not in seen:
                seen.add(key)
                all_citations.append(item)
    for visual in (run.get('result') or {}).get('visualizations', []):
        for item in visual.get('evidence', []):
            key = (item.get('source_id'), item.get('quote'))
            if key not in seen:
                seen.add(key)
                all_citations.append(item)

    if all_citations:
        for item in all_citations:
            source = by_id.get(item.get('source_id'))
            if source:
                category = 'Fuente documental' if source.get('category') == 'documental' else 'Material del profesor'
                lines += [f"{category} [{source['source_id']}]: {plain(citation(source.get('metadata') or {}, source.get('locator') or {}))}", '',
                          '> ' + plain(item.get('quote', '')).replace('\n', '\n> '), '']
    elif run.get('evidence'):
        for source in run.get('evidence'):
            category = 'Fuente documental' if source.get('category') == 'documental' else 'Material del profesor'
            lines += [f"{category} [{source['source_id']}]: {plain(citation(source.get('metadata') or {}, source.get('locator') or {}))}", '']

    if run.get('omitted'):
        lines += ['', f"Fragmentos no enviados al modelo por presupuesto o duplicación: {len(run['omitted'])}."]
    for warning in run.get('warnings', []):
        lines += ['', '**Aviso:** ' + plain(warning)]
    if review:
        lines += ['', '---', '## Revisión del profesor', '']
        action_label = 'Aprobada' if review.get('action') == 'approved' else 'Rechazada'
        lines.append(f"**{action_label}** · {plain(review.get('reviewed_at', ''))}")
        if review.get('notes'):
            lines += ['', plain(review['notes'])]
    return '\n'.join(lines).rstrip() + '\n'


def render_pedagogy(run: dict) -> str:
    context = run['request']['pedagogy']
    group = context.get('group', {})
    topic_raw = str(run.get('original_topic') or (run.get('request') or {}).get('original_topic') or run['request'].get('question', '')).strip()
    display_title = run.get('display_title') or (run.get('request') or {}).get('display_title')
    if not display_title:
        from docente_ai.teaching.terms import normalize_topic
        normalized_topic = normalize_topic(topic_raw)
        display_title = (normalized_topic[:1].upper() + normalized_topic[1:]) if normalized_topic else topic_raw

    topic_header = plain(display_title)
    topic_lines = [f"Tema elegido: {topic_header}"]
    if topic_raw and topic_raw.strip().lower() != display_title.strip().lower():
        topic_lines.append(f"Tema original: {plain(topic_raw)}")

    lines = ['# Propuesta pedagógica', '', f"Registro: {run['id']}", '',
             *topic_lines,
             f"Grupo: {plain(group.get('name', ''))} · Nivel: {plain(group.get('level', ''))}",
             f"Duración solicitada: {context.get('duration_minutes', 0)} minutos", '',
             f"Criterios del profesor: {plain(context.get('teacher_criteria') or 'No especificados')}",
             f"Unidad elegida: {plain(context['unit']['title'] if context.get('unit') else 'No seleccionada')}", '']

    state = run.get('status', 'unknown')
    if state in ('failed', 'cancelled', 'running'):
        lines += [f'Estado: {state}. No hay una respuesta validada.', '', plain(run.get('error') or 'Operación incompleta.')]
        return '\n'.join(lines) + '\n'
    if state == 'abstained':
        lines.append(NO_EVIDENCE)
        return '\n'.join(lines) + '\n'

    result = run.get('result') or {}
    plan = result.get('plan')
    claims = result.get('claims', [])
    by_id = {item['source_id']: item for item in (run.get('evidence') or [])}
    has_unbacked = any(
        not any(
            is_bibliographic_origin(by_id.get(ev.get('source_id'), {}))
            for ev in claim.get('evidence', [])
        )
        for claim in claims
    )
    has_pending_ia = any(
        (by_id.get(ev.get('source_id'), {}).get('metadata') or {}).get('origin') == 'posible_generado_ia'
        for claim in claims for ev in claim.get('evidence', [])
    )

    review = run.get('review')
    if review and review.get('action') == 'approved':
        review_text = '**Propuesta aprobada por el profesor.**'
    else:
        disclaimer = 'Las referencias y citas textuales se han comprobado; eso no garantiza que cada afirmación sea correcta o esté suficientemente sustentada.'
        if has_unbacked:
            disclaimer += '\n\nAviso: algunos contenidos carecen de fuente bibliográfica en la biblioteca (se apoyan en notas del profesor o deducción de IA).'
        if has_pending_ia:
            disclaimer += '\n\nAviso: la propuesta utiliza fuentes pendientes de confirmar su origen (posible texto generado por IA).'
        review_text = f'**Borrador generado por IA, pendiente de revisión del profesor.**\n\n{disclaimer}'

    lines += ['---', '', '# PARTE 1 · GUÍA DOCENTE (Para el Profesor)', '', review_text, '']

    # --- TABLA DE COBERTURA DE REQUISITOS DEL PROFESOR ---
    requirements = context.get('requirements') or (run.get('request') or {}).get('requirements') or []
    coverage = (run.get('result') or {}).get('coverage') or []
    if coverage or requirements:
        lines += ['## Cobertura de requisitos del profesor', '']
        cov_by_id = {item.get('requirement_id'): item for item in coverage if isinstance(item, dict)}
        req_by_id = {item.get('id'): item for item in requirements if isinstance(item, dict)}
        all_req_ids = list(dict.fromkeys(list(req_by_id.keys()) + list(cov_by_id.keys())))

        status_labels = {
            'cubierto': 'Cubierto',
            'parcial': 'Parcial',
            'sin_fuentes': '⚠️ Sin fuentes documentales'
        }

        lines += [
            '| ID | Requisito / Petición | Tipo | Estado | Contenidos (claims) | Observaciones |',
            '| --- | --- | --- | --- | --- | --- |'
        ]
        has_missing_sources = False
        for rid in all_req_ids:
            req_info = req_by_id.get(rid, {})
            cov_info = cov_by_id.get(rid, {})
            desc = plain(req_info.get('description') or rid)
            rtype = plain(req_info.get('type') or 'contenido')
            c_status = cov_info.get('status', 'sin_fuentes' if not cov_info else 'cubierto')
            status_txt = status_labels.get(c_status, c_status.capitalize())
            c_claims = cov_info.get('claim_ids') or []
            claims_txt = ', '.join(f'#{cid}' for cid in c_claims) if c_claims else '—'
            note_txt = plain(cov_info.get('note') or '—')
            if c_status == 'sin_fuentes':
                has_missing_sources = True
            lines.append(f"| **{plain(rid)}** | {desc} | {rtype} | {status_txt} | {claims_txt} | {note_txt} |")
        lines.append('')
        if has_missing_sources:
            lines += [
                '> ⚠️ **Aviso de cobertura bibliográfica:** Hay requisitos marcados como *Sin fuentes documentales*. '
                'La biblioteca actual no dispone de pasajes autorizados suficientes para fundamentar estos aspectos sin especulación.',
                ''
            ]

    if plan:
        lines += ['## 1. Planificación didáctica y objetivos', '',
                  '### Objetivos de aprendizaje', '']
        lines += ['- ' + plain(x) for x in plan.get('objectives', [])]
        lines += ['', '**Dificultad propuesta:** ' + plain(plan.get('difficulty', '')), '']
        if plan.get('assessment'):
            lines += ['**Evaluación de la sesión:** ' + plain(replace_source_references(plan.get('assessment', ''), by_id)), '']
        lines += ['### Secuencia didáctica y actividades', '']
        elapsed = 0
        time_suffix_rx = re.compile(
            r'\s*[\(\[]\s*(?:\d+\s*(?:[-–—]|a)\s*)?\d+\s*(?:min(?:utos?)?|m|min\.)\s*[\)\]]\s*$',
            re.IGNORECASE
        )
        grouping_labels = {
            'individual': 'Individual',
            'grupo': 'En grupo',
            'colectivo': 'Colectivo',
        }
        for activity in plan.get('activities', []):
            end = elapsed + activity.get('minutes', 0)
            links = ', '.join(str(i) for i in activity.get('claim_ids', []))
            raw_title = str(activity.get('title', '')).strip()
            clean_title = time_suffix_rx.sub('', raw_title).strip()
            grouping_key = activity.get('grouping')
            mode_tag = f" [{grouping_labels.get(grouping_key, grouping_key.capitalize())}]" if grouping_key else ""
            lines += [f"**{elapsed}–{end} min · {plain(clean_title)}{mode_tag}**", '']
            if activity.get('teacher_notes'):
                lines += [f"**Pautas docentes:** {plain(replace_source_references(activity['teacher_notes'].strip(), by_id))}", '']
            elif activity.get('instructions'):
                lines += [plain(replace_source_references(activity['instructions'].strip(), by_id)), '']
            if activity.get('student_task'):
                lines += [f"**Consigna del alumno:** {plain(activity['student_task'].strip())}", '']
            if activity.get('deliverable'):
                lines += [f"**Entregable:** {plain(activity['deliverable'].strip())}", '']
            if activity.get('solution'):
                lines += [f"**Solución / Criterios de corrección:** {plain(replace_source_references(activity['solution'].strip(), by_id))}", '']
            lines += [f'Base documental: contenidos {links}.', '']
            elapsed = end
        lines += ['### Recursos y partituras por preparar', ''] + ['- ' + format_teacher_resource(x) for x in plan.get('resources', [])]

        music_reqs = result.get('music_requests') or []
        resolved_reqs = {r.get('request_id'): r for r in (result.get('resolved_music_requests') or [])}
        if music_reqs:
            lines += ['', '### Partituras y ejemplos musicales requeridos', '']
            for m_req in music_reqs:
                m_id = m_req.get('id', '')
                res_info = resolved_reqs.get(m_id, {})
                status = res_info.get('status', 'sin_resolver')
                work = m_req.get('work') or 'Obra requerida'
                comp = m_req.get('composer') or 'Compositor'
                tech = m_req.get('technique') or 'General'
                act_t = m_req.get('activity_title') or 'Actividad de aula'
                ej = res_info.get('ejemplo')
                if status == 'resuelto_catalogo' and ej and res_info.get('verificado'):
                    is_th = ej.get('calculado_teoria') or ej.get('fuente') == 'Calculado a partir de la teoría'
                    tag = '[Calculado a partir de la teoría]' if is_th else '[Verificado]'
                    lines += [
                        f"- **{plain(work)}** ({plain(comp)}) · *{plain(tech)}* {tag}",
                        f"  - Archivo: `{plain(ej.get('archivo', ''))}` · Compases: {plain(ej.get('compases', '1-8'))} · Licencia: {plain(ej.get('licencia', 'Libre'))}",
                    ]
                else:
                    lines += [
                        f"- ⚠️ **{plain(work)}** ({plain(comp)}) · *{plain(tech)}* [Pendiente de revisión]",
                        f"  - Petición para *{plain(act_t)}*: ejemplo pendiente de añadir o verificar en el catálogo.",
                    ]
            lines.append('')

        didactic_comps = result.get('resolved_didactic_components') or []
        if didactic_comps:
            lines += ['', '### Componentes didácticos deterministas incorporados', '']
            for dc in didactic_comps:
                tit = dc.get('titulo') or dc.get('tipo')
                lines += [f"- ✓ **{plain(tit)}** [Calculado a partir de la teoría]"]
            lines.append('')

        discarded_comps = list(result.get('discarded_didactic_components') or [])
        fulfillment_items = result.get('fulfillment') or []
        for fi in fulfillment_items:
            if fi.get('estado') == 'descartado':
                desc_disc = fi.get('falta') or 'No aplicable'
                rid = fi.get('requirement_id')
                if not any(dc.get('motivo_descarte') == desc_disc for dc in discarded_comps):
                    discarded_comps.append({
                        'tipo': rid,
                        'titulo': f"Requisito {rid} ({fi.get('ejecutor')})",
                        'motivo_descarte': desc_disc,
                    })
        if discarded_comps:
            lines += ['', '### Componentes didácticos descartados', '']
            for dc in discarded_comps:
                tit = dc.get('titulo') or dc.get('tipo')
                motivo = dc.get('motivo_descarte') or 'Parámetros no válidos o fuera de ámbito'
                lines += [f"- ⚠️ **{plain(tit)}** [Descartado]: {plain(motivo)}"]
            lines.append('')


        lines += ['', '**Observaciones didácticas:** ' + plain(replace_source_references(plan.get('observations', ''), by_id)), '']

    lines += ['## 2. Fundamentación teórica y contenidos', '']
    for index, claim in enumerate(claims, 1):
        label = claim_synthesis_label(claim, by_id)
        text = str(claim.get('text', '')).strip()
        lines += [f"**Contenido {index} — {label}:**", '', text, '']
        lines += format_claim_sources(claim, by_id) + ['']

    guide = (run.get('result') or {}).get('teacher_guide') or {}
    if guide.get('theory'):
        lines += ['## Guía teórica desarrollada para el profesor', '']
        for section in guide['theory']:
            links = ', '.join(str(i) for i in section.get('claim_ids', []))
            lines += [f"### {plain(section.get('title', ''))}", '',
                      plain(section.get('text', '')), '',
                      f"Base documental: contenidos {links}.", '']
    example = guide.get('worked_example') or lilypond_teacher_example(run)
    if example:
        language = re.sub(r'[^\w.+#-]', '', str(example.get('language', 'text')))[:40] or 'text'
        links = ', '.join(str(i) for i in example.get('claim_ids', []))
        lines += ['## Ejemplo resuelto completo', '', f"### {plain(example.get('title', ''))}", '',
                  f'```{language}', str(example.get('code', '')).strip(), '```', '',
                  '### Explicación del ejemplo', '']
        lines += ['- ' + plain(item) for item in example.get('explanation', [])]
        lines += ['', f'Base documental: contenidos {links}.', '']

    from docente_ai.teaching.fichas import get_ficha_for_run, is_ficha_verified
    ficha = get_ficha_for_run(run)
    if ficha:
        is_verified = is_ficha_verified(ficha)
        if not is_verified:
            lines += [
                '',
                f"## Contenido de plantilla pendiente de revisión ({plain(ficha.get('tema', ''))})",
                '',
                '> ⚠️ **Aviso para el profesor:** El siguiente contenido procede de la plantilla temática '
                'y está marcado como `verificado: false`. Permanece visible únicamente en esta guía docente '
                'para su revisión y nunca se publica en el material del alumnado hasta ser validado.',
                '',
            ]
            if ficha.get('revisado_con'):
                lines += [f"> **Revisado con:** {plain(ficha['revisado_con'])}", '']
            if ficha.get('cotejar'):
                lines += ['> ⚠️ **Pendiente de revisión del profesor / Puntos a cotejar:**']
                for c in ficha['cotejar']:
                    lines += [f"> - {plain(c)}"]
                lines.append('')
        else:
            lines += ['', f"## Contenido de plantilla validado ({plain(ficha.get('tema', ''))})", '']

        infog = ficha.get('infografia') or {}
        if infog:
            lines += [f"### 1. Esquema gráfico: {plain(infog.get('titulo', ''))}", '']
            if infog.get('subtitulo'):
                lines += [f"*{plain(infog['subtitulo'])}*", '']
            for m in infog.get('modelos_misa', []):
                rev_mark = f"\n  - **{plain(m['nota_revision'])}**" if m.get('nota_revision') else ""
                lines += [
                    f"- **{plain(m.get('nombre', ''))}:** {plain(m.get('disposicion', ''))}",
                    f"  - Características: {' '.join(plain(c) for c in m.get('caracteristicas', []))}",
                    f"  - Ejemplo: *{plain(m.get('ejemplo', ''))}* ({plain(m.get('ejemplo_descripcion', ''))}){rev_mark}",
                ]
            tecn = infog.get('tecnicas') or {}
            for paso_key in ('paso_1', 'paso_2', 'paso_3'):
                paso = tecn.get(paso_key)
                if not paso:
                    continue
                lines += ['', f"#### {plain(paso.get('titulo', ''))}", plain(paso.get('descripcion', ''))]
                for proc in paso.get('procedimientos', []):
                    lines += [f"- **{plain(proc.get('nombre', ''))}:** {' '.join(plain(d) for d in proc.get('detalles', []))} → *{plain(proc.get('resultado', ''))}*"]
                for rec in paso.get('recursos', []):
                    rev_mark = f" — **{plain(rec['nota_revision'])}**" if rec.get('nota_revision') else ""
                    lines += [f"- **{plain(rec.get('nombre', ''))}** ({plain(rec.get('subtitulo', ''))}): {' '.join(plain(d) for d in rec.get('detalles', []))}{rev_mark}"]

            for f_soc in infog.get('funciones_sociales', []):
                lines += [f"- **{plain(f_soc.get('funcion', ''))}:** {plain(f_soc.get('contexto', ''))} ({plain(f_soc.get('repertorio', ''))})"]
            for org in infog.get('organologia', []):
                lines += [f"- **{plain(org.get('familia', ''))}:** {plain(org.get('instrumentos', ''))} — {plain(org.get('contexto', ''))}"]
            for fi in infog.get('fuentes_e_iconografia', []):
                lines += [f"- {plain(fi)}"]

        conceptos = ficha.get('conceptos') or []
        if conceptos:
            lines += ['', '### 2. Conceptos de plantilla', '']
            for c in conceptos:
                rev_mark = f" — **{plain(c['nota_revision'])}**" if c.get('nota_revision') else ""
                lines += [f"- **{plain(c.get('termino', ''))}** [{plain(c.get('categoria', ''))}]: {plain(c.get('definicion', ''))}{rev_mark}"]

        tareas = ficha.get('tareas_adicionales_casa') or []
        if tareas:
            lines += ['', '### 3. Tareas adicionales de plantilla', '']
            for t in tareas:
                rev_mark = f"\n  - **{plain(t['nota_revision'])}**" if t.get('nota_revision') else ""
                lines += [
                    f"- **{plain(t.get('titulo', ''))}** [{plain(t.get('tag', ''))}]: {plain(t.get('objetivo', ''))}",
                    f"  - Pautas: {' '.join(plain(i) for i in t.get('instrucciones', []))}{rev_mark}",
                ]

        bib = ficha.get('bibliografia') or []
        if bib:
            lines += ['', '### 4. Bibliografía de plantilla', '']
            for b in bib:
                detail = f"{b.get('editorial', '')}"
                if b.get('anio'):
                    detail += f" ({b['anio']})"
                lines += [f"- **{plain(b.get('autor', ''))}**: *{plain(b.get('titulo', ''))}* — {plain(detail)}"]

        lines.append('')

    # Discografía y repertorio de audiciones
    listenings_to_render = []
    if _is_15th_century_topic(run):
        listenings_to_render = POLYPHONY_15TH_CENTURY_LISTENINGS
    elif _is_ancient_egypt_topic(run):
        listenings_to_render = ANCIENT_EGYPT_LISTENINGS
    if listenings_to_render:
        lines += ['', '## 4. Discografía de aula y repertorio de audiciones con enlaces', '',
                  '| Obra y partes | Grabación e Intérpretes | Enlace de audición | Criterio docente |',
                  '| --- | --- | --- | --- |']
        for item in listenings_to_render:
            links_str = '<br>'.join(f"[{plain(l['label'])}]({l['url']})" for l in item.get('links', []))
            lines.append(
                f"| **{plain(item['composer'])}**<br>*{plain(item['title'])}* | {plain(item.get('performer', ''))} | {links_str} | {plain(item.get('teacher_note', ''))} |"
            )
        lines.append('')

    for visual in (run.get('result') or {}).get('visualizations', []):
        lines += ['## Esquema documentado', '', f"### {plain(visual.get('title', ''))}", '']
        if visual.get('type') == 'table':
            lines += ['| Elemento | Relación o función |', '| --- | --- |']
            lines += [f"| {plain(item.get('label', ''))} | {plain(item.get('detail', ''))} |" for item in visual.get('items', [])]
        else:
            connector = ' → ' if visual.get('type') == 'sequence' else ' ⇄ '
            lines.append(connector.join(f"**{plain(item.get('label', ''))}** ({plain(item.get('detail', ''))})" for item in visual.get('items', [])))
        lines += ['', plain(visual.get('caption', '')), '']

    # --- SECCIÓN PLEGABLE DE REVISIÓN AUTOMÁTICA ---
    auto_review = (run.get('metrics') or {}).get('auto_review')
    if auto_review and isinstance(auto_review, dict):
        scores = auto_review.get('scores') or {}
        issues = auto_review.get('issues') or []
        summary = auto_review.get('summary') or ''
        repaired = auto_review.get('repaired', False)

        from docente_ai.agents.reviewer import CRITERIA_KEYS, CRITERIA_LABELS

        lines += [
            '',
            '<details>',
            '<summary><strong>🔍 Revisión automática (evaluación según rúbrica)</strong></summary>',
            '',
            '> ℹ️ **Nota de verificación:** Esta revisión es un análisis preliminar automático basado en la rúbrica pedagógica de Arkhé. **No sustituye a la revisión ni al criterio del profesor.**',
            '',
        ]
        if repaired:
            lines += ['> ⚠️ **Aviso de reparación:** Se ejecutó una ronda de corrección automática para subsanar criterios con puntuación inferior a 2.', '']

        lines += [
            '| Criterio evaluado | Puntuación (0–3) | Valoración |',
            '| --- |:---:| --- |'
        ]
        score_descs = {0: 'Insuficiente', 1: 'Parcial / Básico', 2: 'Bueno / Competente', 3: 'Excelente / Sobresaliente'}
        for ckey in CRITERIA_KEYS:
            clabel = CRITERIA_LABELS.get(ckey, ckey)
            sc = scores.get(ckey, '—')
            sdesc = score_descs.get(sc, 'Sin calificar') if isinstance(sc, int) else '—'
            lines.append(f"| {plain(clabel)} | **{sc}** | {sdesc} |")
        lines.append('')

        if summary:
            lines += [f"**Dictamen del revisor:** {plain(summary)}", '']

        if issues:
            lines += ['**Incidencias y propuestas de mejora detectadas:**', '']
            for iss in issues:
                f_name = plain(iss.get('field', 'General'))
                i_desc = plain(iss.get('issue', ''))
                p_desc = plain(iss.get('proposal', ''))
                lines.append(f"- **`{f_name}`:** {i_desc} *(Propuesta: {p_desc})*")
            lines.append('')
        else:
            lines += ['*No se detectaron problemas críticos en la propuesta.*', '']

        lines += ['</details>', '']

    if plan:
        lines += ['', '---', '', '# PARTE 2 · DOSSIER Y ACTIVIDADES (Material para el Alumnado)', '',
                  f"**Materia:** {plain(group.get('name', ''))} · **Tema:** {topic_header}", '',
                  '## 1. Conceptos clave y guía de estudio', '']
        for index, claim in enumerate(claims, 1):
            text = str(claim.get('student_summary') or claim.get('text', '')).strip()
            clean_text = re.sub(r'^###\s*', '', text)
            lines += [f"- **Punto {index}:** {clean_text}", '']

        if (run.get('result') or {}).get('visualizations'):
            lines += ['### Esquemas de estudio', '']
            for visual in run['result']['visualizations']:
                lines += [f"#### {plain(visual.get('title', ''))}", '']
                if visual.get('type') == 'table':
                    lines += ['| Concepto | Característica / Función |', '| --- | --- |']
                    lines += [f"| {plain(item.get('label', ''))} | {plain(item.get('detail', ''))} |" for item in visual.get('items', [])]
                else:
                    connector = ' → ' if visual.get('type') == 'sequence' else ' ⇄ '
                    lines.append(connector.join(f"**{plain(item.get('label', ''))}** ({plain(item.get('detail', ''))})" for item in visual.get('items', [])))
                lines += ['', plain(visual.get('caption', '')), '']

        lines += ['## 2. Repertorio, fuentes y audiciones de trabajo', '']
        rendered_student_res = []
        for item in plan.get('resources', []):
            formatted = format_student_resource(item, by_id)
            if formatted:
                rendered_student_res.append(formatted)
        lines += ['- ' + plain(r) for r in rendered_student_res]
        lines += ['', '## 3. Cuaderno de actividades y ejercicios prácticos', '']
        time_suffix_rx = re.compile(
            r'\s*[\(\[]\s*(?:\d+\s*(?:[-–—]|a)\s*)?\d+\s*(?:min(?:utos?)?|m|min\.)\s*[\)\]]\s*$',
            re.IGNORECASE
        )
        for idx, act in enumerate(plan.get('activities', []), 1):
            raw_title = str(act.get('title', '')).strip()
            clean_title = time_suffix_rx.sub('', raw_title).strip()
            title = plain(clean_title)
            grouping_key = act.get('grouping')
            grouping_labels = {'individual': 'Individual', 'grupo': 'En grupo', 'colectivo': 'Colectivo'}
            mode_tag = f" [{grouping_labels.get(grouping_key, grouping_key.capitalize())}]" if grouping_key else ""
            task_text = act.get('student_task') or act.get('instructions', '')
            lines += [f"### Actividad {idx}: {title}{mode_tag} ({act.get('minutes', 0)} min)", '']
            if task_text:
                lines += [f"**Tarea:** {plain(str(task_text).strip())}", '']
            if act.get('deliverable'):
                lines += [f"**Entregable:** {plain(str(act['deliverable']).strip())}", '']
            lines += [
                '*Espacio para notas, análisis o resolución del ejercicio:*', '',
                '```', '', '', '```', ''
            ]

    if run.get('omitted'):
        lines += ['', f"Fragmentos no enviados al modelo por presupuesto o duplicación: {len(run['omitted'])}."]
    for warning in run.get('warnings', []):
        lines += ['', '**Aviso:** ' + plain(warning)]
    if review:
        lines += ['', '---', '## Revisión del profesor', '']
        action_label = 'Aprobada' if review.get('action') == 'approved' else 'Rechazada'
        lines.append(f"**{action_label}** · {plain(review.get('reviewed_at', ''))}")
        if review.get('notes'):
            lines += ['', plain(review['notes'])]
    return clean_terminologia_output('\n'.join(lines).rstrip() + '\n')


def lilypond_teacher_example(run: dict):
    """Backfill a source-backed worked example for older LilyPond proposals."""
    result = run.get('result') or {}
    searchable = ' '.join([
        str((run.get('request') or {}).get('question', '')),
        *(str(item.get('text', '')) for item in result.get('claims') or []),
    ])
    labels = {
        str(item.get('label', ''))
        for visual in result.get('visualizations') or []
        for item in visual.get('items') or []
    }
    if not re.search(r'lilypond', searchable, re.I) or '\\score' not in labels:
        return None
    claim_count = len(result.get('claims') or [])
    return {
        'title': 'Archivo LilyPond completo y compilable',
        'language': 'lilypond',
        'claim_ids': [item for item in (3, 4, 5) if item <= claim_count],
        'code': '''\\version "2.23.82"

\\header {
  title = "Mi primera partitura"
  composer = "Nombre del alumno/a"
}

% VARIABLE MUSICAL: se declara sin barra invertida.
% Guarda este fragmento para poder reutilizarlo después.
melody = \\relative {
  c'4 a b c
}

\\score {
  % LLAMADA A LA VARIABLE: \\melody inserta aquí su contenido.
  \\melody
  \\layout { }
  \\midi { }
}''',
        'explanation': [
            '\\version declara la versión del lenguaje usada por el archivo.',
            '\\header reúne los metadatos visibles, como título y compositor.',
            'melody = ... declara una variable musical: el nombre se escribe sin barra invertida y conserva todo el bloque de notas.',
            '\\melody llama a esa variable dentro de \\score: la barra invertida indica a LilyPond que debe insertar su contenido.',
            '\\relative calcula cada altura con relación a la anterior y reduce la escritura de octavas.',
            '\\score reúne la expresión musical que se va a procesar.',
            '\\layout produce la partitura gráfica y \\midi genera la reproducción MIDI.',
        ],
    }
