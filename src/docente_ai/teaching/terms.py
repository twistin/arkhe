"""Normalización de términos musicológicos y corrección de erratas en temas."""

import re

# Diccionario de erratas y variantes comunes a su forma estándar canónica
MUSICOLOGICAL_TERMS: dict[str, str] = {
    # Compositores
    'ockehem': 'Johannes Ockeghem',
    'okeghem': 'Johannes Ockeghem',
    'ockeghen': 'Johannes Ockeghem',
    'ockeghem': 'Johannes Ockeghem',
    'johanes ockeghem': 'Johannes Ockeghem',
    'resse': 'Gustave Reese',
    'rese': 'Gustave Reese',
    'gustav reese': 'Gustave Reese',
    'dufay': 'Guillaume Du Fay',
    'du fay': 'Guillaume Du Fay',
    'guillaume dufay': 'Guillaume Du Fay',
    'binchois': 'Gilles Binchois',
    'gilles de binchois': 'Gilles Binchois',
    'busnois': 'Antoine Busnois',
    'josquin': 'Josquin des Prez',
    'josquin des pres': 'Josquin des Prez',
    'josquin desprez': 'Josquin des Prez',
    'palestrina': 'Giovanni Pierluigi da Palestrina',
    'monteverdi': 'Claudio Monteverdi',

    # Obras, fuentes y conceptos históricos
    'seikilos': 'Seikilos',
    'srikilos': 'Seikilos',
    'epitafio de seikilos': 'Epitafio de Seikilos',
    'eputafio de seikilos': 'Epitafio de Seikilos',
    'epitafio de srikilos': 'Epitafio de Seikilos',
    'epitafio de sikilos': 'Epitafio de Seikilos',
    'seikilos epitaph': 'Epitafio de Seikilos',
    'nebamun': 'Nebamun',
    'nebamún': 'Nebamún',
    'tutankamon': 'Tutankamón',
    'tutankhamun': 'Tutankamón',
    'duchesne': 'Marcelle Duchesne-Guillemin',
    'duchesne-guillemin': 'Marcelle Duchesne-Guillemin',
    'burkholder': 'J. Peter Burkholder',
    'fubini': 'Enrico Fubini',

    # Géneros y técnicas
    'cantus firmus': 'cantus firmus',
    'formes fixes': 'formes fixes',
    'misa ciclica': 'misa cíclica',
    'misa cicilica': 'misa cíclica',
    'misa de parafrasis': 'misa de paráfrasis',
    'parafrasis': 'paráfrasis',
    'faburden': 'faburden',
    'fauxbourdon': 'fauxbourdon',
    'organum': 'organum',
    'discantus': 'discantus',
    'clausula': 'cláusula',

    # Términos griegos y modos antiguos
    'jastio': 'iastio',
}

# Autores canónicos para comprobación de omisiones en líneas temporales y requisitos
CANONICAL_AUTHORS: dict[str, list[str]] = {
    'Pitágoras': ['Pitágoras', 'Pitagoras', 'pitagórico', 'pitagóricos', 'Pythagoras'],
    'Filolao': ['Filolao', 'Philolaus'],
    'Arquitas': ['Arquitas', 'Archytas'],
    'Damón': ['Damón', 'Damon'],
    'Platón': ['Platón', 'Platon', 'platónico', 'Plato'],
    'Aristóteles': ['Aristóteles', 'Aristoteles', 'aristotélico', 'Aristotle'],
    'Aristóxeno': ['Aristóxeno', 'Aristoxeno', 'Aristoxenus'],
    'Hefestión': ['Hefestión', 'Hefestion', 'Hephaestion'],
    'Ptolomeo': ['Ptolomeo', 'Tolomeo', 'Ptolemy'],
    'Arístides Quintiliano': ['Arístides Quintiliano', 'Aristides Quintiliano', 'Arístides', 'Aristides Quintilianus'],
    'Alipio': ['Alipio', 'Alypius'],
    'San Agustín': ['San Agustín', 'San Agustin', 'Agustín de Hipona', 'Agustin de Hipona', 'Augustine', 'St. Augustine'],
    'Boecio': ['Boecio', 'Boethius'],
}

# Mapa canónico para visualización de nombres de autor (tildes, mayúsculas correctas)
KNOWN_AUTHORS_MAP: dict[str, str] = {
    'aristoxeno': 'Aristóxeno',
    'aristoxenus': 'Aristóxeno',
    'hefestion': 'Hefestión',
    'hephaestion': 'Hefestión',
    'ptolomeo': 'Ptolomeo',
    'tolomeo': 'Ptolomeo',
    'ptolemy': 'Ptolomeo',
    'willi apel': 'Willi Apel',
    'ralph t. daniel': 'Ralph T. Daniel',
    'ralph t daniel': 'Ralph T. Daniel',
    'fuensanta garrido domene': 'Fuensanta Garrido Domené',
    'fuensanta garrido domené': 'Fuensanta Garrido Domené',
    'aristides quintiliano': 'Arístides Quintiliano',
    'aristides quintilianus': 'Arístides Quintiliano',
    'boecio': 'Boecio',
    'boethius': 'Boecio',
    'alipio': 'Alipio',
    'alypius': 'Alipio',
    'san agustin': 'San Agustín',
    'san agustín': 'San Agustín',
    'agustin': 'San Agustín',
    'gustave reese': 'Gustave Reese',
    'j. peter burkholder': 'J. Peter Burkholder',
    'claude v. palisca': 'Claude V. Palisca',
    'andrew barker': 'Andrew Barker',
    'pitagoras': 'Pitágoras',
    'filolao': 'Filolao',
    'arquitas': 'Arquitas',
    'platon': 'Platón',
    'aristoteles': 'Aristóteles',
}


def normalize_author_display(name: str) -> str:
    """Normaliza la visualización de un nombre de autor (mayúsculas iniciales, tildes conocidas, sin dobles espacios).

    No modifica los metadatos originales en base de datos.
    """
    if not name:
        return ''
    import unicodedata
    cleaned = ' '.join(name.split())
    lowered = cleaned.lower()
    lowered_sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', lowered) if unicodedata.category(c) != 'Mn')

    if lowered in KNOWN_AUTHORS_MAP:
        return KNOWN_AUTHORS_MAP[lowered]
    if lowered_sin_tildes in KNOWN_AUTHORS_MAP:
        return KNOWN_AUTHORS_MAP[lowered_sin_tildes]

    # Para nombres como 'WILLI APEL, RALPH T. DANIEL'
    if ',' in cleaned and any(p.strip().lower() in KNOWN_AUTHORS_MAP for p in cleaned.split(',')):
        sub_parts = [normalize_author_display(p.strip()) for p in cleaned.split(',')]
        return ', '.join(sub_parts)

    # Si está todo en mayúsculas o todo en minúsculas, aplicar capitalización respetando iniciales
    if cleaned.isupper() or cleaned.islower():
        words = cleaned.split(' ')
        capitalized = []
        for w in words:
            if len(w) == 2 and w[1] == '.':
                capitalized.append(w.upper())
            elif w.lower() in ('de', 'del', 'da', 'di', 'von', 'van', 'y'):
                capitalized.append(w.lower())
            else:
                capitalized.append(w.capitalize())
        return ' '.join(capitalized)

    return cleaned


def normalize_authors_display(authors: list[str] | None) -> list[str]:
    """Normaliza una lista de autores para visualización."""
    if not authors:
        return []
    res = []
    for a in authors:
        if not a:
            continue
        norm = normalize_author_display(str(a))
        if norm and norm not in res:
            res.append(norm)
    return res



def find_canonical_authors_in_text(text: str) -> set[str]:
    """Extrae los nombres normalizados de autores canónicos que aparecen en un texto."""
    if not text:
        return set()
    found = set()
    for canonical, variants in CANONICAL_AUTHORS.items():
        for variant in variants:
            if re.search(r'\b' + re.escape(variant) + r'\b', text, re.IGNORECASE):
                found.add(canonical)
                break
    return found



# Palabras comunes docentes y musicológicas que requieren tilde habitual
COMMON_ACCENTS: dict[str, str] = {
    'polifonia': 'polifonía',
    'teoria': 'teoría',
    'musica': 'música',
    'armonia': 'armonía',
    'notacion': 'notación',
    'audicion': 'audición',
    'composicion': 'composición',
    'edicion': 'edición',
    'representacion': 'representación',
    'grafica': 'gráfica',
    'generos': 'géneros',
    'ritmica': 'rítmica',
    'melodica': 'melódica',
    'practica': 'práctica',
}


def _match_case(matched_text: str, replacement: str) -> str:
    """Conserva mayúsculas completas o iniciales al sustituir."""
    if matched_text.isupper():
        return replacement.upper()
    if matched_text and matched_text[0].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement.lower()


def normalize_topic(text: str) -> str:
    """Corrige erratas evidentes en nombres o términos musicológicos conocidos,
    acentos habituales y espacios antes de signos de puntuación,
    preservando la estructura del texto y sin tocar nombres propios.
    """
    if not text or not isinstance(text, str):
        return text or ''

    result = text

    # 1. Corrección de espacios antes de signos de puntuación
    result = re.sub(r'\s+([,.:;!?\)\]])', r'\1', result)
    result = re.sub(r'([¿¡\(\[])\s+', r'\1', result)
    result = re.sub(r'([,;:])([A-Za-zÀ-ÿ0-9])', r'\1 \2', result)

    # 2. Sustitución de frases completas y términos musicológicos con límites de palabra
    for typo, correction in sorted(MUSICOLOGICAL_TERMS.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(r'\b' + re.escape(typo) + r'\b', re.IGNORECASE)
        result = pattern.sub(correction, result)

    # 3. Corrección de acentos habituales (Polifonía, Teoría, Música, etc.) respetando mayúsculas
    for word_no_accent, word_with_accent in COMMON_ACCENTS.items():
        pattern = re.compile(r'\b' + re.escape(word_no_accent) + r'\b', re.IGNORECASE)
        result = pattern.sub(lambda m: _match_case(m.group(0), word_with_accent), result)

    # 4. Normalizar espacios múltiples
    result = re.sub(r'[ \t]+', ' ', result).strip()

    return result

