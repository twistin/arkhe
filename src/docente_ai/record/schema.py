"""Migración 6: registro de impartición real, progreso por unidad y feedback del profesor."""

MIGRATION_6 = (
    # Registro de lo que se impartió de verdad en una sesión.
    # Un plan aprobado no prueba que se haya impartido; esto sí lo hace.
    '''CREATE TABLE session_records (
        id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        session_date TEXT NOT NULL CHECK(session_date GLOB '????-??-??'),
        duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0 AND duration_minutes <= 480),
        run_id TEXT REFERENCES generation_runs(id),
        topic TEXT NOT NULL CHECK(length(trim(topic)) > 0),
        objectives_met TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(objectives_met)),
        activities_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(activities_json)),
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL
    )''',
    # Progreso confirmado por unidad de programación (relación N-N con session_records).
    '''CREATE TABLE session_unit_progress (
        id TEXT PRIMARY KEY,
        session_record_id TEXT NOT NULL REFERENCES session_records(id),
        group_id TEXT NOT NULL,
        unit_id TEXT NOT NULL,
        progress_note TEXT NOT NULL DEFAULT '',
        UNIQUE(session_record_id, unit_id)
    )''',
    # Feedback del profesor sobre la sesión: qué funcionó, qué falló, notas para la siguiente.
    # Siempre es interpretación del profesor; no evidencia bibliográfica.
    '''CREATE TABLE session_feedback (
        id TEXT PRIMARY KEY,
        session_record_id TEXT NOT NULL UNIQUE REFERENCES session_records(id),
        what_worked TEXT NOT NULL DEFAULT '',
        what_failed TEXT NOT NULL DEFAULT '',
        next_session_note TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL
    )''',
)
