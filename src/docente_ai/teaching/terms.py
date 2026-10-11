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
    'Ptolomeo': ['Ptolomeo', 'Tolomeo', 'Ptolemy'],
    'Arístides Quintiliano': ['Arístides Quintiliano', 'Aristides Quintiliano', 'Arístides', 'Aristides Quintilianus'],
    'Alipio': ['Alipio', 'Alypius'],
    'San Agustín': ['San Agustín', 'San Agustin', 'Agustín de Hipona', 'Agustin de Hipona', 'Augustine', 'St. Augustine'],
    'Boecio': ['Boecio', 'Boethius'],
}


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



def normalize_topic(text: str) -> str:
    """Corrige erratas evidentes en nombres o términos musicológicos conocidos,

    preservando la estructura del texto.
    """
    if not text or not isinstance(text, str):
        return text or ''

    result = text
    # Sustitución de frases completas y términos con límites de palabra
    for typo, correction in sorted(MUSICOLOGICAL_TERMS.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(r'\b' + re.escape(typo) + r'\b', re.IGNORECASE)
        result = pattern.sub(correction, result)

    return result
