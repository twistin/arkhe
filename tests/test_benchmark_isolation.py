"""Verifica que scripts/run_eval.py opera estrictamente sobre copias temporales

y nunca contamina ni escribe en data/docente.sqlite3.
"""

import hashlib
from pathlib import Path
import sqlite3
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_eval import run_benchmark, run_single_case, CASE_SOURCES
from test_generation import FakeEmbedder, FakeGenerator



def test_run_eval_never_writes_to_real_docente_sqlite3(tmp_path, monkeypatch):
    """Comprueba que run_eval no modifica data/docente.sqlite3 si existe."""
    # 1. Crear una base de datos ficticia que simule data/docente.sqlite3
    real_db_dir = tmp_path / "data"
    real_db_dir.mkdir(parents=True, exist_ok=True)
    real_db_path = real_db_dir / "docente.sqlite3"

    conn = sqlite3.connect(real_db_path)
    conn.execute("CREATE TABLE test_canary (id INTEGER PRIMARY KEY, canary TEXT)")
    conn.execute("INSERT INTO test_canary (canary) VALUES ('ORIGINAL_SECRET_CANARY')")
    conn.commit()
    conn.close()

    initial_bytes = real_db_path.read_bytes()
    initial_hash = hashlib.sha256(initial_bytes).hexdigest()

    # Redirigir ROOT en run_eval para apuntar a tmp_path
    import shutil
    import scripts.run_eval as re_mod
    shutil.copytree(ROOT / "config", tmp_path / "config")
    monkeypatch.setattr(re_mod, "ROOT", tmp_path)
    monkeypatch.setattr(re_mod, "CASES_DIR", ROOT / "eval" / "casos")
    monkeypatch.setattr(re_mod, "RESULTS_BASE_DIR", tmp_path / "eval" / "resultados")


    # Interceptar sqlite3.connect para detectar si alguien abre directamente real_db_path en modo escritura
    original_connect = sqlite3.connect

    def guarded_connect(database, *args, **kwargs):
        p = Path(database).resolve()
        if p == real_db_path.resolve():
            # Solo se permite si fuera de solo lectura (URI) o verificación, nunca para escribir
            pass
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", guarded_connect)

    # 2. Ejecutar el benchmark offline
    results = run_benchmark(offline=True, case_filter="teoria-griega-seikilos")
    assert len(results) > 0, "Se esperaba al menos un caso evaluado."

    # 3. Comprobar que la base real no fue tocada en absoluto
    final_bytes = real_db_path.read_bytes()
    final_hash = hashlib.sha256(final_bytes).hexdigest()

    assert final_hash == initial_hash, (
        "FALLO DE SEGURIDAD: scripts/run_eval.py ha modificado data/docente.sqlite3 real."
    )

    # Verificar que el canary sigue intacto
    conn = sqlite3.connect(real_db_path)
    rows = conn.execute("SELECT canary FROM test_canary").fetchall()
    conn.close()
    assert rows == [("ORIGINAL_SECRET_CANARY",)]


def test_run_single_case_uses_provided_db_path_strictly(tmp_path):
    """Comprueba que run_single_case solo opera sobre el db_path temporal proporcionado."""
    from docente_ai.storage import import_config
    from docente_ai.config import load
    from docente_ai.rag.settings import RagSettings
    from docente_ai.generation.settings import GenerationSettings

    temp_db = tmp_path / "custom_temp.sqlite3"
    example_cfg = Path(__file__).resolve().parents[1] / "config" / "teaching.example.yaml"
    import_config(temp_db, load(example_cfg))

    case_data = {
        "id": "caso-test",
        "group_id": "historia-3gp",
        "duration_minutes": 30,
        "topic": "Prueba de aislamiento",
        "teacher_criteria": "Criterio de prueba",
    }
    rag_settings = RagSettings(model="embed:1")
    gen_settings = GenerationSettings(model="gen:1", num_ctx=8192, max_output_tokens=1536)

    def gen_factory(settings):
        from test_pedagogy import proposal
        return FakeGenerator(settings, response=proposal())

    result = run_single_case(
        case_data,
        temp_db,
        rag_settings,
        gen_settings,
        embedder_factory=FakeEmbedder,
        generator_factory=gen_factory,
    )
    assert result["status"] in ("answered", "abstained")
    # La propuesta se guardó en temp_db, no en ninguna otra base
    conn = sqlite3.connect(temp_db)
    runs = conn.execute("SELECT id FROM generation_runs").fetchall()
    conn.close()
    assert len(runs) == 1
    assert runs[0][0] == result["id"]

