"""Tests de calibración del revisor pedagógico con casos históricos de referencia."""

import json
from pathlib import Path
import sqlite3

import pytest

from docente_ai.agents.reviewer import (
    evaluate_deterministic_fallback,
    build_reviewer_prompt,
    validate_review,
)


def test_reviewer_calibration_main_run_0183ad98bdf0():
    """El run histórico de main run-0183ad98bdf04cd6b53d9667a8974958 (Grecia, 6 de octubre)

    mezcla instrucciones dirigidas al profesor en el cuaderno del alumno y plantea tareas
    donde el docente es el que ejecuta la acción ("Reproducir...", "Explicar...", "Proyectar...").
    El revisor debe calificar con <= 1 en separacion_roles y en actividades_activas.
    """
    db_path = Path("data/docente.sqlite3")
    if not db_path.exists():
        pytest.skip("data/docente.sqlite3 no disponible para test de calibración")

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "select id, request_json, result_json, evidence_json from generation_runs where id = 'run-0183ad98bdf04cd6b53d9667a8974958'"
    )
    row = cur.fetchone()
    con.close()

    if not row:
        pytest.skip("Run histórico run-0183ad98bdf04cd6b53d9667a8974958 no encontrado en la base de datos local")

    _run_id, request_json, result_json, evidence_json = row
    req = json.loads(request_json) if request_json else {}
    res = json.loads(result_json) if result_json else {}
    evidence = json.loads(evidence_json) if evidence_json else []

    context = {
        'group': {'name': 'Historia 4', 'level': '4º GP'},
        'duration_minutes': 60,
        'teacher_criteria': 'Creame un tema con lknea de tiempo desde pitagoras a san agustin...',
        'topic': 'Teoria musical, pensamiento , epitafio de srikilos y notaciones'
    }
    requirements = []

    # 1. Comprobar que build_reviewer_prompt incluye el material del alumno renderizado
    messages = build_reviewer_prompt(res, requirements, evidence, context, context['topic'])
    assert len(messages) == 2
    user_payload = json.loads(messages[1]['content'])
    assert 'student_material_markdown' in user_payload
    student_md = user_payload['student_material_markdown']
    assert len(student_md) > 100
    # Verificar que el texto renderizado efectivamente contiene las fugas docentes
    assert 'Apertura metodológica' in student_md or 'Explicar' in student_md or 'Proyectar' in student_md

    # 2. Comprobar evaluación determinista
    evaluation = evaluate_deterministic_fallback(res, requirements, evidence, context)
    scores = evaluation.get('scores', {})

    # Requisito estricto de calibración:
    # separacion_roles <= 1
    # actividades_activas <= 1
    assert scores.get('separacion_roles') is not None
    assert scores.get('separacion_roles') <= 1, (
        f"Calibración fallida: separacion_roles={scores.get('separacion_roles')}, se esperaba <= 1 "
        f"debido a fugas docentes en el material del alumno: {evaluation.get('justifications', {}).get('separacion_roles')}"
    )

    assert scores.get('actividades_activas') is not None
    assert scores.get('actividades_activas') <= 1, (
        f"Calibración fallida: actividades_activas={scores.get('actividades_activas')}, se esperaba <= 1 "
        f"debido a tareas donde el profesor es el agente: {evaluation.get('justifications', {}).get('actividades_activas')}"
    )

    # 3. Validar que justifications contiene justificaciones con texto concreto
    justifications = evaluation.get('justifications', {})
    assert 'separacion_roles' in justifications
    assert 'actividades_activas' in justifications
    assert len(justifications['separacion_roles']) > 10
    assert len(justifications['actividades_activas']) > 10


def test_validate_review_with_justifications():
    """Valida que validate_review acepte el esquema estructurado con justifications."""
    review_raw = json.dumps({
        "scores": {
            "cobertura": 2,
            "rigor_factual": 2,
            "separacion_roles": 1,
            "actividades_activas": 1,
            "adecuacion_nivel": 3,
            "temporizacion": 3
        },
        "justifications": {
            "cobertura": 'Cobertura parcial con "sin_fuentes".',
            "rigor_factual": 'Hechos fundamentados.',
            "separacion_roles": 'Filtraciones como "el alumnado".',
            "actividades_activas": 'Faltan agrupaciones explícitas.',
            "adecuacion_nivel": 'Nivel 4º GP adecuado.',
            "temporizacion": 'Suma 60 minutos.'
        },
        "issues": [
            {
                "field": "student_material",
                "issue": "Uso de tercera persona",
                "proposal": "Cambiar a 2ª persona"
            }
        ],
        "summary": "Evaluación con observaciones menores."
    })
    validated = validate_review(review_raw)
    assert validated["scores"]["separacion_roles"] == 1
    assert "justifications" in validated
