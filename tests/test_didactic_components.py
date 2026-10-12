"""Tests para los componentes didácticos musicales deterministas,
glosario griego e importación de transcripciones MusicXML.
"""

import json
from pathlib import Path
import pytest

from docente_ai.agents.pedagogy import validate, ResponseValidationError
from docente_ai.music.didactic import (
    resolver_componente_didactico,
    generar_svg_gran_sistema_perfecto,
    generar_svg_monocordio,
    generar_svg_escalera_intervalos,
    generar_svg_linea_temporal,
    generar_svg_tetracordos,
    construir_hitos_linea_temporal,
    NOTAS_GRAN_SISTEMA_PERFECTO,
    DIVISIONES_MONOCORDIO,
    SUBTITULO_GSP,
)
from docente_ai.teaching.score_resolver import importar_transcripcion_musicxml
from docente_ai.teaching.fichas import get_ficha, is_ficha_verified
from docente_ai.generation.render import render_student, render_pedagogy


def test_validacion_didactic_components_tipos_validos():
    """Valida que pedagogy acepte didactic_components con tipos permitidos y sin código SVG."""
    data = {
        'status': 'answered',
        'coverage': [{'requirement_id': 'R1', 'status': 'cubierto', 'claim_ids': [1], 'note': 'ok'}],
        'claims': [{
            'kind': 'summary',
            'text': 'Teoría del tetracordo.',
            'student_summary': 'En esta lección vas a estudiar la división del tetracordo griego y sus tres géneros fundamentales.',
            'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}],
        }],
        'plan': {
            'objectives': ['Comprender los géneros musicales.', 'Distinguir las afinaciones.'],
            'difficulty': 'Medio',
            'activities': [
                {
                    'title': 'Análisis de tetracordos',
                    'teacher_notes': 'Exposición.',
                    'student_task': 'Analiza el intervalo de cuarta y sus tres géneros.',
                    'grouping': 'individual',
                    'deliverable': 'Esquema comparativo.',
                    'solution': 'Solución.',
                    'minutes': 30,
                    'claim_ids': [1],
                },
                {
                    'title': 'Práctica auditiva',
                    'teacher_notes': 'Audición guiada.',
                    'student_task': 'Compara las frecuencias auditivas.',
                    'grouping': 'individual',
                    'deliverable': 'Ficha de discriminación.',
                    'solution': 'Solución práctica.',
                    'minutes': 30,
                    'claim_ids': [1],
                },
            ],
            'resources': ['Tratado de Aristóxeno'],
            'assessment': 'Evaluación continua',
            'observations': 'Notas',
        },
        'didactic_components': [
            {'tipo': 'tetracordos'},
            {'tipo': 'gran_sistema_perfecto'},
            {'tipo': 'monocordio', 'parametros': {'base_hz': 130.8}},
            {'tipo': 'escalera_intervalos'},
            {'tipo': 'linea_temporal', 'parametros': {'autores': ['Aristóxeno', 'Ptolomeo']}},
        ],
    }

    evidence = [{'source_id': 'S1', 'text': 'Texto de la fuente con quote_001 como pasaje.', 'metadata': {'title': 'Fuente'}, 'passages': [{'id': 'P1', 'text': 'quote_001'}]}]
    context = {'duration_minutes': 60, 'level': 'Superior'}

    res = validate(json.dumps(data), evidence, context)
    assert len(res['didactic_components']) == 5
    assert res['didactic_components'][0]['tipo'] == 'tetracordos'
    assert res['didactic_components'][2]['parametros']['base_hz'] == 130.8


def test_validacion_didactic_components_rechaza_svg_del_modelo():
    """Valida que pedagogy rechace cualquier intento del modelo de devolver código SVG o HTML."""
    data = {
        'status': 'answered',
        'coverage': [{'requirement_id': 'R1', 'status': 'cubierto', 'claim_ids': [1], 'note': 'ok'}],
        'claims': [{
            'kind': 'summary',
            'text': 'Teoría.',
            'student_summary': 'Explicación directa para ti sobre los conceptos teóricos.',
            'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}],
        }],
        'plan': {
            'objectives': ['Objetivo inicial.', 'Objetivo secundario.'],
            'difficulty': 'Medio',
            'activities': [
                {
                    'title': 'Actividad 1',
                    'teacher_notes': 'Notas.',
                    'student_task': 'Tarea práctica.',
                    'grouping': 'individual',
                    'deliverable': 'Entrega.',
                    'solution': 'Solución.',
                    'minutes': 30,
                    'claim_ids': [1],
                },
                {
                    'title': 'Actividad 2',
                    'teacher_notes': 'Notas 2.',
                    'student_task': 'Tarea práctica 2.',
                    'grouping': 'individual',
                    'deliverable': 'Entrega 2.',
                    'solution': 'Solución 2.',
                    'minutes': 30,
                    'claim_ids': [1],
                },
            ],
            'resources': ['Recurso'],
            'assessment': 'Evaluación',
            'observations': 'Notas',
        },
        'didactic_components': [
            {'tipo': 'monocordio', 'parametros': {'grafico': '<svg><line x1="0"/></svg>'}},
        ],
    }
    evidence = [{'source_id': 'S1', 'text': 'Texto de la fuente con quote_001 como pasaje.', 'metadata': {'title': 'Fuente'}, 'passages': [{'id': 'P1', 'text': 'quote_001'}]}]
    context = {'duration_minutes': 60, 'level': 'Superior'}

    with pytest.raises(ResponseValidationError, match='Prohibido incluir código SVG'):
        validate(json.dumps(data), evidence, context)


def test_resolucion_componentes_didacticos():
    """Comprueba la resolución determinista de los 5 componentes didácticos."""
    calculados = ['tetracordos', 'gran_sistema_perfecto', 'monocordio', 'escalera_intervalos']
    for t in calculados:
        res = resolver_componente_didactico(t)
        assert res['tipo'] == t
        assert res['calculado_teoria'] is True
        assert res['verificado'] is True
        assert '<svg' in res['svg']
        assert res['titulo']

    # Línea temporal: factual, NO calculada a partir de teoría
    lt = resolver_componente_didactico('linea_temporal')
    assert lt['tipo'] == 'linea_temporal'
    assert lt['calculado_teoria'] is False
    assert lt['verificado'] is True
    assert '<svg' in lt['svg']
    assert '<svg' in lt['svg_alumnado']

    # GSP: 15 notas exactas La2 a La4, subtítulo canónico y afinaciones
    gsp = resolver_componente_didactico('gran_sistema_perfecto')
    assert len(gsp['notas']) == 15
    assert gsp['notas'][0]['nota_moderna'] == 'La2'
    assert gsp['notas'][-1]['nota_moderna'] == 'La4'
    assert any(n['nombre_griego'] == 'Mese' for n in gsp['notas'])
    assert gsp['subtitulo'] == SUBTITULO_GSP
    assert 'pitagorica' in gsp['afinados']
    assert 'temperada' in gsp['afinados']
    assert len(gsp['afinados']['pitagorica']) == 15
    assert len(gsp['afinados']['temperada']) == 15

    # Monocordio: frecuencias por proporción matemática exacta y nombres canónicos
    mono = resolver_componente_didactico('monocordio')
    div_dict = {d['fraccion']: d for d in mono['divisiones']}
    assert '1/2' in div_dict
    assert '2/3' in div_dict
    assert '3/4' in div_dict

    # 4:3 de 220 = 293.33 Hz (epítriton)
    d_cuarta = div_dict['3/4']
    assert d_cuarta['freq_pitagorica'] == 293.33
    assert 'epítriton' in d_cuarta['nombre_proporcion']

    # 3:2 de 220 = 330.0 Hz (hemiólion)
    d_quinta = div_dict['2/3']
    assert d_quinta['freq_pitagorica'] == 330.0
    assert 'hemiólion' in d_quinta['nombre_proporcion']

    # 2:1 de 220 = 440.0 Hz (diplásion)
    d_octava = div_dict['1/2']
    assert d_octava['freq_pitagorica'] == 440.0
    assert 'diplásion' in d_octava['nombre_proporcion']

    # Tetracordos: afinación dual
    tc = resolver_componente_didactico('tetracordos')
    assert 'pitagorica' in tc['afinados']
    assert 'temperada' in tc['afinados']
    assert tc['afinados']['pitagorica']['diatonico'][1] == 293.33


def test_linea_temporal_dinamica_y_fuentes():
    """Comprueba que la línea temporal se construya con fuentes citadas,
    incluya Platón y Aristóteles si están en evidencias, y marque sin_fuente para docente."""
    evidence = [
        {
            'source_id': 'S1',
            'metadata': {'title': 'La República', 'authors': ['Platón']},
        },
        {
            'source_id': 'S2',
            'metadata': {'title': 'Política', 'authors': ['Aristóteles']},
        },
    ]
    # Solicitamos además San Agustín (que no está en fuentes)
    hitos = construir_hitos_linea_temporal(evidence, autores_solicitados=['San Agustín'])
    autores = [h['autor'] for h in hitos]
    assert any('Platón' in a for a in autores)
    assert any('Aristóteles' in a for a in autores)
    assert any('Agustín' in a for a in autores)

    agustin = next(h for h in hitos if 'Agustín' in h['autor'])
    assert agustin['sin_fuente'] is True
    assert agustin['fuente'] == 'sin fuente en la biblioteca'

    # En el SVG para el docente aparece la advertencia
    svg_doc = generar_svg_linea_temporal(hitos, para_alumnado=False)
    assert '[sin fuente en la biblioteca]' in svg_doc

    # En el SVG para el alumnado NO aparece San Agustín
    svg_alum = generar_svg_linea_temporal(hitos, para_alumnado=True)
    assert 'Agustín' not in svg_alum
    assert '[sin fuente en la biblioteca]' not in svg_alum


def test_linea_temporal_extrae_autores_de_claims_y_visualizaciones():
    """Comprueba que la línea temporal incluya todos los autores citados en claims y visualizaciones,
    y los ordene cronológicamente."""
    claims = [
        {'text': 'Aristóxeno de Tarento expone la división empírica del tetracordo.'},
        {'text': 'Boecio transmite la teoría pitagórica a Occidente en De institutione musica.'},
    ]
    visualizaciones = [
        {
            'title': 'Tratadistas clave',
            'items': [
                {'label': 'Ptolomeo', 'detail': 'Armónicos'},
            ]
        }
    ]
    hitos = construir_hitos_linea_temporal(claims=claims, visualizaciones=visualizaciones)
    autores = [h['autor'] for h in hitos]
    assert any('Aristóxeno' in a for a in autores)
    assert any('Ptolomeo' in a for a in autores)
    assert any('Boecio' in a for a in autores)

    # Comprueba orden cronológico estricto
    anos = [h['ano_numerico'] for h in hitos]
    assert anos == sorted(anos)


def test_glosario_griego_en_ficha_no_verificada():
    """Comprueba que el glosario griego resida en config/fichas/glosario_griego.yaml con verificado: false,
    y que mientras no esté verificada solo aparezca en la guía docente y nunca en el material del alumnado."""
    ficha = get_ficha('glosario_griego')
    assert ficha is not None
    assert ficha.get('verificado') is False
    assert is_ficha_verified(ficha) is False

    conceptos = [c['termino'] for c in ficha.get('conceptos', [])]
    assert 'Phthongos (φθόγγος)' in conceptos
    assert 'Diastema (διάστημα)' in conceptos
    assert 'Systema (σύστημα)' in conceptos
    assert 'Díesis (δίεσις)' in conceptos
    assert 'Ditono (δίτονον)' in conceptos

    run = {
        'id': 'run-test-glosario-grecia',
        'original_topic': 'Teoría musical de la Grecia Antigua y Epitafio de Seikilos',
        'display_title': 'Teoría musical de la Grecia Antigua y Epitafio de Seikilos',
        'evidence': [{
            'source_id': 'S1',
            'metadata': {'title': 'Historia de la Música', 'authors': ['Aristóxeno']},
            'passages': [{'text': 'phthongos, diastema y systema'}],
        }],
        'request': {
            'pedagogy': {
                'group': {'name': 'Historia 4', 'level': 'Superior'},
                'duration_minutes': 60,
            }
        },
        'result': {
            'claims': [{'text': 'Teoría'}],
            'plan': {'objectives': ['Aprender'], 'activities': []},
        }
    }

    # Guía docente: muestra el contenido pendiente de revisión
    doc_teacher = render_pedagogy(run)
    assert 'Contenido de plantilla pendiente de revisión' in doc_teacher
    assert 'Phthongos' in doc_teacher

    # Material del alumnado: NO muestra el glosario mientras verificado: false
    doc_student = render_student(run)
    assert 'Phthongos' not in doc_student


def test_render_student_incluye_componentes_calculados():
    """Comprueba que render_student incluya los componentes didácticos calculados."""
    gsp_res = resolver_componente_didactico('gran_sistema_perfecto')
    tc_res = resolver_componente_didactico('tetracordos')

    run = {
        'id': 'run-test-didactico',
        'original_topic': 'Teoría musical de la Grecia Antigua y Epitafio de Seikilos',
        'display_title': 'Teoría musical de la Grecia Antigua y Epitafio de Seikilos',
        'evidence': [{
            'source_id': 'S1',
            'metadata': {'title': 'Historia de la Música Griega', 'authors': ['Aristóxeno']},
            'passages': [{'text': 'El phthongos es la unidad del diastema y del systema.'}],
        }],
        'request': {
            'pedagogy': {
                'group': {'name': 'Historia 4', 'level': 'Superior'},
                'duration_minutes': 60,
                'session': {'date': '2026-10-15'},
            }
        },
        'result': {
            'claims': [{
                'kind': 'summary',
                'text': 'El tetracordo es el fundamento de los tres géneros.',
                'student_summary': 'El tetracordo griego abarca una cuarta justa fija cuyos límites permanecen inmóviles. En esta sesión podrás observar y escuchar cómo se articulan los géneros diatónico, cromático y enarmónico.',
                'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}],
            }],
            'plan': {
                'objectives': ['Comprender el Gran Sistema Perfecto.'],
                'activities': [{
                    'title': 'Análisis del sistema',
                    'minutes': 60,
                    'student_task': 'Analiza las quince notas y sus tetracordos.',
                    'deliverable': 'Tabla de frecuencias.',
                }],
                'resources': ['Partitura del Epitafio — pendiente, partitura'],
            },
            'resolved_didactic_components': [tc_res, gsp_res],
        }
    }

    doc = render_student(run)
    assert '## Componentes didácticos y análisis teórico' in doc
    assert 'Gran Sistema Perfecto (Systema Teleion Meizon)' in doc
    assert 'Tetracordo descendente mi–si en los tres géneros' in doc
    assert 'Proslambanómenos' in doc



def test_endpoint_import_musicxml(tmp_path):
    """Comprueba el endpoint POST /api/runs/{id}/music_requests/{req_id}/import_musicxml."""
    from docente_ai.config import load
    from docente_ai.storage import import_config
    from docente_ai.web.app import create_app
    from docente_ai.web.workspace import Workspace
    from starlette.testclient import TestClient
    from test_generation import FakeEmbedder, EXAMPLE
    import re
    import sqlite3

    db_path = tmp_path / 'data/docente.sqlite3'
    db_path.parent.mkdir(parents=True)
    import_config(db_path, load(EXAMPLE))

    config = tmp_path / 'config'
    config.mkdir()
    (config / 'rag.yaml').write_text('schema_version: 1\nembeddings:\n  model: embed:1\n')
    (config / 'generation.yaml').write_text('schema_version: 1\ngeneration:\n  model: gen:1\n')
    (config / 'pedagogy.yaml').write_text('schema_version: 1\ngeneration:\n  model: gen:1\n')

    run_id = 'run-test-seikilos'
    initial_result = {
        'status': 'answered',
        'claims': [{'text': 'Teoría'}],
        'plan': {'objectives': ['Aprender'], 'activities': []},
        'music_requests': [{
            'id': 'MR1',
            'work': 'Epitafio de Seikilos',
            'composer': 'Anónimo',
            'activity_title': 'Audición y transcripción',
            'description': 'Melodía completa de la estela de Tralles',
        }],
        'resolved_music_requests': [{
            'request_id': 'MR1',
            'status': 'sin_resolver',
            'candidatos': [],
        }],
    }
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            'INSERT INTO generation_runs (id, created_at, status, prompt_version, original_topic, display_title, request_json, result_json) '
            'VALUES (?, datetime("now"), "draft", "pedagogy:10", "Grecia Antigua", "Grecia Antigua", "{}", ?)',
            (run_id, json.dumps(initial_result))
        )


    ws = Workspace(tmp_path, embedder_factory=FakeEmbedder)
    app = create_app(tmp_path, workspace=ws)

    with TestClient(app, base_url='http://127.0.0.1:8765') as client:
        html = client.get('/').text
        token = re.search(r'name="docente-token" content="([^"]+)"', html).group(1)
        client.headers['X-Docente-Token'] = token

        xml_data = '<?xml version="1.0"?><score-partwise><part id="P1"><measure number="1"><note><pitch><step>E</step><octave>4</octave></pitch></note></measure></part></score-partwise>'
        resp = client.post(
            f'/api/runs/{run_id}/music_requests/MR1/import_musicxml',
            json={
                'musicxml': xml_data,
                'fuente': 'Transcripción propia a partir de la estela de Tralles',
                'titulo': 'Epitafio de Seikilos',
                'compositor': 'Anónimo',
            }
        )
        assert resp.status_code == 200
        run_data = resp.json()
        resolved_reqs = run_data['result']['resolved_music_requests']
        assert len(resolved_reqs) == 1
        assert resolved_reqs[0]['status'] == 'resuelto_catalogo'
        assert resolved_reqs[0]['verificado'] is True
        assert resolved_reqs[0]['ejemplo']['fuente'] == 'Transcripción propia a partir de la estela de Tralles'


def test_seleccion_determinista_componentes_por_tema():
    """Comprueba que seleccionar_componentes_por_tema extraiga los componentes correctos a partir de palabras clave."""
    from docente_ai.music.didactic import seleccionar_componentes_por_tema

    texto_grecia = "El sistema perfecto y los géneros de tetracordos en la música griega. Monocordio de Pitágoras."
    comps = seleccionar_componentes_por_tema(texto_grecia)
    tipos = [c["tipo"] for c in comps]
    assert "tetracordos" in tipos
    assert "gran_sistema_perfecto" in tipos
    assert "monocordio" in tipos
    assert "escalera_intervalos" in tipos
    for c in comps:
        assert c["origen"] == "regla_tema"


def test_linea_temporal_autores_en_pasajes_y_orden_cronologico():
    """Comprueba que los autores citados en pasajes entren en la línea temporal,
    se ordenen cronológicamente y distingan fechas documentadas de no documentadas."""
    from docente_ai.music.didactic import (
        construir_hitos_linea_temporal,
        generar_svg_linea_temporal,
        formatear_fuente_corta,
    )

    # Simular las evidencias de Grecia de la biblioteca
    evidence = [
        {
            'source_id': 'S0',
            'metadata': {'title': 'De institutione musica', 'authors': ['Boecio']},
            'text': 'Boecio expone la división del monocordio atribuida a Pitágoras y cita a Nicómaco de Gerasa.',
        },
        {
            'source_id': 'S1',
            'metadata': {'title': 'Sobre la música', 'authors': ['Arístides Quintiliano']},
            'text': 'Platón en el Timeo y en La República describe la armonía de las esferas.',
        },
        {
            'source_id': 'S2',
            'metadata': {'title': 'Los sistemas armónicos de la Grecia Antigua', 'authors': ['Garrido Domené, Fuensanta']},
            'text': 'Claudio Ptolomeo en sus Harmónicos perfecciona la teoría de los tetracordos.',
        },
        {
            'source_id': 'S3',
            'metadata': {'title': 'La música en la edad media', 'authors': ['Reese, Gustave']},
            'text': 'San Agustín (354-430) en su tratado De musica analiza los ritmos y proporciones métricas.',
        },
    ]

    hitos = construir_hitos_linea_temporal(evidence)
    autores = [h['autor'] for h in hitos]

    # Comprobar que entran Pitágoras, Platón, Nicómaco, Ptolomeo, San Agustín y Boecio
    assert any('Pitágoras' in a for a in autores)
    assert any('Platón' in a for a in autores)
    assert any('Nicómaco' in a for a in autores)
    assert any('Ptolomeo' in a for a in autores)
    assert any('Agustín' in a for a in autores)
    assert any('Boecio' in a for a in autores)

    # Comprobar orden cronológico estricto
    anos = [h['ano_numerico'] for h in hitos]
    assert anos == sorted(anos)

    # San Agustín tiene fecha explícita (354-430) en el pasaje -> fecha_documentada True
    agustin = next(h for h in hitos if 'Agustín' in h['autor'])
    assert agustin['fecha_documentada'] is True

    # Nicómaco o Platón citados por su teoría sin fecha biográfica en el texto -> fecha_documentada False
    nicomaco = next(h for h in hitos if 'Nicómaco' in h['autor'])
    assert nicomaco['fecha_documentada'] is False

    # Comprobar formato de fuente corta sin truncar palabras
    fuente_formateada = formatear_fuente_corta('Garrido Domené, Fuensanta', 'Los sistemas armónicos de la Grecia Antigua', 28)
    assert not fuente_formateada.endswith(' ')
    assert 'Garrido Domené, Los sistemas armónicos' in fuente_formateada

    # SVG docente contiene la etiqueta de advertencia para autores sin fecha en el pasaje
    svg_doc = generar_svg_linea_temporal(hitos, para_alumnado=False)
    assert '[fecha sin fuente]' in svg_doc

    # SVG para alumnado no contiene la advertencia interna
    svg_alum = generar_svg_linea_temporal(hitos, para_alumnado=True)
    assert '[fecha sin fuente]' not in svg_alum


def test_tetracordos_glifo_vectorial_cuarto_tono():
    """Comprueba que el glifo de cuarto de tono sea un trazado vectorial y no dependa de caracteres SMuFL."""
    from docente_ai.music.didactic import generar_svg_tetracordos

    svg = generar_svg_tetracordos()
    # No debe contener el carácter Unicode que falla en PDF sin fuentes SMuFL
    assert '𝄲' not in svg
    # Debe contener el trazado vectorial del semibemol (cuarto de tono)
    assert 'stroke="#dc2626"' in svg
    assert '<path d="M 0,-2 C -4.5,-2' in svg
    # Nombre legible de la nota
    assert 'Si(¼♭)3' in svg


def test_glosario_griego_ditono_cents_y_verificacion(tmp_path):
    """Comprueba la corrección del dítono en cents y la verificación por UI."""
    from pathlib import Path
    import yaml
    from docente_ai.teaching.fichas import get_ficha, verificar_ficha, is_ficha_verified

    f_path = Path('config/fichas/glosario_griego.yaml')
    assert f_path.is_file()
    datos = yaml.safe_load(f_path.read_text(encoding='utf-8'))

    # Comprobar definición exacta del ditono
    ditono = next(c for c in datos['conceptos'] if 'Ditono' in c['termino'])
    assert '81:64 ≈ 408 cents' in ditono['definicion']
    assert 'dítono temperado son 400 cents' in ditono['definicion']

    # Ficha temporal para probar verificación
    test_ficha_file = tmp_path / 'glosario_test.yaml'
    test_ficha_file.write_text(yaml.safe_dump({
        'id': 'glosario_test',
        'tema': 'Test',
        'verificado': False,
        'conceptos': [{'termino': 'Test', 'definicion': 'Definicion test'}]
    }), encoding='utf-8')

    ficha_pre = get_ficha('glosario_test', directory=tmp_path)
    assert is_ficha_verified(ficha_pre) is False

    ficha_post = verificar_ficha('glosario_test', verificado_por='profesor_test', directory=tmp_path)
    assert ficha_post is not None
    assert ficha_post['verificado'] is True
    assert ficha_post['verificado_por'] == 'profesor_test'
    assert 'verificado_en' in ficha_post
    assert is_ficha_verified(ficha_post) is True


