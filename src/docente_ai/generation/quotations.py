import re

ABBREVIATIONS = (
    'a. C.', 'd. C.', 'a. c.', 'd. c.', 'a.n.e.', 'd.n.e.',
    's.', 'c.', 'ca.', 'p.', 'pp.', 'col.', 'caps.', 'cap.',
    'ed.', 'eds.', 'vol.', 'vols.', 'núm.', 'num.', 'fig.', 'figs.'
)


def passages(text):
    """Segmenta un texto en pasajes respetando límites oracionales y protegiendo abreviaturas."""
    if not text or not isinstance(text, str):
        return []

    protected = text
    placeholder_map = {}

    # 1. Proteger abreviaturas conocidas ordenadas de mayor a menor longitud
    sorted_abbrs = sorted(ABBREVIATIONS, key=lambda x: -len(x))
    for i, abbr in enumerate(sorted_abbrs):
        pattern = re.compile(r'\b' + re.escape(abbr), re.IGNORECASE)
        for match in pattern.finditer(protected):
            orig = match.group(0)
            token = f'__ABBR_{i}_{len(placeholder_map)}__'
            placeholder_map[token] = orig
            protected = protected.replace(orig, token)

    # 2. Iniciales de personas con punto, p. ej. 'J. Peter' o 'C. V. Palisca'
    initial_pattern = re.compile(r'\b([A-ZÀ-ÿ])\.\s*(?=[A-ZÀ-ÿ])')
    for match in initial_pattern.finditer(protected):
        orig = match.group(0)
        token = f'__INIT_{len(placeholder_map)}__'
        placeholder_map[token] = orig
        protected = protected.replace(orig, token)

    parts = []
    for sentence in re.split(r'(?<=[.!?])(?=\s)', protected):
        # Restaurar tokens en la oración
        for token, orig in placeholder_map.items():
            sentence = sentence.replace(token, orig)
        while len(sentence) > 500:
            end = sentence.rfind(' ', 0, 500)
            if end < 8:
                end = 500
            parts.append(sentence[:end])
            sentence = sentence[end:]
        if len(sentence.strip()) >= 8:
            parts.append(sentence)
        elif sentence and parts and len(parts[-1] + sentence) <= 500:
            parts[-1] += sentence

    return [{'id': f'quote_{i:03d}', 'text': part} for i, part in enumerate(parts, 1)]

