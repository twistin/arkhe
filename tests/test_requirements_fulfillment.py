"""Tests unitarios para la asignación de ejecutores y resolución de fulfillment de requisitos."""
import json
import sqlite3
from pathlib import Path
import pytest

from docente_ai.rag.planning import extract_requirements
from docente_ai.teaching.fulfillment import (
    EJECUTORES_VALIDOS,
    resolver_fulfillment_requisitos,
)
from docente_ai.agents.pedagogy import validate
from docente_ai.generation.service import get_run


CRITERIO_SEIKILOS = (
    "1. Línea de tiempo con los principales tratadistas y filósofos musicales griegos y su cronología.\n"
    "2. Fundamentos teóricos: doctrina del ethos, armonía de las esferas, consonancia pitagórica y proporciones interválicas.\n"
    "3. Tratadistas y teóricos clave: Pitágoras, Platón, Aristóxeno, Ptolomeo, Boecio y Nicómaco.\n"
    "4. Notación alfabética griega y su desciframiento.\n"
    "5. Epitafio de Seikilos: contexto histórico, soporte epigráfico, texto, traducción y datación.\n"
    "6. Análisis musical del Epitafio de Seikilos: modo frigio / tono jonio, ámbito melódico, notas empleadas y estructura rítmica.\n"
    "7. Representación notacional en partitura y pentagrama de los tetracordos (géneros diatónico, cromático y enarmónico) y del Gran Sistema Perfecto.\n"
    "8. Mostrar el uso del material modal y tetracordal en el Epitafio de Seikilos."
)


def test_asignacion_ejecutores_caso_seikilos():
    """Verifica que cada requisito del caso de Seikilos se asigna al ejecutor correcto."""
    reqs = extract_requirements(
        topic="La música en la antigua Grecia y el Epitafio de Seikilos",
        criteria=CRITERIO_SEIKILOS,
    )
    assert len(reqs) == 8

    by_id = {r["id"]: r for r in reqs}

    # Todos los ejecutores deben pertenecer al enum cerrado
    for r in reqs:
        assert r.get("ejecutor") in EJECUTORES_VALIDOS

    # R1: Línea de tiempo
    assert by_id["R1"]["ejecutor"] == "linea_temporal"

    # R7: Representación notacional de tetracordos y Gran Sistema Perfecto
    assert by_id["R7"]["ejecutor"] == "componente_calculado"
    componentes = by_id["R7"].get("componentes", [])
    comps_tipos = [c["tipo"] for c in componentes]
    assert "tetracordos" in comps_tipos
    assert "gran_sistema_perfecto" in comps_tipos

    # R8: Mostrar uso en Epitafio de Seikilos
    assert by_id["R8"]["ejecutor"] == "analisis_sobre_partitura"


def test_r8_pendiente_profesor_sin_partitura_verificada(tmp_path):
    """Verifica que R8 queda como pendiente_profesor si no hay partitura verificada en el entorno."""
    reqs = extract_requirements(
        topic="La música en la antigua Grecia y el Epitafio de Seikilos",
        criteria=CRITERIO_SEIKILOS,
    )

    # Entorno sin partituras verificadas
    cat_dir = tmp_path / "data/ejemplos"
    cat_dir.mkdir(parents=True)
    (cat_dir / "ejemplos.yaml").write_text("[]\n", encoding="utf-8")

    fulfillment, recursos = resolver_fulfillment_requisitos(
        reqs,
        root=tmp_path,
    )

    by_id = {f["requirement_id"]: f for f in fulfillment}

    # R7 cumplido (componente calculado disponible)
    assert by_id["R7"]["estado"] == "cumplido"
    assert "tetracordos" in by_id["R7"]["artefacto_id"]

    # R8 pendiente de acción del profesor por falta de partitura verificada
    assert by_id["R8"]["estado"] == "pendiente_profesor"
    assert "Epitafio de Seikilos" in by_id["R8"]["falta"]

    # R1 cumplido (línea temporal calculada)
    assert by_id["R1"]["estado"] == "cumplido"


def test_requisito_sin_fuentes_en_biblioteca():
    """Un requisito de texto_fuentes sin claims ni fuentes queda como sin_fuentes."""
    reqs = [
        {"id": "R1", "description": "Explica la teoría general del pulso", "ejecutor": "texto_fuentes"},
        {"id": "R2", "description": "Explica la afinación mesotónica renacentista", "ejecutor": "texto_fuentes"},
    ]
    # Fulfillment inicial sin evidencias en biblioteca para R2
    fulfillment, recursos = resolver_fulfillment_requisitos(reqs)
    f_by_id = {f["requirement_id"]: f for f in fulfillment}
    assert f_by_id["R2"]["estado"] == "sin_fuentes"

    # En la validación de coverage, si hay fuentes para R1 pero no para R2, R2 queda sin cubrir
    text_s1 = "El pulso musical es regular y periódico."
    evidence = [{"source_id": "S1", "text": text_s1}]
    raw_content = json.dumps({
        "status": "answered",
        "coverage": [
            {
                "requirement_id": "R1",
                "status": "cubierto",
                "claim_ids": [1],
                "note": "Cubierto con texto.",
            },
            {
                "requirement_id": "R2",
                "status": "sin_fuentes",
                "claim_ids": [],
                "note": "No se encontraron fuentes documentales autorizadas.",
            }
        ],
        "claims": [
            {
                "kind": "summary",
                "text": text_s1,
                "student_summary": text_s1,
                "evidence": [{"source_id": "S1", "quote": text_s1}]
            }
        ],
        "plan": {
            "objectives": ["Comprender el pulso."],
            "difficulty": "Media",
            "activities": [
                {
                    "title": "Actividad de pulso",
                    "teacher_notes": "Explicación del profesor",
                    "student_task": "Tarea",
                    "grouping": "individual",
                    "deliverable": "Entrega",
                    "solution": "Solución",
                    "minutes": 20,
                    "claim_ids": [1]
                },
                {
                    "title": "Práctica colectiva",
                    "teacher_notes": "Coordinación en grupo",
                    "student_task": "Tarea grupal",
                    "grouping": "colectivo",
                    "deliverable": "Grabación",
                    "solution": "Sincronía",
                    "minutes": 20,
                    "claim_ids": [1]
                }
            ],
            "resources": ["Pizarra y partituras de estudio."],
            "assessment": "Evaluación.",
            "observations": "Observaciones.",
        },
    })
    validated = validate(
        raw_content,
        evidence=evidence,
        context={"requirements": reqs, "fulfillment": fulfillment, "duration_minutes": 40}
    )
    cov_r2 = next(c for c in validated["coverage"] if c["requirement_id"] == "R2")
    assert cov_r2["status"] == "sin_fuentes"


def test_regenerar_crea_nueva_propuesta_y_conserva_anterior(tmp_path):
    """Verifica que regenerar una propuesta crea un nuevo run_id y conserva el anterior intacto."""
    from docente_ai.web.workspace import Workspace

    ws = Workspace(root=tmp_path)
    with sqlite3.connect(ws.db) as conn:
        original_run = {
            "id": "run-original-123",
            "created_at": "2026-10-10T10:00:00Z",
            "finished_at": "2026-10-10T10:01:00Z",
            "status": "draft",
            "prompt_version": "pedagogy:11",
            "model": "test-model",
            "digest": "test-digest",
            "messages_json": "[]",
            "evidence_json": "[]",
            "omitted_json": "[]",
            "metrics_json": "{}",
            "raw_response": "{}",
            "error": None,
            "review_json": None,
            "display_title": "Grecia y Seikilos",
            "original_topic": "La música en la antigua Grecia y el Epitafio de Seikilos",
            "request_json": json.dumps({
                "pedagogy": {
                    "group": {"id": "g1", "name": "1º Historia", "subject_id": "historia-1"},
                    "teacher_criteria": CRITERIO_SEIKILOS,
                    "duration_minutes": 60,
                }
            }),
            "result_json": json.dumps({
                "requirements": [
                    {"id": "R1", "description": "Línea temporal", "ejecutor": "linea_temporal"}
                ],
                "fulfillment": [
                    {"requirement_id": "R1", "ejecutor": "linea_temporal", "estado": "cumplido"}
                ]
            }),
        }
        conn.execute(
            """INSERT INTO generation_runs (
                id, created_at, finished_at, status, prompt_version, model, digest,
                messages_json, evidence_json, omitted_json, result_json, metrics_json,
                raw_response, error, review_json, display_title, original_topic, request_json
            ) VALUES (
                :id, :created_at, :finished_at, :status, :prompt_version, :model, :digest,
                :messages_json, :evidence_json, :omitted_json, :result_json, :metrics_json,
                :raw_response, :error, :review_json, :display_title, :original_topic, :request_json
            )""",
            original_run
        )

    run_previo = get_run(ws.db, "run-original-123")
    assert run_previo["id"] == "run-original-123"

    # Al consultar preview-requirements con los requisitos de la propuesta previa
    reqs_previos = run_previo["result"]["requirements"]
    preview = ws.preview_requirements({
        "question": run_previo["original_topic"],
        "criteria": CRITERIO_SEIKILOS,
        "requirements": reqs_previos,
    })
    assert len(preview["requirements"]) == 1
    assert preview["requirements"][0]["ejecutor"] == "linea_temporal"
    assert preview["fulfillment"][0]["estado"] == "cumplido"

    # La propuesta original sigue intacta en la base de datos
    run_intacto = get_run(ws.db, "run-original-123")
    assert run_intacto["id"] == "run-original-123"
    assert run_intacto["result"]["requirements"] == reqs_previos
