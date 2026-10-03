"""Persistencia transaccional de la configuración docente de fase 2."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from docente_ai.config import RELATIONS, SCHEMAS, validate

SCHEMA_VERSION = 7



class StorageError(ValueError):
    pass


def canonical(data: dict) -> str:
    ordered = {**data, **{table: sorted(data[table], key=lambda row: row['id']) for table in SCHEMAS}}
    return json.dumps(ordered, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    if readonly:
        if not path.is_file():
            raise StorageError('No hay base docente. Ejecuta config import primero.')
        connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
    connection.execute('PRAGMA foreign_keys = ON')
    connection.execute('PRAGMA busy_timeout = 5000')
    return connection


def migrate(connection: sqlite3.Connection) -> None:
    version = connection.execute('PRAGMA user_version').fetchone()[0]
    if version > SCHEMA_VERSION:
        raise StorageError('La base utiliza una versión más reciente que esta aplicación.')
    if version == 0:
        if connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
            raise StorageError('Base desconocida sin versión; no se modificará.')
        # Migración 1: tablas con claves foráneas explícitas. Los campos docentes
        # de cada registro se conservan en un objeto JSON validado y versionado.
        connection.execute('CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        connection.execute('CREATE TABLE config_imports (id INTEGER PRIMARY KEY, imported_at TEXT NOT NULL, sha256 TEXT NOT NULL, snapshot TEXT NOT NULL)')
        for table in SCHEMAS:
            refs = ''.join(f', {key} TEXT NOT NULL REFERENCES {target}(id)' for key, target in RELATIONS.get(table, {}).items())
            connection.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY, position INTEGER NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)){refs})')
        connection.execute('PRAGMA user_version = 1')
        version = 1
    if version == 1:
        from docente_ai.library.schema import MIGRATION_2
        for statement in MIGRATION_2:
            connection.execute(statement)
        connection.execute('PRAGMA user_version = 2')
        version = 2
    if version == 2:
        from docente_ai.rag.schema import MIGRATION_3
        for statement in MIGRATION_3:
            connection.execute(statement)
        connection.execute('PRAGMA user_version = 3')
        version = 3
    if version == 3:
        from docente_ai.generation.schema import MIGRATION_4
        for statement in MIGRATION_4:
            connection.execute(statement)
        connection.execute('PRAGMA user_version = 4')
        version = 4
    if version == 4:
        from docente_ai.generation.schema import MIGRATION_5
        for statement in MIGRATION_5:
            connection.execute(statement)
        connection.execute('PRAGMA user_version = 5')
        version = 5
    if version == 5 and SCHEMA_VERSION >= 6:
        from docente_ai.record.schema import MIGRATION_6
        for statement in MIGRATION_6:
            connection.execute(statement)
        connection.execute('PRAGMA user_version = 6')
        version = 6
    if version == 6 and SCHEMA_VERSION >= 7:
        # Las credenciales pertenecen al Llavero o al entorno, nunca al
        # historial auditable de una consulta.
        connection.execute('''UPDATE generation_runs
            SET request_json=json_set(
                json_remove(request_json, '$.generation.api_key'),
                '$.generation.api_key_configured',
                CASE WHEN coalesce(json_extract(request_json, '$.generation.api_key'), '') <> ''
                     THEN json('true') ELSE json('false') END)
            WHERE json_type(request_json, '$.generation.api_key') IS NOT NULL''')
        connection.execute('PRAGMA user_version = 7')
        # UPDATE abre una transacción implícita; los servicios comienzan la
        # suya justo después de migrate().
        connection.commit()


def import_config(path: Path, raw: dict, *, replace: bool = False) -> dict:
    data = validate(raw)  # Validar antes de crear directorios o abrir SQLite.
    snapshot = canonical(data)
    digest = hashlib.sha256(snapshot.encode()).hexdigest()
    with closing(connect(path)) as connection, connection:
        migrate(connection)
        connection.execute('BEGIN IMMEDIATE')
        last = connection.execute('SELECT sha256 FROM config_imports ORDER BY id DESC LIMIT 1').fetchone()
        if last and last[0] == digest:
            return {'changed': False, 'sha256': digest, 'message': 'Configuración idéntica; no se ha duplicado.'}
        if last and not replace:
            raise StorageError('Ya existe una configuración diferente. Usa config export para revisarla y config import --replace para sustituirla; se conservará una instantánea local.')
        for table in SCHEMAS:
            refs = list(RELATIONS.get(table, {}))
            columns = ['id', 'position', 'payload', *refs]
            placeholders = ','.join('?' for _ in columns)
            for position, row in enumerate(data[table]):
                updates = ','.join(f'{column}=excluded.{column}' for column in columns if column != 'id')
                connection.execute(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}',
                                   [row['id'], position, json.dumps(row, ensure_ascii=False), *[row[key] for key in refs]])
        try:
            for table in reversed(SCHEMAS):
                ids = [row['id'] for row in data[table]]
                if ids:
                    placeholders = ','.join('?' for _ in ids)
                    connection.execute(f'DELETE FROM {table} WHERE id NOT IN ({placeholders})', ids)
                else:
                    connection.execute(f'DELETE FROM {table}')
        except sqlite3.IntegrityError as exc:
            raise StorageError('No se puede retirar una entidad docente vinculada a la biblioteca. Reasigna sus documentos primero.') from exc
        for key in ('schema_version', 'timezone'):
            connection.execute('INSERT OR REPLACE INTO settings VALUES (?, ?)', (key, json.dumps(data[key])))
        connection.execute('INSERT INTO config_imports (imported_at, sha256, snapshot) VALUES (?, ?, ?)',
                           (datetime.now(timezone.utc).isoformat(), digest, snapshot))
    return {'changed': True, 'sha256': digest, 'message': 'Configuración importada.'}


def read_config(path: Path) -> dict:
    with closing(connect(path, readonly=True)) as connection:
        connection.execute('BEGIN')  # Instantánea coherente durante todas las lecturas.
        if connection.execute('PRAGMA user_version').fetchone()[0] not in range(1, SCHEMA_VERSION + 1):
            raise StorageError('Versión de base no compatible; no se modificará.')
        result = {key: json.loads(value) for key, value in connection.execute('SELECT key, value FROM settings')}
        for table in SCHEMAS:
            result[table] = [json.loads(row[0]) for row in connection.execute(f'SELECT payload FROM {table} ORDER BY position')]
    return validate(result)
