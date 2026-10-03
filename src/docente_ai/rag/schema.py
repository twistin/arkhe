"""Migración 3: perfiles, fragmentos e índices completos por versión."""

MIGRATION_3 = (
    '''CREATE TABLE embedding_profiles (
        id TEXT PRIMARY KEY,
        settings TEXT NOT NULL CHECK(json_valid(settings)),
        model TEXT NOT NULL,
        digest TEXT NOT NULL,
        dimensions INTEGER NOT NULL CHECK(dimensions>0),
        created_at TEXT NOT NULL
    )''',
    '''CREATE TABLE rag_chunks (
        id TEXT PRIMARY KEY,
        version_id TEXT NOT NULL REFERENCES document_versions(id),
        segment_id TEXT NOT NULL REFERENCES document_segments(id),
        profile_id TEXT NOT NULL REFERENCES embedding_profiles(id),
        ordinal INTEGER NOT NULL,
        text TEXT NOT NULL,
        locator TEXT NOT NULL CHECK(json_valid(locator)),
        vector BLOB NOT NULL,
        UNIQUE(version_id,profile_id,ordinal)
    )''',
    '''CREATE TABLE rag_indexes (
        version_id TEXT NOT NULL REFERENCES document_versions(id),
        profile_id TEXT NOT NULL REFERENCES embedding_profiles(id),
        chunk_count INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY(version_id,profile_id)
    )''',
    'CREATE INDEX rag_chunks_lookup ON rag_chunks(profile_id,version_id)',
)
