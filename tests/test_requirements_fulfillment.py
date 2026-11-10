"""Tests unitarios para la asignación de ejecutores y resolución de fulfillment de requisitos."""
import json
import sqlite3
from pathlib import Path
import pytest

from docente_ai.generation.settings import GenerationSettings
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


def test_extract_requirements_sin_settings_lanza_error():
    """extract_requirements sin settings debe lanzar un error explícito, nunca crear GenerationSettings('default')."""
    with pytest.raises(ValueError, match="extract_requirements requiere un objeto GenerationSettings explícito"):
        extract_requirements(
            topic="La forma sonata",
            criteria="Exposición, desarrollo y reexposición",
            settings=None,
        )


def test_fallback_asignacion_ejecutores_caso_seikilos():
    """Verifica que cada requisito del caso de Seikilos se asigna al ejecutor correcto usando fallback."""
    settings = GenerationSettings("test")
    reqs = extract_requirements(
        topic="La música en la antigua Grecia y el Epitafio de Seikilos",
        criteria=CRITERIO_SEIKILOS,
        settings=settings,
        generator_factory=None,
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


def test_fallback_r8_pendiente_profesor_sin_partitura_verificada(tmp_path):
    """Verifica que R8 queda como pendiente_profesor si no hay partitura verificada en el entorno."""
    settings = GenerationSettings("test")
    reqs = extract_requirements(
        topic="La música en la antigua Grecia y el Epitafio de Seikilos",
        criteria=CRITERIO_SEIKILOS,
        settings=settings,
        generator_factory=None,
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


def test_fulfillment_panel_rojo_en_vista_profesor():
    """Verifica el Punto 3: panel rojo en vista de profesor con botón de importar y actividades afectadas."""
    # Comprobar que documentos.js incluye renderFulfillmentAlertPanel y el panel de aviso
    docs_js = Path("src/docente_ai/web/static/js/componentes/documentos.js").read_text(encoding="utf-8")
    assert "renderFulfillmentAlertPanel" in docs_js
    assert "fulfillment-unmet-panel" in docs_js
    assert "import-musicxml-btn" in docs_js
    assert "unmet-affected-text" in docs_js


def test_omision_seccion_pendiente_y_aviso_en_actividades_alumnado():
    """Verifica el Punto 1, 3 y 4: omisión de requisitos no cumplidos y aviso en actividades."""
    mat_js = Path("src/docente_ai/web/static/js/componentes/material-alumnado.js").read_text(encoding="utf-8")
    # Requisitos no cumplidos: las actividades afectadas se marcan como pendientes
    assert "unmetReqIds" in mat_js
    assert "activity-resource-pending" in mat_js
    assert "Material que te entregará el profesor" in mat_js
    assert "limitWords" in mat_js
    assert "glossary-callout" in mat_js


def test_fallback_caso_polifonia_siglo_xvi_descomposicion_y_fulfillment():
    """Caso real run-1367d9daff4e4bcfb82e1e000c16b53e:
    La propuesta del siglo XVI debe descomponerse en al menos 8 requisitos atómicos,
    no incluir contenido de Grecia ni del siglo XV, y tener fulfillment nunca null."""
    criterios_xvi = (
        "1. Escuelas polifónicas del siglo XVI: franco-flamenca, romana, veneciana y española (Palestrina, Lassus, Victoria).\n"
        "2. Impacto de la Reforma luterana y la Contrarreforma católica (Concilio de Trento).\n"
        "3. La misa renacentista: técnicas de cantus firmus, paráfrasis y parodia.\n"
        "4. El motete renacentista como expresión sacra.\n"
        "5. Formas profanas: la chanson francesa y el madrigal italiano.\n"
        "6. La polifonía en la península ibérica y su difusión en América.\n"
        "7. Técnicas contrapuntísticas: contrapunto imitativo y policoralidad (cori spezzati).\n"
        "8. Actividad práctica de análisis auditivo comparativo de texturas del siglo XVI."
    )

    settings = GenerationSettings("test")
    reqs = extract_requirements(
        topic="La polifonía en el siglo XVI",
        criteria=criterios_xvi,
        settings=settings,
        generator_factory=None,
    )

    # 1. Al menos 8 requisitos atómicos
    assert len(reqs) >= 8

    # 2. Prohibido copiar el tema o criterios enteros como descripción de un requisito
    for r in reqs:
        assert r["description"].lower() != "la polifonía en el siglo xvi"
        assert r["description"].lower() != criterios_xvi.lower()
        # Ni un solo término ni autor griego o del siglo XV
        desc_low = r["description"].lower()
        for term_prohibido in ("pitágoras", "pitagoras", "aristóxeno", "boecio", "seikilos", "monocordio", "tetracordo", "dufay", "ockeghem"):
            assert term_prohibido not in desc_low, f"Término prohibido encontrado: {term_prohibido} en {r['id']}"

    # 3. Fulfillment resuelto nunca null
    fulfillment, recursos = resolver_fulfillment_requisitos(
        reqs,
        topic="La polifonía en el siglo XVI",
        subject="historia_de_la_musica_1",
    )
    assert fulfillment is not None
    assert len(fulfillment) == len(reqs)
    for f in fulfillment:
        assert f["estado"] in ("cumplido", "pendiente_profesor", "sin_fuentes", "descartado")

    # 4. Comprobar que no se asigne la ficha del siglo XV
    from docente_ai.teaching.fichas import get_ficha_for_topic
    ficha_xvi = get_ficha_for_topic("La polifonía en el siglo XVI")
    assert ficha_xvi is None


def test_cita_profesor_literal_y_rechazo_si_no_coincide():
    """Verifica que un requisito con cita_profesor que no existe en el texto se rechaza."""
    from docente_ai.rag.planning import _verificar_cita_profesor

    texto = "Quiero ver la forma sonata y el desarrollo temático en Haydn y Mozart."
    assert _verificar_cita_profesor("forma sonata", texto)
    assert _verificar_cita_profesor("desarrollo temático", texto)
    assert _verificar_cita_profesor("desarrollo tematico", texto)  # tolera tilde
    # Cita inventada que no está en el texto
    assert not _verificar_cita_profesor("Epitafio de Seikilos", texto)
    assert not _verificar_cita_profesor("misa cíclica", texto)


def test_fallback_a_frases_sin_plantillas_ante_fallo_llm():
    """Simula fallo completo del LLM y comprueba aviso de error y troceado por frases sin plantillas."""
    class FakeBrokenGenerator:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def generate(self, prompt, **kwargs):
            return {"content": "Esto no es un JSON válido en absoluto."}

    topic = "La síntesis FM y el diseño de sonido digital en los años 80"
    criteria = "Explicar oscilador portador y modulador; índice de modulación; espectro no armónico; DX7 de Yamaha"

    settings = GenerationSettings("test")
    reqs = extract_requirements(
        topic=topic,
        criteria=criteria,
        settings=settings,
        generator_factory=lambda _: FakeBrokenGenerator(),
    )

    # Debe marcar el error en el contenedor
    assert getattr(reqs, "error", None) == "No he podido descomponer tus indicaciones"
    # Debe tener requisitos troceados del texto
    assert len(reqs) >= 3
    # Cada uno debe tener su cita_profesor literal del texto original
    texto_completo = f"{topic} {criteria}"
    for r in reqs:
        assert r.get("cita_profesor")
        assert r["cita_profesor"].lower() in texto_completo.lower()
        # Prohibido cualquier residuo de plantillas fijas (Seikilos, etc.)
        for forbidden in ("seikilos", "monocordio", "tetracordo", "dufay", "ockeghem", "palestrina"):
            assert forbidden not in r["description"].lower()


def test_fallback_caso_xvi_texto_informal_con_erratas_del_profesor():
    """Prueba con el texto real del profesor (informal, sin espacios tras comas):
    los requisitos deben basarse en sus palabras y no inventar autores como requisitos obligatorios."""
    topic = "Quiero trabajar la polifonia Renacentista del siglo XVI: generaciones 3,4 y 5 de compositores, escuelas europeas Reforma y contrarreforma,Misa,chanson y Madrigales"
    criteria = "Priorizar formas musicales, compositores, cambios en el contexto social, politico y economico (america, Reforma, contrarreforma), tecnicas de composicion"

    settings = GenerationSettings("test")
    reqs = extract_requirements(
        topic=topic,
        criteria=criteria,
        settings=settings,
        generator_factory=None,
    )
    assert len(reqs) >= 4

    texto_total = f"{topic} {criteria}"
    for r in reqs:
        cita = r.get("cita_profesor") or ""
        assert cita, f"Requisito {r['id']} no tiene cita_profesor"
        # La cita debe estar presente en el texto
        from docente_ai.rag.planning import _verificar_cita_profesor
        assert _verificar_cita_profesor(cita, texto_total), f"Cita '{cita}' no encontrada en el texto del profesor"


def test_llm_extraccion_requisitos_con_generador_falso():
    """Prueba que extract_requirements procesa adecuadamente la salida válida de un LLM."""
    payload = {
        "requirements": [
            {
                "id": "R1",
                "description": "Línea de tiempo con los principales tratadistas griegos",
                "type": "línea temporal",
                "cita_profesor": "Línea de tiempo con los principales tratadistas y filósofos musicales griegos",
            },
            {
                "id": "R2",
                "description": "Doctrina del ethos y consonancia pitagórica",
                "type": "contenido",
                "cita_profesor": "Fundamentos teóricos: doctrina del ethos",
                "sugerencias": ["Monocordio pitagórico", "Aristóxeno de Tarento"],
            },
        ],
        "sugerencias_adicionales": ["Escala de géneros griegos"],
    }

    class FakeLLMGenerator:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def generate(self, prompt, **kwargs):
            return {"content": json.dumps(payload, ensure_ascii=False)}

    settings = GenerationSettings("test")
    reqs = extract_requirements(
        topic="La música en la antigua Grecia",
        criteria=CRITERIO_SEIKILOS,
        settings=settings,
        generator_factory=lambda _: FakeLLMGenerator(),
    )
    assert len(reqs) == 2
    assert reqs[0]["ejecutor"] == "linea_temporal"
    assert reqs[0]["cita_profesor"] == "Línea de tiempo con los principales tratadistas y filósofos musicales griegos"
    assert reqs[1]["sugerencias"] == ["Monocordio pitagórico", "Aristóxeno de Tarento"]
    assert getattr(reqs, "error", None) is None
    assert "Escala de géneros griegos" in getattr(reqs, "sugerencias", [])



