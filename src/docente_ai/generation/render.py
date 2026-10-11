"""Markdown de borradores y propuestas pedagógicas con evidencia estructurada."""

import html
import re
from typing import Any

from docente_ai.rag.service import NO_EVIDENCE, citation


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
    'bibliografia', 'fuente_primaria', 'archivo local', 'material académico de la carrera'
}


def is_bibliographic_origin(src: dict) -> bool:
    if not src:
        return False
    if src.get('category') == 'documental':
        return True
    orig = (src.get('metadata') or {}).get('origin')
    return orig in BIBLIOGRAPHIC_ORIGINS


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
        if orig == 'sin_clasificar':
            has_unclassified = True
        elif orig in ('notas_profesor', 'material docente propio') or category == 'profesor':
            has_prof = True
        elif orig in BIBLIOGRAPHIC_ORIGINS or category == 'documental':
            has_bib = True
    if has_bib:
        return 'Síntesis respaldada por bibliografía'
    if has_prof:
        return 'Síntesis basada en notas del profesor'
    if has_unclassified:
        return 'Origen documental pendiente de clasificar'
    return 'Contenido sin respaldo bibliográfico'


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
        authors = '; '.join(meta.get('authors') or []) if meta.get('authors') else 'Sin autor identificado'
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
        primary = authors[0].split(',')[0].strip()
        author = primary.title() if (primary.isupper() or primary.islower()) else primary
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
    lines += ['- ' + plain(item) for item in plan.get('objectives', [])]

    # --- SECCIÓN 01: CONTENIDO TEÓRICO DE LAS FUENTES ---
    claims = result.get('claims') or []
    lines += ['', '## 01 · Contenido teórico de las fuentes', '']
    if is_polyphony:
        lines += [
            '*Análisis musicológico e histórico basado en las fuentes de Allan Atlas, Gustave Reese y Ulrich Michels.*', ''
        ]
    elif is_egypt:
        lines += [
            '*Análisis histórico, organológico e iconográfico basado en Marcelle Duchesne-Guillemin, J. Peter Burkholder y Enrico Fubini.*', ''
        ]
    for index, claim in enumerate(claims, 1):
        summary_text = str(claim.get('student_summary') or claim.get('text', '')).strip()
        lines += [f"### {index}. Punto clave", '', plain(summary_text), '']

    # --- SECCIÓN 02: ESQUEMAS ---
    sec02_title = '## 02 · Esquema gráfico: Modelos y técnicas de composición' if is_polyphony else '## 02 · Esquemas de estudio'
    lines += ['', sec02_title, '']
    if is_polyphony:
        lines += [
            '### 1. Distribución vocálica y modelos de misa del siglo XV',
            '*Una melodía, tres caminos de creación.*', '',
            '| Modelo de Misa | Disposición de Voces | Características Esenciales | Obra de Ejemplo |',
            '| --- | --- | --- | --- |',
            '| **1. Misa de Cantus Firmus** (Estructura rígida) | **Superius** (Soprano)<br>**Altus** (Contralto)<br>**TENOR (Melodía en valores largos / aumentación)**<br>**Bassus** (Bajo) | • Melodía preexistente fija en valores largos.<br>• Generalmente asignada al Tenor.<br>• Otras voces tejen contrapunto libre o imitativo.<br>• Estructura solemne y eje formal de la misa. | *L\'homme armé* (Cantus firmus en el Tenor en valores de longa y máxima). |',
            '| **2. Misa de Paráfrasis** (Estructura fluida) | **Superius** (Fragmento A)<br>↳ **Altus** (Imitación)<br>↳ **Tenor** (Imitación)<br>↳ **Bassus** (Imitación) | • Melodía original reconocible pero con glosas/adornos.<br>• Se reparte entre todas las voces por imitación.<br>• Mayor libertad rítmica, melódica y expresiva.<br>• Textura dinámica y homogénea. | *Pange Lingua* (Himno gregoriano ornamentado e imitado en todas las voces). |',
            '| **3. Misa Parodia / Imitación** (Estructura en bloque) | **Obra Original (Chanson/Motete a 4 voces)**<br>⇊ *Se copia, se adapta y se transforma* ⇊<br>**Misa Nueva (Superius, Altus, Tenor, Bassus)** | • Se toma la obra original completa (las cuatro voces).<br>• Puede alterarse el orden, ritmo o métrica.<br>• Alternancia de imitación polifónica y homofonía.<br>• Inserción de nuevos motivos y adaptación al texto litúrgico. | *Je ne vis oncques la* / *Missa Se la face ay pale*. |',
            '',
            '### 2. Técnicas de composición: Del material preexistente a la misa cíclica',
            '*Tradición · Invención · Unidad*', '',
            '#### PASO 1: Selección del material preexistente',
            '- **Origen Sacro (Canto Llano / Gregoriano):** Himnos, antífonas, cantos litúrgicos (*Ave Maris Stella*, *Pange Lingua*, *Veni Creator Spiritus*).',
            '- **Origen Profano (Chansons y canciones populares):** Chansons cortesanas borgoñonas, canciones de tradición oral y difusión popular (*L\'homme armé*, *Se la face ay pale*, *Belle, bonne, sage*).',
            '',
            '#### PASO 2: Elección de la técnica de tratamiento',
            '1. **CANTUS FIRMUS:** Aislar la melodía; estirar las notas en aumentación; situarla en el Tenor; otras voces en contrapunto libre. → **Resultado:** *Melodía fija como columna vertebral de la obra.*',
            '2. **PARÁFRASIS:** Alterar intervalos; añadir ornamentos (glosas); repartir la melodía entre todas las voces en imitación; mayor libertad rítmica. → **Resultado:** *Melodía transformada y en constante movimiento.*',
            '3. **PARODIA / IMITACIÓN:** Tomar el tejido polifónico completo; variar orden, ritmo o textura; alternar contrapunto y bloques homofónicos. → **Resultado:** *Una nueva obra a partir de todo el material original.*',
            '',
            '#### PASO 3: Unificación de la misa cíclica',
            '- **Técnica del Motto (Motivo de cabeza):** Todas las secciones del Ordinario (Kyrie, Gloria, Credo, Sanctus, Agnus Dei) comienzan con las mismas 3 o 4 notas o células motívicas en las voces superiores, reforzando la coherencia global (Dufay, Josquin).',
            '- **Cadencias Renacentistas:** Uso de la cadencia de Landini y cadencias borgoñonas caracterizadas por la octava sin tercera en los puntos de articulación formal.',
            ''
        ]
    elif is_egypt:
        lines += [
            '### 1. Marco histórico y funciones sociales de la música egipcia',
            '*Una civilización, un río, una música milenaria (Imperio Antiguo c. 2700 a. C. a época grecorromana).*', '',
            '| Función Social | Ámbito y Contexto | Práctica y Repertorio | Divinidad / Símbolo |',
            '| --- | --- | --- | --- |',
            '| **1. Religiosa y Ritual** | Culto en templos, himnos, procesiones | Sacerdotisas y músicos del templo, ofrendas | Hathor (música y danza) e Isis (protección) |',
            '| **2. Funeraria** | Acompañamiento en el viaje al Más Allá | Cantos de enterramiento, honra y renacimiento del difunto | Ojo de Horus / Osiris |',
            '| **3. Cortesana y Festiva** | Banquetes, recepciones y palacios de la élite | Piezas instrumentales, danza, entretenimiento de prestigio | Flor de Loto / Realeza |',
            '| **4. Popular y Laboral** | Faenas agrícolas, talleres, remeros en el Nilo | Canciones rítmicas de trabajo para coordinar el esfuerzo, coplas populares | Vida cotidiana y trabajo |',
            '',
            '### 2. Clasificación organológica de los instrumentos del Antiguo Egipto',
            '*Sonido, técnica y clasificación según la iconografía y hallazgos arqueológicos.*', '',
            '| Familia Organológica | Instrumentos Principales | Materiales y Construcción | Contexto de Uso |',
            '| --- | --- | --- | --- |',
            '| **Cordófonos** (Cuerdas pulsadas) | **Arpa arqueada**, **Laúd** (mástil largo), **Lira** (en U) | Cajas de madera, tripas o fibras vegetales | Ámbitos cortesanos, recepciones íntimas y acompañamiento poético |',
            '| **Aerófonos** (Viento y aire) | **Flautas rectas**, **Clarinetes dobles** (lengüeta), **Trompetas** (bronce) | Caña, madera labrada y metal | Procesiones, ceremonias solemnes y ámbito militar |',
            '| **Percusión e Idiófonos** (Agitados / percutidos) | **Sistros** (anillas de metal), **Collar Menat**, **Tambores**, **Crótalos** | Bronce, fayenza, parches de cuero y madera | Rituales sagrados de Hathor, marcación de danza y pulso |',
            '',
            '### 3. Agrupaciones, fuentes e iconografía (Tumba de Nebamun, c. 1350 a. C.)',
            '- **Práctica de conjunto:** Solistas íntimos (arpa y canto), pequeños conjuntos de cámara (arpa, flauta, percusión) y conjuntos para la danza.',
            '- **Quironimia:** Sistema de dirección mediante gestos manuales del cantor/director que indicaba alturas y contorno melódico.',
            '- **Fuentes de estudio:** Iconografía (murales y relieves), Textos (himnos e inscripciones), Arqueología (instrumentos en tumbas) y Comparación etnomusicológica.',
            ''
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

    # --- CHEAT SHEET DE PRÁCTICA (Conservado para consulta y síntesis rápida) ---
    lines += ['## Cheat sheet de práctica', '',
              'Consulta rápida para tener a mano durante el trabajo de hoy.', '']
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
            lines.append(f"- **Clave {index}:** {plain(str(claim.get('text', '')).strip())}")

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
    # Solo aparece si hay audiciones vinculadas en el run o encontradas en el catálogo verificado.
    # Nunca inventa "Obra representativa N" a partir de las actividades.
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

    # --- TRABAJO EN CLASE ---
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
        task_text = activity.get('student_task') or activity.get('instructions', '')
        if task_text:
            lines += [f"- **Tarea:** {plain(task_text.strip())}"]
        if activity.get('deliverable'):
            lines += [f"- **Entregable:** {plain(str(activity['deliverable']).strip())}"]
        lines.append('')
        elapsed += minutes

    lines += ['## Material necesario', '']
    lines += ['- ' + plain(item) for item in plan.get('resources', [])]

    sources = []
    for item in run.get('evidence') or []:
        meta = item.get('metadata') or {}
        stitle = str(meta.get('title') or '')
        # Filtrar fuentes sintéticas de evaluación
        if 'Fuente de evaluación:' in stitle or 'prueba' in stitle.lower():
            continue
        key = (stitle, tuple(meta.get('authors') or []), meta.get('year'))
        if key not in sources and stitle:
            sources.append(key)
    if is_polyphony:
        key_atlas = ('La música del Renacimiento & Antología', ('Allan W. Atlas',), 2002)
        key_reese = ('La música en el Renacimiento', ('Gustave Reese',), 1988)
        key_michels = ('Atlas de la Música', ('Ulrich Michels',), 1982)
        for k in (key_atlas, key_reese, key_michels):
            if k not in sources:
                sources.append(k)
    elif is_egypt:
        key_duchesne = ('Music in Ancient Mesopotamia and Egypt', ('Marcelle Duchesne-Guillemin',), 1981)
        key_burkholder = ('Norton Anthology of Western Music (Ancient to Baroque)', ('J. Peter Burkholder', 'Claude V. Palisca'), 2014)
        key_fubini = ('Historia de la estética musical: desde la Antigüedad hasta el siglo XX', ('Enrico Fubini',), 1988)
        for k in (key_duchesne, key_burkholder, key_fubini):
            if k not in sources:
                sources.append(k)

    if sources:
        lines += ['', '## Fuentes de consulta', '']
        for title, authors, year in sources:
            detail = ', '.join(authors) if authors else ''
            if year:
                detail += (' · ' if detail else '') + str(year)
            lines.append(f"- {plain(title or 'Fuente sin título')}{' — ' + plain(detail) if detail else ''}")

    if is_polyphony:
        lines += [
            '',
            '## 06 · Discografía recomendada y enlaces directos de audición para el aula',
            '',
            '| Obra y partes | Grabación e Intérpretes | Enlace de audición | Criterio docente |',
            '| --- | --- | --- | --- |',
            "| **Guillaume Du Fay**<br>*Missa Se la face ay pale* (Kyrie y Gloria) | Early Music Consort of London<br>dir. David Munrow | [▶ Kyrie en YouTube](https://www.youtube.com/watch?v=izy4bDPp23k)<br>[▶ Gloria en YouTube](https://www.youtube.com/watch?v=McyAlOZ4JjQ) | Misma grabación de referencia; interpretación homogénea. |",
            "| **Gilles Binchois**<br>*De plus en plus se renouvelle* | Ensemble Gilles Binchois<br>dir. Dominique Vellard | [▶ De plus en plus en YouTube](https://www.youtube.com/watch?v=cw_V53noTUg) | Carácter lírico y claridad meridiana de las 3 voces. |",
            "| **Johannes Ockeghem**<br>*Missa L'homme armé* (Kyrie y Agnus Dei) | Oxford Camerata<br>dir. Jeremy Summerly | [▶ Kyrie en YouTube](https://www.youtube.com/watch?v=KgV3cxc1NEI)<br>[▶ Agnus Dei en YouTube](https://www.youtube.com/watch?v=xDFKOKWzpI0) | Misma interpretación para ambos movimientos; claridad en el grave. |",
            "| **Johannes Ockeghem**<br>*Mort, tu as navré* (Déploration) | Graindelavoix<br>dir. Björn Schmelzer | [▶ Mort, tu as navré en YouTube](https://www.youtube.com/watch?v=R9tcg1VfKPs) | Gran expresividad, contraste luctuoso y clima sombrío. |",
            ''
        ]

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
                f"> «{plain(trans_text)}»{trans_tag}",
                ''
            ]

    return clean_terminologia_output('\n'.join(lines).rstrip() + '\n')


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
        lines += ['### Recursos y partituras por preparar', ''] + ['- ' + plain(x) for x in plan.get('resources', [])]

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
                    lines += [
                        f"- **{plain(work)}** ({plain(comp)}) · *{plain(tech)}* [Verificado]",
                        f"  - Archivo: `{plain(ej.get('archivo', ''))}` · Compases: {plain(ej.get('compases', '1-8'))} · Licencia: {plain(ej.get('licencia', 'Libre'))}",
                    ]
                else:
                    lines += [
                        f"- ⚠️ **{plain(work)}** ({plain(comp)}) · *{plain(tech)}* [Pendiente de revisión]",
                        f"  - Petición para *{plain(act_t)}*: ejemplo pendiente de añadir o verificar en el catálogo.",
                    ]
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

    is_polyphony = _is_15th_century_topic(run)
    is_egypt = _is_ancient_egypt_topic(run)

    if is_polyphony:
        lines += [
            '## 3. Esquema gráfico y modelos compositivos (Polifonía del siglo XV)', '',
            '### Panel 1: Distribución vocálica y modelos de misa',
            '- **Misa de Cantus Firmus (Estructura rígida):**',
            '  - *Superius (Soprano):* Contrapunto libre y florido.',
            '  - *Altus (Contralto):* Relleno armónico intermedio.',
            '  - *Tenor (Cantus Firmus):* Melodía preexistente fija en valores largos (aumentación).',
            '  - *Bassus (Bajo):* Base armónica, descenso a graves.',
            '  - *Ejemplo canónico:* *L\'homme armé*.',
            '- **Misa de Paráfrasis (Estructura fluida e imitativa):**',
            '  - La melodía preexistente se glosa y adorna, repartiéndose en imitación por todas las voces.',
            '  - *Ejemplo canónico:* *Pange Lingua*.',
            '- **Misa Parodia / Imitación (Estructura en bloque):**',
            '  - Reelaboración de todas las voces del modelo polifónico preexistente.',
            '  - *Ejemplo canónico:* *Je ne vis oncques la* / *Se la face ay pale*.', '',
            '### Panel 2: Técnicas de composición: del material preexistente a la misa cíclica',
            '- **Paso 1 · Selección del material:** Origen Sacro (Canto gregoriano: *Ave Maris Stella*, *Pange Lingua*) u Origen Profano (Chansons: *L\'homme armé*, *Se la face ay pale*).',
            '- **Paso 2 · Técnicas de tratamiento:** *Cantus Firmus* (columna vertebral fija), *Paráfrasis* (elaboración imitativa) o *Parodia / Imitación* (adaptación del tejido completo).',
            '- **Paso 3 · Unificación cíclica:** Técnica del *motto* (motivo de cabeza idéntico en los 5 movimientos) y cadencias renacentistas (cadencia Landini con salto de 6ª a 8ª sin 3ª).', '',
            '## 4. Discografía de aula y repertorio de audiciones con enlaces', '',
            '| Obra y partes | Grabación e Intérpretes | Enlace de audición | Criterio docente |',
            '| --- | --- | --- | --- |',
            "| **Guillaume Du Fay**<br>*Missa Se la face ay pale* (Kyrie y Gloria) | Early Music Consort of London<br>dir. David Munrow | [▶ Kyrie en YouTube](https://www.youtube.com/watch?v=izy4bDPp23k)<br>[▶ Gloria en YouTube](https://www.youtube.com/watch?v=McyAlOZ4JjQ) | Misma grabación de referencia; interpretación homogénea. |",
            "| **Gilles Binchois**<br>*De plus en plus se renouvelle* | Ensemble Gilles Binchois<br>dir. Dominique Vellard | [▶ De plus en plus en YouTube](https://www.youtube.com/watch?v=cw_V53noTUg) | Carácter lírico y claridad meridiana de las 3 voces. |",
            "| **Johannes Ockeghem**<br>*Missa L'homme armé* (Kyrie y Agnus Dei) | Oxford Camerata<br>dir. Jeremy Summerly | [▶ Kyrie en YouTube](https://www.youtube.com/watch?v=KgV3cxc1NEI)<br>[▶ Agnus Dei en YouTube](https://www.youtube.com/watch?v=xDFKOKWzpI0) | Misma interpretación para ambos movimientos; claridad en el grave. |",
            "| **Johannes Ockeghem**<br>*Mort, tu as navré* (Déploration) | Graindelavoix<br>dir. Björn Schmelzer | [▶ Mort, tu as navré en YouTube](https://www.youtube.com/watch?v=R9tcg1VfKPs) | Gran expresividad, contraste luctuoso y clima sombrío. |",
            ''
        ]
    elif is_egypt:
        lines += [
            '## 3. Esquema gráfico: Marco histórico, funciones y organología del Antiguo Egipto', '',
            '### Lámina 1: Contexto, funciones y rasgos generales',
            '- **Marco geográfico-histórico:** Eje del Nilo; desde el Imperio Antiguo (c. 2686 a. C.) hasta la época grecorromana (c. 30 a. C.).',
            '- **4 Funciones de la música:**',
            '  1. *Religiosa y ritual:* Culto en templos (Hathor, Isis, Osiris) para apaciguar a los dioses.',
            '  2. *Funeraria:* Protección y tránsito al más allá en tumbas y pirámides.',
            '  3. *Cortesana y festiva:* Banquetes regios y celebraciones de la nobleza.',
            '  4. *Popular y laboral:* Canciones de siega y cantos de trabajo de remeros en el Nilo.',
            '- **Rasgos:** Unión indisoluble de música, danza y gesto; figura de la **quironimia** y protagonismo femenino.', '',
            '### Lámina 2: Organología, práctica musical y fuentes',
            '- **Cordófonos:** Arpas arqueadas (de pie y suelo), laúd de mástil largo, liras.',
            '- **Aerófonos:** Flautas rectas longitudinales, clarinetes dobles de caña con lengüeta batiente, trompetas ceremoniales.',
            '- **Percusión e idiófonos:** Sistro de Hathor, collar sonajero Menat, crótalos, tambores.',
            '- **Práctica de conjunto:** Fresco de la Tumba de Nebamun (Tebas, c. 1350 a. C.).',
            '- **4 Fuentes de estudio:** Iconografía, textos, arqueología musical y etnomusicología comparada.', '',
            '## 4. Discografía de aula y repertorio de audiciones con enlaces', '',
            '| Audición | Obra y Grabación | Enlaces de audición | Criterio docente y límites metodológicos |',
            '| --- | --- | --- | --- |',
            "| **Audición 1A**<br>Michael Levy | *Ancient Harps of Kemet* (2011)<br>Arpa arqueada de tipo arcaico | [▶ Levy: Arpa en YouTube](https://www.youtube.com/watch?v=mqxB34z4tyw) | Recreación tímbrica e improvisación moderna; timbre organológico vs. obra original. |",
            "| **Audición 1B**<br>Michael Levy | *Reconstructed Ancient Egyptian Melody*<br>Arreglo para lira (banquete tebano) | [▶ Levy: Melodía en YouTube](https://www.youtube.com/watch?v=nBmWXmn11YE) | Procedimiento de reconstrucción a partir de flauta conservada e hipótesis sonora. |",
            "| **Audición 2**<br>De Organographia | *Isis Sistrum Rhythm, after Apuleius*<br>Reconstrucción breve (0:31) | [▶ Sistro en YouTube](https://www.youtube.com/watch?v=599YEae4DYA) | Ritmo ritual de sistro a partir de Apuleyo; función sacra sin melodía inventada. |",
            "| **Audición 3**<br>Descarte metodológico | *Canto colectivo de labor*<br>Análisis crítico de fuentes iconográficas | *(Descartada como audición)* | Sin base documental suficiente para un audio fiable; se analiza iconografía. |",
            "| **Audición 4**<br>Grabación BBC 1939 | *King Tutankhamun's Trumpets*<br>Trompetas originales de la tumba KV62 | [▶ Trompetas BBC en YouTube](https://www.youtube.com/watch?v=Qt9AyV3hnlc)<br>[BBC Ghost Music](https://www.bbc.co.uk/programmes/b010dp0s) | Instrumentos auténticos de c. 1323 a. C.; técnica militar del siglo XX con boquilla moderna. |",
            ''
        ]

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
        lines += ['- ' + plain(x) for x in plan.get('resources', [])]
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
