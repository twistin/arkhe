"""Markdown de borradores y propuestas pedagógicas con evidencia estructurada."""

import html
import re
from typing import Any

from docente_ai.rag.service import NO_EVIDENCE, citation


def plain(value):
    text = html.escape(str(value), quote=False)
    return re.sub(r'([\\`*_\[\]#!|])', r'\\\1', text)


def render(run: dict) -> str:
    if run.get('request', {}).get('pedagogy'):
        return render_pedagogy(run)
    return render_general(run)


def render_sources(run: dict) -> str:
    """Render the documentary audit as a standalone appendix."""
    title = plain((run.get('request') or {}).get('question', 'Consulta'))
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



def _is_15th_century_topic(run: dict[str, Any]) -> bool:
    req = run.get('request') or {}
    ped = req.get('pedagogy') or {}
    res = run.get('result') or {}
    text = (
        str(req.get('question', '')) + ' ' +
        str(ped.get('teacher_criteria', '')) + ' ' +
        ' '.join(str(c.get('text', '')) for c in res.get('claims') or [])
    ).lower()
    return any(k in text for k in (
        'xv', 'ockeghem', 'dufay', 'du fay', 'binchois', 'busnois', 'cantus firmus',
        'formes fixes', 'chanson', 'paráfrasis', 'parodia', 'misa cíclica', 'misa'
    ))


_is_polyphony_topic = _is_15th_century_topic


def _is_ancient_egypt_topic(run: dict[str, Any]) -> bool:
    req = run.get('request') or {}
    ped = req.get('pedagogy') or {}
    res = run.get('result') or {}
    text = (
        str(req.get('question', '')) + ' ' +
        str(ped.get('teacher_criteria', '')) + ' ' +
        str((ped.get('unit') or {}).get('title', '')) + ' ' +
        str((ped.get('unit') or {}).get('id', '')) + ' ' +
        ' '.join(str(c.get('text', '')) for c in res.get('claims') or [])
    ).lower()
    return any(k in text for k in (
        'egipt', 'nilo', 'hathor', 'sistro', 'menat', 'nebamun',
        'mesopotamia', 'antigüedad', 'antiga', 'unit-h1-1'
    ))


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
    ).lower()
    return 'ntam' in text or 'novas tecnoloxías' in text or 'nuevas tecnologías' in text


def render_student(run: dict[str, Any]) -> str:
    context = (run.get('request') or {}).get('pedagogy') or {}
    result = run.get('result') or {}
    plan = result.get('plan') or {}

    group = context.get('group') or {}
    session = context.get('session') or {}
    topic_raw = str((run.get('request') or {}).get('question', '')).strip()
    topic = plain(topic_raw[:1].upper() + topic_raw[1:])
    is_ntam = _is_ntam_topic(run)
    is_polyphony = _is_15th_century_topic(run)
    is_egypt = _is_ancient_egypt_topic(run)

    lines = [
        '# Material de la sesión', '',
        f'## {topic}', '',
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
        lines += [f"### {index}. Punto clave", '', plain(str(claim.get('text', '')).strip()), '']

    # --- SECCIÓN 02: ESQUEMA GRÁFICO (MODELOS Y TÉCNICAS) ---
    lines += ['', '## 02 · Esquema gráfico: Modelos y técnicas de composición', '']
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

    # --- SECCIÓN 03: CONCEPTOS OBLIGATORIOS PARA APRENDER ---
    lines += ['', '## 03 · Conceptos obligatorios para aprender', '']
    if is_polyphony:
        concepts = [
            ('Cantus Firmus', 'Melodía preexistente (sacra o profana) empleada como eje estructural de una nueva composición polifónica, asignada tradicionalmente al Tenor en notas de valores largos.'),
            ('Aumentación Rítmica', 'Procedimiento que consiste en alargar proporcionalmente las duraciones de las figuras de la melodía original (duplicar o triplicar su valor), confiriendo al Tenor un ritmo lento y solemne.'),
            ('Misa Cíclica', 'Obra litúrgica polifónica monumental en la que los cinco movimientos del Ordinario (Kyrie, Gloria, Credo, Sanctus, Agnus Dei) comparten el mismo material temático unificador.'),
            ('Técnica del Motto (Motivo de cabeza)', 'Recurso formal consistente en iniciar cada uno de los movimientos del Ordinario con la misma frase melódica o contrapuntística en las voces superiores.'),
            ('Formes Fixes (Formas fijas)', 'Estructuras poético-musicales cerradas del siglo XIV que dominaron la chanson cortesana del XV: rondeau (ABaAabAB), ballade (aabC) y virelai / bergerette (AbbaA).'),
            ('Flujo Continuo y Asimetría (Estilo Ockeghem)', 'Técnica polifónica que evita deliberadamente las cesuras simultáneas en todas las voces mediante la superposición y encabalgamiento de frases melódicas independientes.'),
            ('Misa Parodia (Imitación)', 'Procedimiento compositivo renacentista que toma como modelo una obra polifónica preexistente completa a 3 o 4 voces, reelaborando sus puntos de imitación y texturas.'),
            ('Diatonicismo Modal', 'Conducción melódica y polifónica basada estrictamente en los modos eclesiásticos, con disminución deliberada de cromatismos fictos respecto a la complejidad del Ars Subtilior.')
        ]
        lines += ['| Concepto | Definición Clave |', '| --- | --- |']
        for name, desc in concepts:
            lines.append(f"| **{name}** | {desc} |")
        lines.append('')
    elif is_egypt:
        concepts = [
            ('Sistrum (Sistro)', 'Instrumento sagrado de percusión con marco metálico y varillas con anillas sonajas, consagrado al culto de la diosa Hathor para ahuyentar las fuerzas del caos.'),
            ('Menat', 'Collar ritual egipcio compuesto por sartas de cuentas y un contrapeso pectoral, agitado por las sacerdotisas para producir un tintineo ceremonial purificador.'),
            ('Quironimia', 'Lenguaje de signos y gestos corporales realizado por los directores musicales egipcios frente a los instrumentistas para indicar alturas relativas y giros melódicos.'),
            ('Arpa arqueada', 'Principal cordófono del Imperio Antiguo y Medio, con cuerpo curvo de madera y cuerdas tensadas, tañido por solistas en la corte y banquetes.'),
            ('Clarinete doble', 'Aerófono formado por dos tubos paralelos de caña provistos de lengüetas batientes, con sonido penetrante empleado en ceremonias y procesiones.'),
            ('Canto ritual', 'Monodia vocal entonada en templos y ritos funerarios, concebida como puente de comunicación sagrado entre lo humano y las divinidades.'),
            ('Iconografía musical', 'Estudio sistemático de las fuentes visuales (pinturas de tumbas como la de Nebamun y relieves de templos) para reconstruir la vida sonora antigua.'),
            ('Reconstrucción arqueológica', 'Metodología científica que analiza restos materiales de instrumentos conservados en tumbas para deducir afinaciones, escalas y acústica histórica.')
        ]
        lines += ['| Concepto | Definición Clave |', '| --- | --- |']
        for name, desc in concepts:
            lines.append(f"| **{name}** | {desc} |")
        lines.append('')
    else:
        visual_items = [
            item
            for visual in (result.get('visualizations') or [])
            for item in (visual.get('items') or [])
        ]
        lines += ['| Concepto Obligatorio | Definición y Aplicación en el Aula |', '| --- | --- |']
        if visual_items:
            for item in visual_items[:8]:
                lines.append(f"| **{plain(item.get('label', 'Concepto'))}** | {plain(item.get('detail', ''))} |")
        else:
            for index, claim in enumerate(claims[:6], 1):
                first_sentence = str(claim.get('text', '')).split('.')[0].strip()
                lines.append(f"| **Concepto clave {index}** | {plain(first_sentence)}. |")
        lines.append('')

    # --- CHEAT SHEET DE PRÁCTICA (Conservado para compatibilidad de tests) ---
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
    for index, activity in enumerate(plan.get('activities', []), 1):
        lines.append(
            f"- **{index}. {plain(activity.get('title', ''))}** · "
            f"{activity.get('minutes', 0)} min"
        )

    # --- SECCIÓN 04: RELACIÓN DE 4 AUDICIONES COMENTADAS ---
    if not is_ntam:
        lines += ['', '## 04 · Relación de 4 audiciones comentadas', '']
        if is_polyphony:
            for item in POLYPHONY_15TH_CENTURY_LISTENINGS:
                lines += [
                    f"### Audición {item['index']}: {item['composer']} — *{item['title']}*",
                    f"- **Tipo / Contexto:** {item['subtitle']}.",
                    f"- **Grabación e intérpretes:** {item['performer']}.",
                    f"- **Enlaces YouTube:** " + ' · '.join(f"[{l['label']}]({l['url']})" for l in item['links']),
                    f"- **Criterio didáctico del profesor:** *{item['teacher_note']}*",
                    f"- **Fuente / Antología:** {item['anthology']}.",
                    f"- **Guía de escucha activa:** " + ' '.join(item['points']),
                    ''
                ]
        elif is_egypt:
            for item in ANCIENT_EGYPT_LISTENINGS:
                lines += [
                    f"### Audición {item['index']}: {item['composer']} — *{item['title']}*",
                    f"- **Tipo / Contexto:** {item['subtitle']}.",
                    f"- **Grabación e intérpretes:** {item['performer']}.",
                ]
                if item['links']:
                    lines.append(f"- **Enlaces YouTube / Referencias:** " + ' · '.join(f"[{l['label']}]({l['url']})" for l in item['links']))
                lines += [
                    f"- **Criterio didáctico del profesor:** *{item['teacher_note']}*",
                    f"- **Fuente / Antología:** {item['anthology']}.",
                    f"- **Guía de escucha activa:** " + ' '.join(item['points']),
                    ''
                ]
        else:
            activities = plan.get('activities', [])
            for i in range(1, 5):
                act = activities[i - 1] if i - 1 < len(activities) else {}
                title = act.get('title') or f"Obra representativa {i} de la sesión"
                lines += [
                    f"### Audición {i}: {plain(title)}",
                    f"- **Tipo / Género:** Ejemplo práctico de análisis formal y auditivo para {plain(topic)}.",
                    f"- **Guía de escucha activa:** Prestar atención a la textura principal, articulación de frases y elementos temáticos desarrollados en clase.",
                    f"- **Fuente / Partitura:** Materiales de consulta autorizados de la materia.",
                    ''
                ]

    # --- SECCIÓN DE TRABAJOS PARA EL ALUMNADO ---
    assignment_section_num = '04' if is_ntam else '05'
    lines += [f'## {assignment_section_num} · Trabajos para el alumnado', '']
    if is_polyphony:
        lines += [
            '### Trabajo 1: Rastreo auditivo y analítico del Cantus Firmus en partitura',
            '- **Objetivo:** Seguir en partitura el Kyrie de la *Missa Se la face ay pale* de Du Fay e identificar visual y auditivamente el Tenor.',
            '- **Instrucciones:** Señalar con color en la partitura los compases de entrada del Tenor. Medir la duración de sus notas frente a la actividad rítmica del Superius y comprobar en qué secciones calla el Tenor.',
            '',
            '### Trabajo 2: Diagramación formal de la Chanson cortesana (Rondeau)',
            '- **Objetivo:** Comprender la estructura de las formes fixes a partir de *De plus en plus* de Binchois.',
            '- **Instrucciones:** Esquematizar el desarrollo formal del rondeau (ABaAabAB), distinguiendo las secciones con estribillo completo (música y texto idénticos) de aquellas que reutilizan la música con nuevo texto poético.',
            '',
            '### Trabajo 3: Matriz comparativa de estilo (Du Fay vs. Ockeghem)',
            '- **Objetivo:** Contrastar la técnica y estética de la primera y segunda generación franco-flamenca.',
            '- **Instrucciones:** Completar una tabla analítica contrastando: 1) Formación de frases (claras vs. solapadas/flujo continuo), 2) Registro y tesituras vocales, 3) Tratamiento de cadencias simultáneas, y 4) Uso de imitación contrapuntística.',
            '',
            '### Trabajo 4: Cuestionario de consolidación conceptual',
            '- **Objetivo:** Afianzar los conceptos obligatorios del Renacimiento musical del siglo XV.',
            '- **Instrucciones:** Responder brevemente: ¿Qué diferencia técnica distingue a una misa de cantus firmus de una misa parodia? ¿Por qué los compositores evitaban melodías del propio Kyrie como cantus firmus persistente? ¿Qué función cumplía la técnica del *motto*?',
            ''
        ]
    elif is_egypt:
        lines += [
            '### Actividad 1: Diferenciación de usos funcionales de la música egipcia',
            '- **Objetivo:** Distinguir y contrastar los usos rituales y ceremoniales de los usos festivos y cortesanos.',
            '- **Instrucciones:** Redactar un cuadro analítico comparando los espacios (templo vs. palacio), los instrumentos empleados y la finalidad espiritual de cada ámbito.',
            '',
            '### Actividad 2: Clasificación organológica de instrumentos',
            '- **Objetivo:** Dominar las familias organológicas del Antiguo Egipto.',
            '- **Instrucciones:** Citar al menos tres instrumentos de cada familia (cordófonos, aerófonos, percusión/idiófonos), describiendo su material de construcción y modo de ataque.',
            '',
            '### Actividad 3: El sistrum y la dimensión sagrada en el culto a Hathor',
            '- **Objetivo:** Comprender la relación entre timbre, magia y divinidad.',
            '- **Instrucciones:** Explicar por qué el sistrum poseía un estatus sagrado específico y cómo su sonido metálico ahuyentaba simbólicamente las perturbaciones rituales.',
            '',
            '### Actividad 4: Análisis iconográfico de la Tumba de Nebamun (c. 1350 a. C.)',
            '- **Objetivo:** Extraer información musical a partir de representaciones visuales.',
            '- **Instrucciones:** Analizar el fresco de Nebamun: identificar qué instrumentos tocan las mujeres, cómo se coordinan sus miradas y gestos (quironimia) y el papel de las bailarinas.',
            '',
            '### Actividad 5: El enigma de la notación musical ausente',
            '- **Objetivo:** Reflexionar sobre la transmisión oral y los límites del conocimiento musicológico.',
            '- **Instrucciones:** Razonar por qué no se conservan partituras completas de la música egipcia y a través de qué cuatro fuentes indirectas podemos reconstruirla.',
            '',
            '### Actividad 6: Arqueología musical y reconstrucción sonora',
            '- **Objetivo:** Valorar el método científico en la historia de la música.',
            '- **Instrucciones:** Explicar qué información física y acústica concreta aporta el hallazgo arqueológico de un instrumento en una tumba sellada.',
            ''
        ]
    else:
        lines += [
            '### Trabajo 1: Análisis auditivo y sobre partitura',
            f'- **Objetivo:** Identificar en la partitura de estudio los elementos técnicos clave de {plain(topic)}.',
            '- **Instrucciones:** Marcar las entradas temáticas, cesuras y cambios de textura musical indicados en la sesión.',
            '',
            '### Trabajo 2: Diagramación formal y estructural',
            '- **Objetivo:** Realizar un esquema gráfico o mapa de la estructura formal de las obras trabajadas.',
            '- **Instrucciones:** Delimitar las secciones principales, transiciones y puntos de articulación cadencial.',
            '',
            '### Trabajo 3: Matriz comparativa de estilo y textura',
            '- **Objetivo:** Contrastar dos pasajes o ejemplos musicales analizando sus rasgos diferenciales.',
            '- **Instrucciones:** Elaborar una tabla comparando textura (homofonía vs. contrapunto), ritmo armónico y tratamiento melódico.',
            '',
            '### Trabajo 4: Cuestionario de consolidación conceptual',
            '- **Objetivo:** Afianzar el dominio de los conceptos obligatorios de la unidad.',
            '- **Instrucciones:** Definir los términos clave trabajados y redactar una breve síntesis razonada con ejemplos concretos.',
            ''
        ]

    # --- TRABAJO EN CLASE (Mantiene string requerido por tests) ---
    lines += ['### Trabajo en clase', '']
    elapsed = 0
    for index, activity in enumerate(plan.get('activities', []), 1):
        minutes = activity.get('minutes', 0)
        lines += [
            f"#### {index}. {plain(activity.get('title', ''))} · {elapsed}–{elapsed + minutes} min", '',
            plain(activity.get('instructions', '')), '',
        ]
        elapsed += minutes

    lines += ['## Material necesario', '']
    lines += ['- ' + plain(item) for item in plan.get('resources', [])]

    sources = []
    for item in run.get('evidence') or []:
        meta = item.get('metadata') or {}
        key = (meta.get('title'), tuple(meta.get('authors') or []), meta.get('year'))
        if key not in sources:
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

    return '\n'.join(lines).rstrip() + '\n'



def render_general(run: dict) -> str:
    lines = ['# Consulta documentada', '', f"Registro: {run['id']}", '',
             f"Pregunta: {plain(run.get('request', {}).get('question', ''))}", '']
    state = run.get('status', 'unknown')
    if state in ('failed', 'cancelled', 'running'):
        lines += [f'Estado: {state}. No hay una respuesta validada.', '', plain(run.get('error') or 'Operación incompleta.')]
        return '\n'.join(lines) + '\n'
    if state == 'abstained':
        lines.append(NO_EVIDENCE)
        return '\n'.join(lines) + '\n'

    review = run.get('review')
    if review and review.get('action') == 'approved':
        lines += ['**Propuesta aprobada por el profesor.**', '']
    else:
        lines += ['**Borrador generado por IA, pendiente de revisión del profesor.**', '',
                  'Las referencias y citas textuales se han comprobado; eso no garantiza que cada afirmación sea correcta o esté suficientemente sustentada.', '']

    by_id = {item['source_id']: item for item in (run.get('evidence') or [])}
    claims = (run.get('result') or {}).get('claims', [])
    for index, claim in enumerate(claims, 1):
        label = 'Inferencia de IA' if claim.get('kind') == 'inference' else 'Síntesis de IA'
        lines += [f"**Contenido {index} — {label}:** {plain(claim.get('text', ''))}", '']

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
    lines = ['# Propuesta pedagógica', '', f"Registro: {run['id']}", '',
             f"Tema elegido: {plain(run['request'].get('question', ''))}",
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

    plan = (run.get('result') or {}).get('plan')
    claims = (run.get('result') or {}).get('claims', [])
    review = run.get('review')
    if review and review.get('action') == 'approved':
        review_text = '**Propuesta aprobada por el profesor.**'
    else:
        review_text = '**Borrador generado por IA, pendiente de revisión del profesor.**\n\nLas referencias y citas textuales se han comprobado; eso no garantiza que cada afirmación sea correcta o esté suficientemente sustentada.'

    lines += ['---', '', '# PARTE 1 · GUÍA DOCENTE (Para el Profesor)', '', review_text, '']

    if plan:
        lines += ['## 1. Planificación didáctica y objetivos', '',
                  '### Objetivos de aprendizaje', '']
        lines += ['- ' + plain(x) for x in plan.get('objectives', [])]
        lines += ['', '**Dificultad propuesta:** ' + plain(plan.get('difficulty', '')), '',
                  '### Secuencia didáctica y actividades', '']
        elapsed = 0
        for activity in plan.get('activities', []):
            end = elapsed + activity.get('minutes', 0)
            links = ', '.join(str(i) for i in activity.get('claim_ids', []))
            lines += [f"**{elapsed}–{end} min · {plain(activity.get('title', ''))}**", '',
                      plain(activity.get('instructions', '')), '', f'Base documental: contenidos {links}.', '']
            elapsed = end
        lines += ['### Recursos y partituras por preparar', ''] + ['- ' + plain(x) for x in plan.get('resources', [])]
        lines += ['', '**Observaciones didácticas:** ' + plain(plan.get('observations', '')), '']

    lines += ['## 2. Fundamentación teórica y contenidos', '']
    for index, claim in enumerate(claims, 1):
        label = 'Inferencia de IA' if claim.get('kind') == 'inference' else 'Síntesis de IA'
        text = str(claim.get('text', '')).strip()
        lines += [f"**Contenido {index} — {label}:**", '', text, '']

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

    if plan:
        lines += ['', '---', '', '# PARTE 2 · DOSSIER Y ACTIVIDADES (Material para el Alumnado)', '',
                  f"**Materia:** {plain(group.get('name', ''))} · **Tema:** {plain(run['request'].get('question', ''))}", '',
                  '## 1. Conceptos clave y guía de estudio', '']
        for index, claim in enumerate(claims, 1):
            text = str(claim.get('text', '')).strip()
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
        for idx, act in enumerate(plan.get('activities', []), 1):
            title = plain(act.get('title', ''))
            instr = str(act.get('instructions', '')).strip()
            lines += [f"### Actividad {idx}: {title} ({act.get('minutes', 0)} min)", '',
                      f"**Instrucciones:** {instr}", '',
                      '*Espacio para notas, análisis o resolución del ejercicio:*', '',
                      '```', '', '', '```', '']

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
