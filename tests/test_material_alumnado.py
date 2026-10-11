"""Pruebas de limpieza y verificación del material del alumnado y fichas pedagógicas."""

from pathlib import Path
import re
import pytest

from docente_ai.generation.render import render_pedagogy, render_student
from docente_ai.teaching.fichas import (
    get_ficha,
    get_ficha_for_run,
    get_ficha_for_topic,
    is_ficha_verified,
    load_all_fichas,
)


def _make_dummy_polyphony_run(extra_claims=None, extra_evidence=None, extra_activities=None):
    evidence = extra_evidence or [
        {
            'source_id': 'S1',
            'document_id': 'doc_atlas',
            'metadata': {'authors': ['Allan W. Atlas'], 'title': 'La música del Renacimiento', 'year': 2002},
            'locator': {'kind': 'pdf_page', 'pdf_page_index': 124},
            'passages': [{'text': 'El cantus firmus permaneció como eje estructural.'}],
        },
        {
            'source_id': 'S2',
            'document_id': 'doc_atlas_anthology',
            'metadata': {'authors': ['Allan W. Atlas'], 'title': 'Antología de la música del Renacimiento', 'year': 2002},
            'locator': {'kind': 'pdf_page', 'pdf_page_index': 45},
            'passages': [{'text': 'Ejemplos de cantus firmus en el tenor.'}],
        },
        {
            'source_id': 'S3',
            'document_id': 'doc_reese',
            'metadata': {'authors': ['Gustave Reese'], 'title': 'La música en el Renacimiento', 'year': 1988},
            'locator': {'kind': 'pdf_page', 'pdf_page_index': 88},
            'passages': [{'text': 'Ockeghem evita la articulación de frases.'}],
        },
    ]

    claims = extra_claims or [
        {
            'id': 1,
            'text': 'El cantus firmus vertebra la misa cíclica (S1, S2).',
            'student_summary': 'El cantus firmus sirve como eje de la misa cíclica. Según pasajes de S1.',
            'evidence': [{'source_id': 'S1', 'quote': 'El cantus firmus permaneció como eje estructural.'}],
        },
        {
            'id': 2,
            'text': 'Ockeghem emplea flujo continuo y asimetría.',
            'student_summary': 'Ockeghem evita las cesuras cadenciales simultáneas.',
            'evidence': [{'source_id': 'S3', 'quote': 'Ockeghem evita la articulación de frases.'}],
        },
    ]

    activities = extra_activities or [
        {
            'title': 'Análisis de cantus firmus',
            'minutes': 20,
            'grouping': 'individual',
            'instructions': 'Analiza los pasajes de S1 y subraya el tenor (S1, S2).',
            'student_task': 'Sigue la partitura y analiza los pasajes de S1.',
            'deliverable': 'Cuadro comparativo con Fuente: S1.',
        },
        {
            'title': 'Debate sobre técnicas de misa',
            'minutes': 40,
            'grouping': 'grupo',
            'instructions': 'Compara cantus firmus y paráfrasis.',
            'student_task': 'Debate en grupos sobre las técnicas de misa cíclica.',
            'deliverable': 'Resumen conjunto.',
        },
    ]

    return {
        'id': 'run_polyphony_test',
        'display_title': 'Polifonía del siglo XV',
        'original_topic': 'polifonia del siglo xv',
        'request': {
            'question': 'Polifonía del siglo XV',
            'pedagogy': {
                'group': {'name': 'Historia de la Música I', 'level': '3º Grado Profesional'},
                'duration_minutes': 60,
                'teacher_criteria': 'Analizar modelos de misa y técnicas del siglo XV.',
            },
        },
        'result': {
            'plan': {
                'objectives': ['Comprender la misa cíclica.', 'Identificar el cantus firmus.'],
                'activities': activities,
                'resources': [
                    {'recurso': 'Partitura del Kyrie', 'tipo': 'partitura', 'pendiente': True},
                    {'recurso': 'Missa L\'homme armé', 'tipo': 'grabacion', 'pendiente': True},
                    {'recurso': '1475 (fecha del manuscrito)', 'tipo': 'dato', 'pendiente': True},
                    'Grabación de audio de referencia.',
                ],
            },
            'claims': claims,
            'visualizations': [
                {
                    'title': 'Modelos de textura',
                    'items': [
                        {'label': 'Cantus firmus', 'detail': 'Tenor en valores largos'},
                        {'label': 'Contrapunto libre', 'detail': 'Voces superiores en imitación'},
                    ],
                }
            ],
        },
        'evidence': evidence,
    }


def test_fichas_cargadas_correctamente_y_verificado_false():
    """Comprueba que las fichas de polifonía, egipto y ntam se cargan con verificado: false."""
    fichas = load_all_fichas()
    ids = {f.get('id') for f in fichas}
    assert 'polifonia_xv' in ids
    assert 'egipto' in ids
    assert 'ntam' in ids

    f_poly = get_ficha('polifonia_xv')
    assert f_poly is not None
    assert f_poly.get('verificado') is False
    assert is_ficha_verified(f_poly) is False

    f_egypt = get_ficha('egipto')
    assert f_egypt is not None
    assert f_egypt.get('verificado') is False

    f_ntam = get_ficha('ntam')
    assert f_ntam is not None
    assert f_ntam.get('verificado') is False


def test_puntos_dudosos_marcados_para_revision_sin_alterar_contenido():
    """Comprueba la revisión docente de la ficha: contiene revisado_con y lista cotejar del profesor."""
    f_poly = get_ficha('polifonia_xv')
    assert f_poly is not None
    assert f_poly.get('revisado_con') is not None
    assert '11-10-2026' in f_poly['revisado_con']

    cotejar = f_poly.get('cotejar', [])
    assert len(cotejar) >= 4
    assert any('Fors seulement' in c for c in cotejar)
    assert any('Du Fay' in c or 'canto llano' in c for c in cotejar)
    assert any('cadencias' in c.lower() for c in cotejar)
    assert any('Tarea' in c for c in cotejar)


def test_ficha_no_verificada_aparece_en_guia_docente_con_aviso_y_marcas():
    """Comprueba que una ficha no verificada se muestra en la guía docente con 'Contenido de plantilla pendiente de revisión'."""
    run = _make_dummy_polyphony_run()
    pedagogy_md = render_pedagogy(run)

    assert 'Contenido de plantilla pendiente de revisión' in pedagogy_md
    assert 'verificado: false' in pedagogy_md
    # Las notas de revisión deben estar visibles para el profesor
    assert 'Pendiente de revisión del profesor' in pedagogy_md
    assert 'Se la face ay pale' in pedagogy_md


def test_ficha_no_verificada_nunca_aparece_en_material_alumnado():
    """Comprueba el punto 1 y 3: ningún bloque de plantilla no verificado aparece en el material del alumnado."""
    run = _make_dummy_polyphony_run()
    student_md = render_student(run)

    assert 'Contenido de plantilla pendiente de revisión' not in student_md
    assert 'verificado: false' not in student_md
    assert 'data/ejemplos' not in student_md
    assert '[Pendiente de revisión' not in student_md
    assert '⚠️' not in student_md
    assert 'Je ne vis oncques la' not in student_md
    assert 'melodías del propio Kyrie' not in student_md


def test_eliminacion_identificadores_fuente_internos_en_material_alumnado():
    """Comprueba el punto 2: elimina o sustituye 'Fuente: S12', 'pasajes de S9', '(S8, S10)'."""
    run = _make_dummy_polyphony_run()
    student_md = render_student(run)

    assert 'Fuente: S1' not in student_md
    assert 'Fuente: S2' not in student_md
    assert '(S1, S2)' not in student_md
    assert 'pasajes de S1' not in student_md
    # Tampoco deben quedar identificadores sueltos en consignas
    assert 'S1' not in student_md.split('## Trabajo en clase')[1].split('## Material necesario')[0]


def test_recursos_estructurados_pendientes_redaccion_segun_tipo_y_omision_de_dato():
    """Comprueba que los recursos pendientes se estructuran por tipo:
    - grabacion: 'grabación que escucharemos en clase'
    - partitura: 'partitura que te entregará el profesor'
    - dato: nunca aparece en material del alumnado, solo en la guía docente
    - se elimina la sustitución indiscriminada por expresiones regulares."""
    run = _make_dummy_polyphony_run()
    student_md = render_student(run)
    pedagogy_md = render_pedagogy(run)

    # 1. Grabación pendiente en material del alumno
    assert "Missa L'homme armé (grabación que escucharemos en clase)" in student_md

    # 2. Partitura pendiente en material del alumno
    assert "Partitura del Kyrie (partitura que te entregará el profesor)" in student_md

    # 3. Dato pendiente (fecha, cifra) NUNCA aparece en material del alumno
    assert "1475" not in student_md
    assert "fecha del manuscrito" not in student_md

    # 4. Dato pendiente y grabación pendiente aparecen en la guía docente
    assert "1475 (fecha del manuscrito) (dato) [Aportación del profesor pendiente]" in pedagogy_md
    assert "Missa L'homme armé (grabacion) [Aportación del profesor pendiente]" in pedagogy_md
    assert "Partitura del Kyrie (partitura) [Aportación del profesor pendiente]" in pedagogy_md

    # 5. Sin sustitución por regex de texto libre de 'pendiente de aportar por el profesor'
    from docente_ai.generation.render import clean_student_text
    raw_texto = "Texto con pendiente de aportar por el profesor"
    assert clean_student_text(raw_texto) == raw_texto


def test_bibliografia_dinamica_y_sin_duplicados_de_autor():
    """Comprueba el punto 5: la bibliografía se genera solo con fuentes citadas, sin Ulrich Michels ni duplicados de Atlas."""
    run = _make_dummy_polyphony_run()
    student_md = render_student(run)

    # 1. Cabecera dinámica en sección 01
    assert 'Allan W. Atlas y Gustave Reese' in student_md
    assert 'Ulrich Michels' not in student_md

    # 2. Fuentes de consulta
    fuentes_sec = student_md.split('## Fuentes de consulta')[1]
    assert 'Ulrich Michels' not in fuentes_sec
    assert 'Manuscrito Chigi' not in fuentes_sec
    assert 'Gustave Reese' in fuentes_sec
    # Allan W. Atlas aparece como autor, pero no duplicado dos veces en las fuentes
    lineas_fuentes = [l for l in fuentes_sec.splitlines() if l.startswith('- ')]
    autores_en_fuentes = [l for l in lineas_fuentes if 'Allan W. Atlas' in l]
    assert len(autores_en_fuentes) == 1, f"Atlas está duplicado: {autores_en_fuentes}"


def test_unificacion_lista_tareas_y_sin_seccion_audiciones_duplicada():
    """Comprueba el punto 6: solo una lista de tareas de aula y sin sección 06 duplicada de discografía."""
    run = _make_dummy_polyphony_run()
    student_md = render_student(run)

    # Solo hay una sección de tareas de trabajo
    assert student_md.count('## Trabajo en clase') == 1
    # No hay sección 06 de discografía duplicada
    assert '06 · Discografía recomendada y enlaces directos de audición para el aula' not in student_md
    # Las audiciones comentadas aparecen una sola vez en 04
    assert student_md.count('## 04 · Relación de audiciones comentadas') == 1


def test_prioridad_fichas_data_gana_sobre_config(tmp_path, monkeypatch):
    """Comprueba que si existe la misma ficha en data/ y config/, data/ tiene prioridad."""
    data_dir = tmp_path / 'data/fichas'
    config_dir = tmp_path / 'config/fichas'
    data_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)

    (config_dir / 'test_ficha.yaml').write_text(
        'id: test_ficha\ntitulo: Version Config\nverificado: true\n',
        encoding='utf-8',
    )
    (data_dir / 'test_ficha.yaml').write_text(
        'id: test_ficha\ntitulo: Version Data Local\nverificado: false\nrevisado_con: profesor\n',
        encoding='utf-8',
    )

    monkeypatch.setattr('docente_ai.teaching.fichas.FICHAS_DEFAULT_DIR', data_dir)
    monkeypatch.setattr('docente_ai.teaching.fichas.FICHAS_CONFIG_DIR', config_dir)

    from docente_ai.teaching.fichas import get_ficha, load_all_fichas

    fichas = load_all_fichas()
    ficha = get_ficha('test_ficha')

    assert ficha is not None
    assert ficha.get('titulo') == 'Version Data Local'
    assert ficha.get('verificado') is False
    assert ficha.get('revisado_con') == 'profesor'

