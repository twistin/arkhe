"""Catálogo de repertorio real: selección por tema, resolución exacta y análisis calculado."""

import json

import pytest

from docente_ai.music import repertorio
from docente_ai.teaching.score_resolver import resolver_peticion_musical


def test_indice_incluido_y_con_metadatos_de_archivo():
    entradas = repertorio.cargar_indice()
    assert len(entradas) > 1000
    obras = repertorio.obras_del_indice()
    papa = obras['palestrina:missa-papae-marcelli']
    assert papa['compositor'] == 'Giovanni Pierluigi da Palestrina'
    assert papa['movimientos'][0] == 'Kyrie'
    assert all(e['id'].startswith('rep:') for e in entradas)


def test_seleccion_solo_con_compositores_mencionados():
    xvi = repertorio.seleccionar_repertorio('Polifonía del siglo XVI: misa y madrigal',
                                           'Josquin, Palestrina y la Missa Papae Marcelli', limite=12)
    ids = [o['id'] for o in xvi]
    assert ids[0] == 'palestrina:missa-papae-marcelli'      # título citado en los pasajes, primero
    assert any(i.startswith('josquin:') for i in ids)       # reparto entre compositores
    assert not any(i.startswith(('vitry:', 'landini:', 'ciconia:')) for i in ids)
    assert repertorio.seleccionar_repertorio('Teoría musical griega', 'Pitágoras y Aristóxeno') == []


def test_resolucion_por_catalog_id_toma_los_datos_del_archivo():
    res = resolver_peticion_musical({
        'id': 'MR1', 'composer': 'Otro autor', 'work': 'Título inventado', 'section': 'Gloria',
        'catalog_id': 'palestrina:missa-papae-marcelli', 'description': 'Observa los bloques.'})
    assert res['status'] == 'resuelto_repertorio'
    ej = res['ejemplo']
    assert ej['compositor'] == 'Giovanni Pierluigi da Palestrina'
    assert ej['obra'] == 'Missa Papae Marcelli' and ej['seccion'] == 'Gloria'
    assert ej['analisis']['entradas'] and ej['edicion_reconocida'] is True
    falsa = resolver_peticion_musical({'id': 'MR2', 'composer': 'Palestrina', 'work': 'Missa inventada',
                                       'section': 'Kyrie', 'catalog_id': 'palestrina:missa-inventada',
                                       'description': 'x'})
    assert falsa['status'] == 'sin_resolver'


def test_fragmento_incluye_la_voz_que_entra_tarde():
    res = resolver_peticion_musical({'id': 'MR1', 'composer': 'x', 'work': 'x', 'section': 'Kyrie',
                                     'catalog_id': 'palestrina:missa-l-homme-arme-1570', 'description': ''})
    inicio, fin = (int(n) for n in res['ejemplo']['compases'].split('-'))
    ultima = max(e['compas'] for e in res['ejemplo']['analisis']['entradas'])
    assert inicio == 1 and fin >= ultima


@pytest.mark.parametrize('rep_id', ['rep:../../etc/passwd', 'rep:palestrina/no-existe.krn', 'palestrina/Kyrie_103.krn'])
def test_ruta_archivo_rechaza_identificadores_fuera_del_indice(rep_id):
    assert repertorio.ruta_archivo(rep_id) is None


def test_analisis_distingue_homorritmia_e_imitacion():
    chanson = repertorio.resolver_obra('josquin:mille-regrets')
    a = repertorio.analizar_fragmento(repertorio.ruta_archivo(chanson['id']), 1, 8, chanson['nombres_voces'])
    assert a['porcentaje_ataques_simultaneos'] >= 70 and 'homorrítmica' in a['textura_calculada']
    kyrie = repertorio.resolver_obra('palestrina:missa-papae-marcelli', 'Kyrie')
    b = repertorio.analizar_fragmento(repertorio.ruta_archivo(kyrie['id']), 1, 8, kyrie['nombres_voces'])
    assert b['entradas_escalonadas'] and b['porcentaje_ataques_simultaneos'] < a['porcentaje_ataques_simultaneos']


def test_colecciones_con_ocr_defectuoso_fuera_del_catalogo():
    assert not any(e['archivo_corpus'].startswith('monteverdi/') for e in repertorio.cargar_indice())


def test_validacion_de_secciones_y_peticiones_de_catalogo():
    from docente_ai.agents.pedagogy import RESPONSE_SCHEMA, SYSTEM
    props = RESPONSE_SCHEMA['properties']['claims']['items']['properties']
    assert {'title', 'key_points', 'example_ids'} <= set(props)
    assert 'catalog_id' in RESPONSE_SCHEMA['properties']['music_requests']['items']['properties']
    assert 'repertorio_disponible' in SYSTEM
    json.dumps(RESPONSE_SCHEMA)
