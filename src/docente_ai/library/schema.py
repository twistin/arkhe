"""Migración 2: biblioteca documental; aún sin índices RAG."""

MIGRATION_2 = (
    '''CREATE TABLE documents (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL CHECK(category IN ('documental','profesor')),
        metadata TEXT NOT NULL CHECK(json_valid(metadata)),
        enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)),
        shared INTEGER NOT NULL DEFAULT 0 CHECK(shared IN (0,1)),
        created_at TEXT NOT NULL,
        current_version_id TEXT REFERENCES document_versions(id)
    )''',
    '''CREATE TABLE document_versions (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL REFERENCES documents(id),
        sha256 TEXT NOT NULL,
        original_path TEXT NOT NULL,
        source_path TEXT NOT NULL,
        format TEXT NOT NULL,
        imported_at TEXT NOT NULL,
        extractor TEXT NOT NULL,
        metadata_snapshot TEXT NOT NULL CHECK(json_valid(metadata_snapshot)),
        status TEXT NOT NULL CHECK(status IN ('ready','needs_review','failed')),
        page_count INTEGER,
        warnings TEXT NOT NULL CHECK(json_valid(warnings)),
        error TEXT,
        UNIQUE(document_id, sha256)
    )''',
    '''CREATE TABLE document_segments (
        id TEXT PRIMARY KEY,
        version_id TEXT NOT NULL REFERENCES document_versions(id),
        ordinal INTEGER NOT NULL,
        text TEXT NOT NULL,
        locator TEXT NOT NULL CHECK(json_valid(locator)),
        UNIQUE(version_id, ordinal)
    )''',
    '''CREATE TABLE document_subjects (
        document_id TEXT NOT NULL REFERENCES documents(id),
        subject_id TEXT NOT NULL REFERENCES subjects(id),
        PRIMARY KEY(document_id, subject_id)
    )''',
    '''CREATE TABLE library_events (
        id INTEGER PRIMARY KEY,
        document_id TEXT NOT NULL REFERENCES documents(id),
        created_at TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT NOT NULL CHECK(json_valid(details))
    )''',
    'CREATE INDEX versions_document ON document_versions(document_id)',
    'CREATE INDEX segments_version ON document_segments(version_id, ordinal)',
)
