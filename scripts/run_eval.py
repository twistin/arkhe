#!/usr/bin/env python3
"""Banco de evaluación de propuestas pedagógicas (Arkhé).

Ejecuta cada caso de eval/casos/*.yaml sobre un entorno temporal seguro
(usando configuraciones de ejemplo y fuentes sintéticas representativas),
guarda la propuesta y el material del alumnado en eval/resultados/<fecha>/<caso>/
y genera un informe en Markdown con checks deterministas automáticos y una columna
vacía para la puntuación manual del profesor según la rúbrica (eval/rubrica.md).
"""

from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
import re
import sys
import tempfile
import time
import yaml

from docente_ai.agents.pedagogy import context_for
from docente_ai.config import load
from docente_ai.generation.render import render, render_student
from docente_ai.generation.service import ask, GenerationFailure
from docente_ai.generation.settings import load_settings as load_generation_settings
from docente_ai.library.service import import_document, authorize_document
from docente_ai.rag.ollama import OllamaEmbedder
from docente_ai.rag.service import index_library
from docente_ai.rag.settings import load_settings as load_rag_settings
from docente_ai.storage import import_config
ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / 'eval' / 'casos'
RESULTS_BASE_DIR = ROOT / 'eval' / 'resultados'

if str(ROOT / 'tests') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tests'))

from test_generation import FakeEmbedder, FakeGenerator


# Fuentes sintéticas representativas para cada caso
# Evitan cualquier acceso a datos personales o archivos reales fuera del entorno de prueba.
CASE_SOURCES = {
    'teoria-griega-seikilos': (
        "La teoría musical en la Antigua Grecia se basaba en el tetracordo, estructura de cuatro sonidos "
        "comprendidos en el intervalo de cuarta justa (epitrito, proporción 4:3). Los géneros del tetracordo "
        "eran diatónico (semitono, tono, tono), cromático (semitono, semitono, tono y medio) y enarmónico "
        "(dos cuartos de tono o diesis y un ditono). Pitágoras (c. 530 a. C.) investigó las proporciones numéricas "
        "acústicas mediante el monocordio, estableciendo la octava (diapason, 2:1), la quinta (diapente, 3:2) "
        "y la cuarta (diatessaron, 4:3). Aristóxeno de Tarento fundamentó la teoría armónica empírica en el siglo IV a. C. "
        "Claudio Ptolomeo sistematizó los modos y géneros armónicos en el siglo II d. C. La notación musical griega "
        "empleaba letras del alfabeto jónico dispuestas de forma directa, rotada o invertida para indicar alturas tanto "
        "en notación vocal como instrumental. El Epitafio de Sícilo (Seikilos), datado entre el siglo II a. C. y el I d. C., "
        "grabado en una estela de mármol de Tralles (Asia Menor), es la composición musical completa más antigua que se conserva. "
        "Está compuesto en el modo frigio (tono jonio) y combina notación alfabética y signos métricos cuantitativos "
        "(stigmê para el arsis y líneas para duraciones dobles o triples). San Agustín y Boecio transmitieron estas teorías "
        "a la Edad Media occidental."
    ),
    'polifonia-siglo-xv': (
        "La polifonía franco-flamenca del siglo XV representa la transición del Ars Subtilior al Renacimiento pleno. "
        "La primera generación borgoñona está encabezada por Guillaume Du Fay (c. 1397-1474) y Gilles Binchois (c. 1400-1460), "
        "quienes asimilaron la contenance angloise de John Dunstaple basada en sonoridades de terceras y sextas paralelas. "
        "Binchois destacó en la chanson profana cortesana cultivando las formes fixes (rondeau, ballade y virelai). "
        "Du Fay consolidó la misa cíclica sobre cantus firmus profano, como en la Missa Se la face ay pale basada en su propia balada, "
        "y la Missa L'homme armé. En la segunda generación, Johannes Ockeghem (c. 1410-1497) expandió la tesitura hacia el registro grave "
        "(Bassus), desarrollando una textura contrapuntística continua sin cesuras cadenciales simultáneas (flujo continuo) "
        "y magistrales recursos canónicos (Missa Prolationum). Las principales técnicas de misa del siglo XV fueron el cantus firmus, "
        "la paráfrasis melódica imitativa y la misa parodia o imitación a partir de modelos polifónicos preexistentes."
    ),
    'ntam-sintesis-audio-digital': (
        "Las Nuevas Tecnologías Aplicadas a la Música (NTAM) abarcan la digitalización y el procesamiento de audio. "
        "La conversión analógico-digital (ADC) consta de muestreo y cuantización. La frecuencia de muestreo (sample rate) "
        "determina el límite de frecuencias reproducibles según el teorema de muestreo de Nyquist-Shannon: la frecuencia "
        "de muestreo debe ser al menos el doble de la frecuencia máxima de la señal para evitar el fenómeno de aliasing o repliegue "
        "espectral, combatido con filtros pasabajos antialiasing. Los estándares comunes son 44.1 kHz (calidad CD) y 48 kHz (vídeo/estudio). "
        "La resolución o profundidad de bits (bit depth: 16 bit, 24 bit) determina el rango dinámico cuantizado (aproximadamente 6 dB por bit), "
        "introduciendo el dither para enmascarar la distorsión armónica de bajo nivel. "
        "En la síntesis sustractiva se parte de osciladores ricos en armónicos: onda senoidal (onda pura sin armónicos), "
        "onda cuadrada o pulso (armónicos impares), onda triangular (armónicos impares con caída rápida) y onda diente de sierra "
        "(todos los armónicos enteros), moldeadas posteriormente mediante filtros resonantes y envolventes ADSR."
    ),
    'barroco-concerto-grosso': (
        "La música instrumental barroca se articuló en torno al bajo continuo (basso continuo), consistente en una línea de bajo "
        "sostenida complementada por indicaciones numéricas cifradas ejecutadas por instrumentos armónicos (clave, órgano, tiorba, laúd) "
        "y melódicos graves (violonchelo, viola da gamba, fagot). Esta práctica sustentó la polaridad tiple-bajo y el principio "
        "de concertación entre fuerzas sonoras contrastantes. "
        "Arcangelo Corelli (1653-1713) fijó los modelos de la sonata a tre (da chiesa y da camera) y del concerto grosso (op. 6), "
        "basado en la alternancia y diálogo dinámico entre el concertino (pequeño grupo de solistas, habitualmente dos violines y violonchelo) "
        "y el ripieno o tutti (el grueso de la orquesta de cuerda). "
        "Antonio Vivaldi (1678-1741) consolidó el concerto solista y la estructura tripartita en tres movimientos (rápido-lento-rápido) "
        "en colecciones como L'estro armonico op. 3, estableciendo el ritornello formal donde el tutti orquestal expone el tema principal "
        "y los episodios solistas modulan con virtuosismo concertante."
    ),
}


def load_test_cases():
    """Carga los archivos YAML de casos en orden alfabético."""
    cases = []
    for path in sorted(CASES_DIR.glob('*.yaml')):
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        if isinstance(data, dict) and 'id' in data:
            cases.append((path, data))
    return cases


def run_single_case(case_data, db_path, rag_settings, gen_settings, embedder_factory=None, generator_factory=None):
    """Ejecuta una propuesta pedagógica para un caso de prueba."""
    from docente_ai.storage import read_config
    config = read_config(db_path)
    existing_group_ids = {g['id'] for g in config.get('groups', [])}
    req_gid = case_data.get('group_id', 'historia-3gp')
    gid = req_gid if req_gid in existing_group_ids else (next(iter(existing_group_ids)) if existing_group_ids else req_gid)

    context = context_for(
        db_path,
        gid,
        case_data.get('duration_minutes', 60),
        unit_id=case_data.get('unit_id'),
        criteria=case_data.get('teacher_criteria', '')
    )
    subject = context['group']['subject_id']

    kwargs = {
        'pedagogy_context': context,
        'subject': subject,
    }
    if embedder_factory:
        kwargs['embedder_factory'] = embedder_factory
    if generator_factory:
        kwargs['generator_factory'] = generator_factory

    result = ask(
        db_path,
        rag_settings,
        gen_settings,
        case_data.get('topic', ''),
        **kwargs
    )
    return result


def evaluate_checks(case_data, run_result):
    """Realiza comprobaciones deterministas automáticas sobre el resultado."""
    checks = {}
    plan = (run_result.get('result') or {}).get('plan') or {}
    claims = (run_result.get('result') or {}).get('claims') or []
    evidence = run_result.get('evidence') or []

    # 1. Número de contenidos / claims
    checks['claims_count'] = len(claims)

    # 2. Número de actividades y suma de tiempos
    activities = plan.get('activities', [])
    checks['activities_count'] = len(activities)
    total_minutes = sum(int(a.get('minutes', 0)) for a in activities)
    expected_minutes = case_data.get('duration_minutes', 60)
    checks['total_minutes'] = total_minutes
    checks['expected_minutes'] = expected_minutes
    checks['timing_matches'] = (total_minutes == expected_minutes)

    # 3. Actividades sin tarea real o sin modalidad explícita para el alumnado
    mode_regex = re.compile(r'\[(?:Individual|En\s+grupo|Colectivo)\]|\b(?:Individual|En\s+grupo|Colectivo)\b', re.IGNORECASE)
    missing_mode_activities = []
    passive_activities = []
    passive_regex = re.compile(r'\b(?:el profesor explica|explicación del profesor|atender a la exposición|escuchar al docente)\b', re.IGNORECASE)

    for i, act in enumerate(activities, 1):
        has_grouping = act.get('grouping') in ('individual', 'grupo', 'colectivo')
        text = f"{act.get('title', '')} {act.get('instructions', '')} {act.get('student_task', '')} {act.get('teacher_notes', '')}"
        if not has_grouping and not mode_regex.search(text):
            missing_mode_activities.append(i)
        task_str = act.get('student_task') or act.get('instructions', '')
        if passive_regex.search(task_str) and not re.search(r'\b(?:alumnado|estudiante|práctica|debate|análisis|escucha|compara|transcribe)\b', task_str, re.I):
            passive_activities.append(i)

    checks['activities_missing_mode'] = missing_mode_activities
    checks['activities_passive'] = passive_activities

    # 4. Criterios del profesor sin cubrir (búsqueda de palabras clave clave en claims y plan)
    criteria_text = case_data.get('teacher_criteria', '')
    # Extraer términos sustantivos de más de 5 letras
    words = [w for w in re.findall(r'\b[A-Za-zÀ-ÿ]{5,}\b', criteria_text)
             if w.lower() not in {'explicar', 'detallar', 'analizar', 'incluir', 'diseñar', 'aula', 'profesor', 'alumnado'}]
    all_gen_text = ' '.join([
        ' '.join(c.get('text', '') + ' ' + c.get('student_summary', '') for c in claims),
        ' '.join(a.get('title', '') + ' ' + a.get('instructions', '') + ' ' + a.get('student_task', '') + ' ' + a.get('teacher_notes', '') + ' ' + a.get('deliverable', '') for a in activities),
        ' '.join(plan.get('objectives', [])),
        str(plan.get('assessment', '')),
    ]).lower()

    missing_keywords = []
    # Muestreo representativo de palabras clave
    for w in sorted(set(words[:15])):
        if w.lower() not in all_gen_text:
            missing_keywords.append(w)
    checks['missing_keywords_sample'] = missing_keywords

    # 5. Fuentes de tipo IA usadas como evidencia
    ai_sources_used = []
    for ev in evidence:
        cat = ev.get('category')
        doc_type = (ev.get('metadata') or {}).get('document_type')
        if cat not in ('documental', 'profesor') or doc_type == 'ia_generated':
            ai_sources_used.append(ev.get('source_id'))
    checks['ai_sources_used'] = ai_sources_used

    # 6. Preservación del tema original frente a normalizado
    raw_topic = case_data.get('topic', '')
    student_md = render_student(run_result)
    pedagogy_md = render(run_result)
    checks['shows_original_topic'] = (raw_topic in student_md or raw_topic in pedagogy_md)

    return checks


def create_synthetic_proposal_response(case_data):
    """Genera una respuesta sintética realista ajustada al caso para líneas base offline."""
    case_id = case_data.get('id', '')
    duration = case_data.get('duration_minutes', 60)

    if case_id == 'teoria-griega-seikilos':
        resp = {
            'status': 'answered',
            'claims': [
                {
                    'kind': 'summary',
                    'text': 'La teoría musical griega se fundamenta en el tetracordo y las proporciones acústicas descubiertas por Pitágoras en el monocordio.',
                    'student_summary': 'La música griega se basaba en el tetracordo, un grupo de cuatro notas afinadas según proporciones matemáticas exactas. Pitágoras descubrió que intervalos como la octava y la quinta corresponden a fracciones numéricas sencillas.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}]
                },
                {
                    'kind': 'summary',
                    'text': 'El Epitafio de Sícilo conserva notación alfabética jónica grabada en una estela de mármol en modo frigio.',
                    'student_summary': 'El Epitafio de Sícilo es la canción completa más antigua conservada en el mundo. Sus notas se escribieron con letras del alfabeto griego sobre los versos poéticos grabados en piedra.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_002'}]
                },
            ],
            'visualizations': [
                {
                    'type': 'relationship',  # Provocamos test de normalización a sequence
                    'title': 'Cronología de la teoría musical griega a la tardoantigüedad',
                    'items': [
                        {'label': 'c. 530 a. C.', 'detail': 'Pitágoras de Samos formula las proporciones acústicas fundamentales en el monocordio.'},
                        {'label': 'c. 330 a. C.', 'detail': 'Aristóxeno de Tarento desarrolla la teoría empírica de los elementos armónicos.'},
                        {'label': 'c. 150 d. C.', 'detail': 'Claudio Ptolomeo compila y sistematiza los modos y géneros en su Harmónica.'},
                        {'label': 'c. 400 d. C.', 'detail': 'San Agustín y Boecio transmiten la teoría y taxonomía griega a Occidente.'},
                    ],
                    'caption': 'Evolución histórica de los principales teóricos musicales grecolatinos.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}]
                }
            ],
            'plan': {
                'objectives': [
                    'Comprender las proporciones pitagóricas y los géneros del tetracordo griego.',
                    'Descifrar y entonar los motivos melódicos del Epitafio de Sícilo.'
                ],
                'difficulty': 'Grado profesional: asimilación de intervalos modales no temperados y notación antigua.',
                'activities': [
                    {
                        'title': 'Exploración del monocordio y proporciones',
                        'teacher_notes': 'Demostrar la división de la cuerda en la mesa de acústica y supervisar el cálculo de razones interválicas.',
                        'student_task': 'Calcula y escucha las proporciones pitagóricas fundamentales (2:1, 3:2, 4:3) en la cuerda tensada y anota sus intervalos correspondientes.',
                        'grouping': 'individual',
                        'deliverable': 'Tabla de proporciones pitagóricas y relaciones interválicas en el cuaderno.',
                        'solution': '2:1 equivale a la octava (diapason), 3:2 a la quinta justa (diapente) y 4:3 a la cuarta justa (diatessaron).',
                        'minutes': 15,
                        'claim_ids': [1]
                    },
                    {
                        'title': 'Lectura y transcripción del Epitafio de Seikilos',
                        'teacher_notes': 'Distribuir facsímiles de la estela y guiar la equivalencia de signos métricos cuantitativos.',
                        'student_task': 'Transcribid las letras griegas a notación moderna en pentagrama y marcad los puntos y barras de duración métrica.',
                        'grouping': 'grupo',
                        'deliverable': 'Partitura transcrita a compás libre con texto griego y traducción castellana.',
                        'solution': 'La melodía se desenvuelve en ámbito de octava en el modo frigio con disyunción y saltos diatónicos sobre las letras jónicas.',
                        'minutes': 25,
                        'claim_ids': [2]
                    },
                    {
                        'title': 'Canto colectivo y debate filosófico',
                        'teacher_notes': 'Dirigir la afinación modal con el monocordio y moderar la reflexión sobre la cosmovisión epitáfica.',
                        'student_task': 'Interpretad vocalmente la melodía completa manteniendo la articulación modal y comentad el mensaje sobre la brevedad de la vida.',
                        'grouping': 'colectivo',
                        'deliverable': 'Interpretación coral al unísono y breve síntesis reflexiva compartida.',
                        'solution': 'Afinación pura sin vibrato y respeto de los ictus métricos (arson y thesin).',
                        'minutes': 20,
                        'claim_ids': [2]
                    },
                ],
                'resources': ['Fotocopias de la estela de Seikilos', 'Monocordio didáctico o teclado'],
                'assessment': 'Evaluación formativa mediante rúbrica de transcripción interválica y precisión afinada en el canto modal colectivo.',
                'observations': 'Ajustar la tesitura vocal a la media del grupo.'
            }
        }
    elif case_id == 'polifonia-siglo-xv':
        resp = {
            'status': 'answered',
            'claims': [
                {
                    'kind': 'summary',
                    'text': 'La generación de Du Fay y Binchois asimiló la contenance angloise y creó la misa cíclica sobre cantus firmus profano.',
                    'student_summary': 'Los compositores franco-flamencos del siglo XV combinaron la dulzura armónica inglesa con el contrapunto continental. Du Fay unificó los movimientos de la misa utilizando una misma canción popular o religiosa en la voz del tenor.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}]
                },
                {
                    'kind': 'summary',
                    'text': 'Johannes Ockeghem amplió el registro grave hacia el Bassus y desarrolló la técnica de flujo continuo.',
                    'student_summary': 'Ockeghem llevó las voces a registros mucho más graves y evitó que todas las voces respiraran a la vez. Su música fluye sin interrupciones claras mediante melodías largas que se solapan continuamente.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_002'}]
                },
            ],
            'visualizations': [],
            'plan': {
                'objectives': [
                    'Diferenciar las técnicas de cantus firmus, paráfrasis y parodia en la misa del siglo XV.',
                    'Identificar auditivamente la textura de flujo continuo de Ockeghem.'
                ],
                'difficulty': '3º GP: análisis formal de polifonía renacentista a cuatro voces.',
                'activities': [
                    {
                        'title': 'Audición comparativa: Binchois vs. Du Fay',
                        'teacher_notes': 'Proyectar la partitura y marcar los puntos de entrada del cantus firmus para guiar la audición analítica.',
                        'student_task': 'Escucha individualmente los fragmentos seleccionados e identifica en tu plantilla la estructura del rondeau y la aumentación del tenor.',
                        'grouping': 'individual',
                        'deliverable': 'Ficha de audición con esquema formal y cronograma de entradas de voz.',
                        'solution': 'Binchois presenta textura a 3 voces clara (rondeau ABaAabAB); Du Fay estira los valores del tenor al triple en el Kyrie.',
                        'minutes': 20,
                        'claim_ids': [1]
                    },
                    {
                        'title': 'Taller de análisis de partitura en Ockeghem',
                        'teacher_notes': 'Organizar mesas de trabajo y verificar el rastreo de cadencias encabalgadas y la tesitura del Bassus.',
                        'student_task': 'Localizad en equipos los compases donde se solapan las frases cadenciales y medid la distancia interválica que alcanza el bajo.',
                        'grouping': 'grupo',
                        'deliverable': 'Partitura con anotaciones analíticas en colores diferenciados para cada voz.',
                        'solution': 'El Bassus desciende hasta Fa grave y las voces superiores inician nuevos motivos antes del reposo del tenor.',
                        'minutes': 25,
                        'claim_ids': [2]
                    },
                    {
                        'title': 'Puesta en común y síntesis de estilos',
                        'teacher_notes': 'Coordinar la puesta en común en la pizarra resumiendo las diferencias técnicas entre ambas generaciones.',
                        'student_task': 'Contrastad en asamblea los hallazgos de cada grupo y elaborad una conclusión colectiva sobre la evolución de la misa cíclica.',
                        'grouping': 'colectivo',
                        'deliverable': 'Esquema mural colaborativo con las tres técnicas canónicas de misa renacentista.',
                        'solution': 'Evolución de cantus firmus rígido a paráfrasis e imitación con ampliación del registro coral.',
                        'minutes': 15,
                        'claim_ids': [1, 2]
                    },
                ],
                'resources': ['Partituras de la Missa Se la face ay pale y Missa Prolationum', 'Equipo de sonido'],
                'assessment': 'Comprobación de la precisión en la localización de cadencias solapadas y dominio de los términos cantus firmus y flujo continuo.',
                'observations': 'Preparar guías de audición con esquemas formales.'
            }
        }
    elif case_id == 'ntam-sintesis-audio-digital':
        resp = {
            'status': 'answered',
            'claims': [
                {
                    'kind': 'summary',
                    'text': 'La digitalización del sonido depende de la frecuencia de muestreo y del teorema de Nyquist-Shannon para evitar el aliasing.',
                    'student_summary': 'Para convertir un sonido analógico en datos digitales se toman miles de muestras por segundo. Según el teorema de Nyquist, la frecuencia de muestreo debe ser como mínimo el doble de la frecuencia sonora más aguda para evitar ruidos parásitos.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}]
                },
                {
                    'kind': 'summary',
                    'text': 'La síntesis sustractiva modela armónicamente ondas complejas mediante osciladores y filtros.',
                    'student_summary': 'En la síntesis sustractiva se genera primero un sonido rico en frecuencias (como diente de sierra o cuadrada) y luego se esculpe recortando armónicos con filtros y modelando el volumen con envolventes temporales.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_002'}]
                },
            ],
            'visualizations': [],
            'plan': {
                'objectives': [
                    'Comprender la relación entre frecuencia de muestreo, aliasing y resolución de bits.',
                    'Diseñar timbres elementales mediante síntesis sustractiva en estación de audio.'
                ],
                'difficulty': 'Iniciación a conceptos físico-matemáticos y herramientas de producción sonora.',
                'activities': [
                    {
                        'title': 'Demostración acústica de muestreo y aliasing',
                        'teacher_notes': 'Conectar analizador espectral en el proyector y reducir paulatinamente el sample rate de una señal pura de barrido.',
                        'student_task': 'Observad en el analizador de espectro cómo aparecen frecuencias reflejadas y describid el timbre resultante al bajar la tasa de muestreo.',
                        'grouping': 'colectivo',
                        'deliverable': 'Cuaderno con anotación gráfica de la frecuencia de Nyquist y frecuencias espurias.',
                        'solution': 'Por debajo del doble de la frecuencia original surgen tonos falsos reflejados (aliasing inarmónico).',
                        'minutes': 15,
                        'claim_ids': [1]
                    },
                    {
                        'title': 'Práctica de síntesis de osciladores en DAW',
                        'teacher_notes': 'Supervisar individualmente la configuración del sintetizador virtual y la selección de formas de onda.',
                        'student_task': 'Genera individualmente una onda de diente de sierra y una onda cuadrada, comparando su contenido armónico auditivo y visual.',
                        'grouping': 'individual',
                        'deliverable': 'Preset guardado en el sintetizador virtual con ambas formas de onda puras.',
                        'solution': 'Diente de sierra contiene todos los armónicos; cuadrada contiene solo armónicos impares con sonoridad hueca.',
                        'minutes': 25,
                        'claim_ids': [2]
                    },
                    {
                        'title': 'Esculpido tímbrico con filtro y envolvente',
                        'teacher_notes': 'Plantear un reto de modelado tímbrico (sonido percusivo o pad suave) y resolver dudas sobre el tiempo de decaimiento.',
                        'student_task': 'Diseñad en parejas un timbre con filtro paso bajo resonante y aplicad una envolvente ADSR corta para crear un sonido de bajo percusivo.',
                        'grouping': 'grupo',
                        'deliverable': 'Archivo de proyecto exportado con el sonido programado y captura de pantalla de los parámetros.',
                        'solution': 'Frecuencia de corte baja con ataque rápido y decaimiento medio en la envolvente del filtro.',
                        'minutes': 20,
                        'claim_ids': [2]
                    },
                ],
                'resources': ['Ordenadores con software DAW o sintetizador virtual', 'Auriculares de monitorización'],
                'assessment': 'Evaluación práctica del archivo de preset exportado comprobando la correcta parametrización de corte, resonancia y tiempos ADSR.',
                'observations': 'Comprobar antelación la configuración de drivers de audio en las aulas.'
            }
        }
    else:  # Caso Barroco
        resp = {
            'status': 'answered',
            'claims': [
                {
                    'kind': 'summary',
                    'text': 'El bajo continuo constituyó el cimiento armónico y estructural de la música barroca instrumental.',
                    'student_summary': 'El bajo continuo es la base armónica que sostiene casi toda la música del Barroco. Un instrumento grave (como el violonchelo) toca la línea melódica mientras otro armónico (como el clave) improvisa los acordes indicados con números.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}]
                },
                {
                    'kind': 'summary',
                    'text': 'Corelli y Vivaldi definieron los principios del concerto grosso y del concerto solista con forma ritornello.',
                    'student_summary': 'En el concerto barroco dialogan grupos de diferente tamaño. En el concerto grosso contrasta un pequeño grupo de solistas con la orquesta entera, alternando pasajes de conjunto con secciones virtuosas.',
                    'evidence': [{'source_id': 'S1', 'quote': 'quote_002'}]
                },
            ],
            'visualizations': [],
            'plan': {
                'objectives': [
                    'Diferenciar las texturas de concertino y ripieno en el concerto grosso.',
                    'Reconocer la alternancia de ritornellos y episodios solistas en Vivaldi.'
                ],
                'difficulty': '3º GP: análisis formal de texturas concertantes del siglo XVIII.',
                'activities': [
                    {
                        'title': 'Audición analítica: Concerto grosso de Corelli',
                        'teacher_notes': 'Facilitar la guía de audición cronometrada y destacar el contraste tímbrico entre tríos y tutti.',
                        'student_task': 'Anota en tu ficha individual cada alternancia dinámica entre concertino y ripieno indicando los cambios de textura.',
                        'grouping': 'individual',
                        'deliverable': 'Esquema cronometrado del diálogo concertante en la ficha de audición.',
                        'solution': 'El concertino expone pasajes a tres voces (2 violines y bajo); el ripieno interviene en bloque homofónico como refuerzo.',
                        'minutes': 20,
                        'claim_ids': [1, 2]
                    },
                    {
                        'title': 'Análisis sobre partitura de la forma ritornello',
                        'teacher_notes': 'Organizar grupos para seguir la partitura de Vivaldi y señalar las modulaciones en los solos.',
                        'student_task': 'Señalad en grupos con colores diferentes los temas del ritornello del tutti y las modulaciones motívicas del solista.',
                        'grouping': 'grupo',
                        'deliverable': 'Partitura con esquema de bloques formales y modulaciones tonales delimitadas.',
                        'solution': 'El ritornello regresa en tonalidades vecinas de forma abreviada intercalando episodios virtuosísticos modulantes.',
                        'minutes': 25,
                        'claim_ids': [2]
                    },
                    {
                        'title': 'Taller colectivo de realización de bajo cifrado',
                        'teacher_notes': 'Escribir una línea de bajo cifrado en la pizarra y guiar la disposición de terceras y quintas a cuatro voces.',
                        'student_task': 'Completad colectivamente en el piano o en la pizarra las notas de los acordes según los números cifrados del compás.',
                        'grouping': 'colectivo',
                        'deliverable': 'Resolución armónica correcta a cuatro partes del fragmento cifrado.',
                        'solution': 'Cifrado 6 indica primera inversión (tercera y sexta); cifrado sin número implica tríada fundamental en estado 5/3.',
                        'minutes': 15,
                        'claim_ids': [1]
                    },
                ],
                'resources': ['Partituras de estudio de Corelli y Vivaldi', 'Grabaciones de referencia'],
                'assessment': 'Verificación de la correcta delimitación de ritornellos en la partitura y resolución coherente de las cifras del bajo armónico.',
                'observations': 'Facilitar esquemas formales visuales para seguir el ritornello.'
            }
        }

    # Generar cobertura automática vinculando claims a los requisitos extraídos
    from docente_ai.rag.planning import extract_requirements
    from docente_ai.generation.settings import GenerationSettings
    reqs = extract_requirements(case_data.get('topic', ''), case_data.get('teacher_criteria', ''), GenerationSettings('eval'), generator_factory=None)
    coverage = []
    num_claims = len(resp.get('claims', []))
    for idx, r in enumerate(reqs):
        cid = (idx % num_claims) + 1 if num_claims > 0 else 1
        coverage.append({
            'requirement_id': r['id'],
            'status': 'cubierto',
            'claim_ids': [cid],
            'note': f"Requisito cubierto con la fundamentación del contenido {cid}."
        })
    resp['coverage'] = coverage
    return resp


def run_benchmark(offline=False, enable_review=False, provider=None, model=None, date_str=None, case_filter=None):
    """Ejecuta el banco de pruebas."""
    cases = load_test_cases()
    if case_filter:
        cases = [(p, d) for p, d in cases if d.get('id') == case_filter or case_filter in p.stem]
    if not cases:
        print("No se encontraron casos coincidentes en eval/casos/*.yaml")
        return []

    date_str = date_str or datetime.now().strftime('%Y-%m-%d_%H%M%S')
    run_dir = RESULTS_BASE_DIR / date_str
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"============================================================")
    print(f"  BANCO DE EVALUACIÓN DE PROPUESTAS PEDAGÓGICAS (ARKHÉ)")
    print(f"  Fecha: {date_str}")
    print(f"  Casos encontrados: {len(cases)}")
    print(f"  Revisión automática: {'ACTIVADA' if enable_review else 'DESACTIVADA'}")
    prov_label = provider or 'ollama'
    print(f"  Modo: {'Sintético determinista (Offline)' if offline else f'Modelo generativo activo ({prov_label})'}")
    print(f"============================================================\n")

    rag_cfg_path = (ROOT / 'config/rag.yaml') if (not offline and (ROOT / 'config/rag.yaml').exists()) else (ROOT / 'config/rag.example.yaml')
    ped_cfg_path = (ROOT / 'config/pedagogy.yaml') if (not offline and (ROOT / 'config/pedagogy.yaml').exists()) else (ROOT / 'config/pedagogy.example.yaml')
    rag_settings = load_rag_settings(rag_cfg_path)
    gen_settings = load_generation_settings(ped_cfg_path)

    if provider == 'deepseek' or (not offline and provider != 'ollama'):
        from docente_ai.llm.presets import PRESETS
        preset = PRESETS['deepseek']
        gen_settings = replace(
            gen_settings,
            provider='deepseek',
            model=model or 'deepseek-chat',
            base_url=preset['base_url'],
            data_residency=preset['data_residency'],
            response_format=preset['response_format'],
            enable_review=enable_review,
            num_ctx=65536,
            max_output_tokens=8192,
        )
        gen_settings = replace(gen_settings, remote_consent=gen_settings.consent_scope)
    else:
        # Configurar revisión y contexto
        gen_settings = replace(gen_settings, enable_review=enable_review)
        if gen_settings.input_budget < 10000:
            gen_settings = replace(gen_settings, num_ctx=12288, max_output_tokens=1536)

    results_report = []

    with tempfile.TemporaryDirectory(prefix='docente-eval-') as tmpdir:
        if not offline and (ROOT / 'data/docente.sqlite3').exists():
            # Ejecución real contra la biblioteca del profesor sobre copia temporal (no contamina data/docente.sqlite3)
            import shutil
            db_path = Path(tmpdir) / 'docente_eval.sqlite3'
            shutil.copy2(ROOT / 'data/docente.sqlite3', db_path)
            lib_link = Path(tmpdir) / 'library'
            if (ROOT / 'data/library').exists() and not lib_link.exists():
                lib_link.symlink_to((ROOT / 'data/library').resolve())
            from docente_ai.rag.ollama import OllamaEmbedder
            embedder_factory = OllamaEmbedder
        else:
            db_path = Path(tmpdir) / 'docente.sqlite3'
            # Modo offline / pruebas unitarias: entorno temporal seguro
            import_config(db_path, load(ROOT / 'config/teaching.example.yaml'))

            # Fuentes sintéticas marcadas con origin 'generado_ia' y tipo 'texto_prueba' (nunca 'bibliografia')
            for case_id, content in CASE_SOURCES.items():
                src_file = Path(tmpdir) / f"{case_id}.txt"
                src_file.write_text(content, encoding='utf-8')
                doc = import_document(db_path, src_file, category='documental', subjects=['historia-i'],
                                      values={
                                          'title': f"Texto de prueba sintetico: {case_id}",
                                          'authors': ['Entorno de prueba (offline)'],
                                          'origin': 'generado_ia',
                                          'document_type': 'texto_prueba'
                                      })
                authorize_document(db_path, doc['document_id'], enabled=True)

            embedder_factory = FakeEmbedder
            index_library(db_path, rag_settings, FakeEmbedder())

        for case_path, case_data in cases:
            case_id = case_data.get('id', case_path.stem)
            print(f"-> Ejecutando caso: [{case_id}] {case_data.get('topic')[:50]}...")
            start_t = time.perf_counter()

            if offline:
                fake_response = create_synthetic_proposal_response(case_data)
                def make_gen(s, resp=fake_response):
                    class EvalGen(FakeGenerator):
                        def generate(self, messages):
                            sys_content = str(messages[0].get('content', '')).lower() if messages else ''
                            if 'revisor' in sys_content or 'rúbrica' in sys_content or 'rubrica' in sys_content:
                                # Evaluación por el revisor con la rúbrica
                                from docente_ai.agents.reviewer import CRITERIA_KEYS
                                review_scores = {k: 3 for k in CRITERIA_KEYS}
                                # Si hay particularidades en el caso se pueden reflejar
                                review_json = {
                                    'scores': review_scores,
                                    'issues': [],
                                    'summary': 'Propuesta alineada con la rúbrica pedagógica.'
                                }
                                return {'content': json.dumps(review_json), 'metrics': {'eval_count': 120, 'prompt_eval_count': 450}}
                            return {'content': json.dumps(resp), 'metrics': {'eval_count': 220, 'prompt_eval_count': 600}}
                    return EvalGen(s)
                generator_factory = make_gen
            else:
                generator_factory = None

            try:
                run_res = run_single_case(
                    case_data, db_path, rag_settings, gen_settings,
                    embedder_factory=embedder_factory,
                    generator_factory=generator_factory
                )
                duration_s = round(time.perf_counter() - start_t, 2)
                status = run_res.get('status', 'unknown')
                print(f"   Estado: {status} ({duration_s}s)")

                # Guardar salidas en directorio del caso
                case_out_dir = run_dir / case_id
                case_out_dir.mkdir(parents=True, exist_ok=True)

                proposal_md = render(run_res)
                student_md = render_student(run_res)

                (case_out_dir / 'propuesta_docente.md').write_text(proposal_md, encoding='utf-8')
                (case_out_dir / 'material_alumnado.md').write_text(student_md, encoding='utf-8')
                (case_out_dir / 'run_result.json').write_text(json.dumps(run_res, ensure_ascii=False, indent=2), encoding='utf-8')
                (case_out_dir / 'caso.yaml').write_text(case_path.read_text(encoding='utf-8'), encoding='utf-8')

                checks = evaluate_checks(case_data, run_res)
                auto_rev = (run_res.get('metrics') or {}).get('auto_review')
                res_metrics = run_res.get('metrics') or {}
                results_report.append({
                    'id': case_id,
                    'topic': case_data.get('topic'),
                    'status': status,
                    'seconds': duration_s,
                    'checks': checks,
                    'auto_review': auto_rev,
                    'metrics': {
                        'prompt_tokens': res_metrics.get('prompt_eval_count'),
                        'completion_tokens': res_metrics.get('eval_count'),
                        'attempts': res_metrics.get('attempts', []),
                        'reviewer_tokens': (auto_rev or {}).get('tokens'),
                        'repair_attempts': res_metrics.get('reviewer_repair_attempts', []),
                    },
                    'dir': str(case_out_dir.relative_to(ROOT)),
                })
            except Exception as exc:
                print(f"   [Error] Falló la ejecución del caso: {exc}")
                results_report.append({
                    'id': case_id,
                    'topic': case_data.get('topic'),
                    'status': 'error',
                    'seconds': round(time.perf_counter() - start_t, 2),
                    'error': str(exc),
                    'checks': None,
                    'auto_review': None,
                    'dir': None,
                })

    # Generar informe Markdown consolidado
    report_md = generate_markdown_report(date_str, results_report, gen_settings)
    report_path = run_dir / 'informe_evaluacion.md'
    report_path.write_text(report_md, encoding='utf-8')

    print(f"\n============================================================")
    print(f"Informe consolidado generado en:")
    print(f"{report_path}")
    print(f"============================================================\n")
    return results_report


def generate_markdown_report(date_str, results, gen_settings):
    """Crea la tabla y el desglose de checks con columna vacía para evaluación manual."""
    has_review = getattr(gen_settings, 'enable_review', False)
    lines = [
        f"# Informe de evaluación de propuestas pedagógicas (Arkhé)",
        "",
        f"- **Fecha de ejecución:** `{date_str}`",
        f"- **Revisión pedagógica automática:** `{'ACTIVADA' if has_review else 'DESACTIVADA'}`",
        f"- **Presupuesto generativo configurado:** `num_ctx={gen_settings.num_ctx}`, `max_output_tokens={gen_settings.max_output_tokens}`, `input_budget={gen_settings.input_budget}`",
        f"- **Rúbrica de referencia:** [`eval/rubrica.md`](../rubrica.md)",
        "",
        "## Resumen de comprobaciones deterministas automáticas",
        "",
        "| Caso | Estado | Contenidos | Actividades | Tiempos | Modalidad OK | Criterios clave ausentes | Fuentes IA | Rev. Rúbrica (/18) | Latencia |",
        "|---|:---:|:---:|:---:|:---:|:---:|---|:---:|:---:|:---:|",
    ]

    for item in results:
        cid = item['id']
        status = item['status']
        secs = f"{item['seconds']}s"
        if status != 'draft' and item.get('checks') is None:
            lines.append(f"| **{cid}** | ❌ Error | — | — | — | — | `{item.get('error', '')}` | — | — | {secs} |")
            continue

        checks = item['checks']
        claims = checks['claims_count']
        acts = checks['activities_count']
        time_status = "✅ Cuadra" if checks['timing_matches'] else f"❌ {checks['total_minutes']}/{checks['expected_minutes']}m"
        missing_modes = len(checks['activities_missing_mode'])
        mode_status = "✅ Sí" if missing_modes == 0 else f"❌ {missing_modes} sin tag"
        missing_kw = ', '.join(checks['missing_keywords_sample'][:4]) or "Ninguna"
        ai_sources = "0" if len(checks['ai_sources_used']) == 0 else f"⚠️ {len(checks['ai_sources_used'])}"

        rev_score = "—"
        if item.get('auto_review') and item['auto_review'].get('scores'):
            sc_dict = item['auto_review']['scores']
            tot = sum(sc_dict.values())
            rep_tag = " (rep)" if item['auto_review'].get('repaired') else ""
            rev_score = f"{tot}/18{rep_tag}"

        lines.append(f"| [`{cid}`]({cid}/) | {status} | {claims} | {acts} | {time_status} | {mode_status} | {missing_kw} | {ai_sources} | {rev_score} | {secs} |")

    lines.extend([
        "",
        "## Desglose por caso de prueba y enlaces a materiales",
        ""
    ])

    for item in results:
        cid = item['id']
        lines.append(f"### Caso: `{cid}`")
        lines.append(f"- **Tema propuesto:** {item['topic']}")
        lines.append(f"- **Estado de la propuesta:** `{item['status']}`")
        if item.get('dir'):
            lines.append(f"- **Guía docente:** [`{item['dir']}/propuesta_docente.md`]({cid}/propuesta_docente.md)")
            lines.append(f"- **Cuaderno del alumnado:** [`{item['dir']}/material_alumnado.md`]({cid}/material_alumnado.md)")
            lines.append(f"- **JSON del run:** [`{item['dir']}/run_result.json`]({cid}/run_result.json)")

        if item.get('checks'):
            c = item['checks']
            lines.append(f"- **Auditoría temporal:** {c['total_minutes']} min asignados sobre {c['expected_minutes']} min esperados ({'Correcto' if c['timing_matches'] else 'DESAJUSTE'}).")
            lines.append(f"- **Actividades sin modalidad (`[Individual]`, `[En grupo]`, `[Colectivo]`):** {c['activities_missing_mode'] or 'Ninguna (todas tienen modalidad explícita)'}.")
            lines.append(f"- **Actividades con formulación meramente pasiva:** {c['activities_passive'] or 'Ninguna (todas tienen tarea activa)'}.")
            lines.append(f"- **Muestreo de términos del profesor revisados en la propuesta:** {', '.join(c['missing_keywords_sample']) if c['missing_keywords_sample'] else 'Todos los términos detectados en el texto'}.")
            lines.append(f"- **Preservación del tema original en la cabecera:** {'Sí' if c['shows_original_topic'] else 'No'}.")
        if item.get('auto_review'):
            rev = item['auto_review']
            lines.append(f"- **Revisión automática:** Puntuaciones: `{rev.get('scores')}`, Reparado: `{rev.get('repaired')}`.")
            if rev.get('issues'):
                lines.append(f"  - Incidencias: {len(rev['issues'])} problemas detectados.")
        lines.append("")

    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Banco de evaluación de propuestas pedagógicas (Arkhé).')
    parser.add_argument('--offline', action='store_true', help='Modo sintético offline sin llamadas LLM.')
    parser.add_argument('--with-review', action='store_true', help='Activar paso de revisión pedagógica automática.')
    parser.add_argument('--compare-review', action='store_true', help='Comparar ejecución sin revisión vs con revisión.')
    parser.add_argument('--provider', default='deepseek', help='Proveedor LLM (deepseek u ollama).')
    parser.add_argument('--model', default='deepseek-chat', help='Modelo generativo.')
    parser.add_argument('--date-str', default=None, help='Fecha o identificador de salida en eval/resultados/<date-str>/')
    parser.add_argument('--case', default=None, help='Filtrar por id de caso específico.')
    args = parser.parse_args()

    offline_mode = args.offline
    with_review = args.with_review
    compare_mode = args.compare_review
    provider = args.provider
    model = args.model

    if compare_mode:
        print("\n>>> EJECUTANDO COMPARACIÓN: REVISIÓN DESACTIVADA VS ACTIVADA <<<\n")
        print("--- 1. Ejecución con Revisión DESACTIVADA ---")
        date_off = args.date_str or (datetime.now().strftime('%Y-%m-%d_%H%M%S') + '_sin_revision')
        res_off = run_benchmark(offline=offline_mode, enable_review=False, provider=provider, model=model, date_str=date_off, case_filter=args.case)
        print("\n--- 2. Ejecución con Revisión ACTIVADA ---")
        date_on = args.date_str or (datetime.now().strftime('%Y-%m-%d_%H%M%S') + '_con_revision')
        res_on = run_benchmark(offline=offline_mode, enable_review=True, provider=provider, model=model, date_str=date_on, case_filter=args.case)

        print("\n" + "=" * 110)
        print("               TABLA COMPARATIVA DETALLADA: REVISIÓN DESACTIVADA VS ACTIVADA")
        print("=" * 110)
        print(f"{'Caso':<28} | {'Sin Rev (s)':<12} | {'Con Rev (s)':<12} | {'Punt. Rúbrica':<14} | {'Reparado':<8} | {'Tokens Gen/Rev/Rep':<25}")
        print("-" * 110)
        for r_off, r_on in zip(res_off, res_on):
            cid = r_off['id']
            t_off = f"{r_off['seconds']}s"
            t_on = f"{r_on['seconds']}s"
            rev = r_on.get('auto_review') or {}
            scores = rev.get('scores') or {}
            tot_score = f"{sum(scores.values())}/18" if scores else "N/A"
            repaired = "Sí" if rev.get('repaired') else "No"

            m_on = r_on.get('metrics') or {}
            gen_tok = f"{m_on.get('prompt_tokens', 0)}in/{m_on.get('completion_tokens', 0)}out"
            rev_tok_dict = m_on.get('reviewer_tokens') or {}
            rev_tok = f"{rev_tok_dict.get('input', 0)}in/{rev_tok_dict.get('output', 0)}out" if rev_tok_dict else "—"
            rep_tok = f"{len(m_on.get('repair_attempts', []))} rep" if m_on.get('repair_attempts') else "0 rep"
            tok_str = f"G:{gen_tok} R:{rev_tok} ({rep_tok})"

            print(f"{cid:<28} | {t_off:<12} | {t_on:<12} | {tot_score:<14} | {repaired:<8} | {tok_str:<25}")
        print("=" * 110 + "\n")
        sys.exit(0)

    run_benchmark(offline=offline_mode, enable_review=with_review, provider=provider, model=model, date_str=args.date_str, case_filter=args.case)
    sys.exit(0)

