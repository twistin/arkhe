"""Migraciones del módulo de generación: registros documentados y revisiones del profesor."""

MIGRATION_4 = (
    '''CREATE TABLE generation_runs (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT NOT NULL CHECK(status IN ('running','draft','abstained','failed','cancelled')),
        request_json TEXT NOT NULL CHECK(json_valid(request_json)),
        prompt_version TEXT NOT NULL,
        model TEXT,
        digest TEXT,
        messages_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(messages_json)),
        evidence_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(evidence_json)),
        omitted_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(omitted_json)),
        result_json TEXT CHECK(result_json IS NULL OR json_valid(result_json)),
        metrics_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(metrics_json)),
        raw_response TEXT,
        error TEXT
    )''',
)

# Migración 5: revisión del profesor sobre borradores.
# review_json: {"action": "approved"|"rejected", "notes": str, "reviewed_at": ISO8601,
#               "approved_hash": sha256_hex_del_result_json}
# Una edición posterior del plan vuelve a poner review_json a NULL.
MIGRATION_5 = (
    'ALTER TABLE generation_runs ADD COLUMN review_json TEXT CHECK(review_json IS NULL OR json_valid(review_json))',
)
