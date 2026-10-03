"""Operaciones locales de biblioteca; la autorización siempre es explícita."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from urllib.parse import urlsplit
from uuid import uuid4

from docente_ai.library.parsers import extract
from docente_ai.storage import SCHEMA_VERSION, connect, migrate, StorageError

FIELDS = {'title', 'authors', 'year', 'publisher', 'doi', 'url', 'document_type', 'tags', 'collections', 'origin'}
LIST_FIELDS = {'authors', 'tags', 'collections'}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def metadata(values: dict, *, defaults: dict | None = None) -> dict:
    if values.keys() - FIELDS:
        raise ValueError('Campos bibliográficos desconocidos.')
    result = {key: ([] if key in LIST_FIELDS else None) for key in FIELDS}
    result.update(defaults or {})
    result.update(values)
    for key, value in result.items():
        if key in LIST_FIELDS:
            if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
                raise ValueError(f'{key}: se esperaba una lista de textos no vacíos.')
            result[key] = list(dict.fromkeys(item.strip() for item in value))
        elif key == 'year':
            if value is not None and (type(value) is not int or not 1 <= value <= 9999):
                raise ValueError('El año debe ser un entero entre 1 y 9999 o desconocido.')
        elif value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'{key}: se esperaba texto no vacío.')
            result[key] = value.strip()
    if not result['title']:
        raise ValueError('El título no puede estar vacío.')
    if result['doi'] and not re.fullmatch(r'10\.\d{4,9}/\S+', result['doi']):
        raise ValueError('DOI inválido; utiliza el identificador 10.…/… sin URL.')
    if result['url']:
        try:
            url = urlsplit(result['url'])
            if url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password:
                raise ValueError
            _ = url.port
        except ValueError:
            raise ValueError('URL bibliográfica inválida; utiliza http(s) sin credenciales.') from None
    return result


def event(connection, document_id, action, details):
    connection.execute('INSERT INTO library_events(document_id,created_at,action,details) VALUES (?,?,?,?)',
                       (document_id, now(), action, json.dumps(details, ensure_ascii=False)))


def get_document(connection, document_id):
    row = connection.execute('SELECT * FROM documents WHERE id=?', (document_id,)).fetchone()
    if row is None:
        raise ValueError(f'Documento inexistente: {document_id}.')
    return dict(row)


def check_subjects(connection, subjects: list[str]):
    if not isinstance(subjects, list) or any(not isinstance(item, str) for item in subjects):
        raise ValueError('Las asignaturas deben ser una lista de IDs.')
    for subject in subjects:
        if connection.execute('SELECT id FROM subjects WHERE id=?', (subject,)).fetchone() is None:
            raise ValueError(f'Asignatura inexistente: {subject}. Importa primero la configuración docente.')


def subjects_for(connection, document_id):
    return [row[0] for row in connection.execute('SELECT subject_id FROM document_subjects WHERE document_id=? ORDER BY subject_id', (document_id,))]


def original_file(db: Path, relative: str) -> Path:
    root = db.resolve().parent
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root / 'library' / 'originals'):
        raise ValueError('Ruta de original fuera del almacén permitido.')
    return candidate


def preserve_original(db: Path, content: bytes, digest: str, suffix: str) -> str:
    relative = f'library/originals/{digest}{suffix}'
    target = original_file(db, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('El original almacenado no coincide con su hash. No se sobrescribirá.')
        return relative
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o444)
        try:
            os.link(temporary, target)  # Publicación atómica sin sobrescritura.
        except FileExistsError:
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError('Conflicto de integridad en el almacén de originales.') from None
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return relative


def import_document(
    db: Path, source: Path, *, category: str, values: dict | None = None,
    subjects: list[str] | None = None, shared: bool | None = None,
    document_id: str | None = None, max_mb: int = 300,
) -> dict:
    if category not in {'documental', 'profesor'}:
        raise ValueError('Categoría requerida: documental o profesor. Las generaciones IA no son fuentes.')
    if type(max_mb) is not int or not 1 <= max_mb <= 1024:
        raise ValueError('El límite de archivo debe estar entre 1 y 1024 MiB.')
    suffix = source.suffix.lower()
    if suffix not in {'.pdf', '.txt', '.md'}:
        raise ValueError('Formato no admitido. Utiliza .pdf, .txt o .md.')
    if not source.is_file() or source.resolve() == db.resolve():
        raise ValueError('Selecciona un archivo existente distinto de la base de datos.')
    with source.open('rb') as stream:
        content = stream.read(max_mb * 1024 * 1024 + 1)
    if len(content) > max_mb * 1024 * 1024:
        raise ValueError(f'El archivo supera el límite de {max_mb} MiB.')
    digest = hashlib.sha256(content).hexdigest()
    values = values or {}
    parsed = extract(content, suffix)
    with closing(connect(db)) as connection, connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN IMMEDIATE')
        migrate(connection)
        # Sin ID explícito, solo deduplicar dentro de la misma categoría.
        if document_id is None:
            match = connection.execute('SELECT d.id FROM documents d JOIN document_versions v ON v.document_id=d.id WHERE v.sha256=? AND d.category=? ORDER BY d.created_at LIMIT 1', (digest, category)).fetchone()
            document_id = match[0] if match else None
        existing = get_document(connection, document_id) if document_id else None
        if existing:
            if existing['category'] != category:
                raise ValueError('No se puede cambiar la categoría de un documento existente.')
            meta = metadata(values, defaults=json.loads(existing['metadata']))
            if meta != json.loads(existing['metadata']):
                raise ValueError('Los metadatos difieren. Utiliza library update para cambiarlos explícitamente.')
            if subjects is not None and sorted(set(subjects)) != subjects_for(connection, document_id):
                raise ValueError('Las asignaturas difieren. Utiliza library update para reasignar.')
            if shared is not None and shared != bool(existing['shared']):
                raise ValueError('El ámbito compartido difiere. Utiliza library update.')
            duplicate = connection.execute('SELECT id,status,error FROM document_versions WHERE document_id=? AND sha256=?', (document_id, digest)).fetchone()
            if duplicate:
                previous = connection.execute('SELECT original_path,sha256 FROM document_versions WHERE id=?', (duplicate['id'],)).fetchone()
                stored = original_file(db, previous['original_path'])
                if not stored.is_file() or hashlib.sha256(stored.read_bytes()).hexdigest() != previous['sha256']:
                    raise ValueError('El original almacenado falta o ha cambiado; no se considera una importación íntegra.')
                return {'document_id': document_id, 'version_id': duplicate['id'], 'status': duplicate['status'], 'changed': False,
                        'error': duplicate['error'], 'message': 'Versión ya importada; no se cambia la versión activa ni su autorización.'}
        else:
            meta = metadata(values, defaults={'title': source.stem, 'origin': 'archivo local'})
            subjects = list(dict.fromkeys(subjects or []))
            check_subjects(connection, subjects)
            document_id = f'doc-{uuid4().hex}'
            connection.execute('INSERT INTO documents(id,category,metadata,shared,created_at) VALUES (?,?,?,?,?)',
                               (document_id, category, json.dumps(meta, ensure_ascii=False), bool(shared), now()))
            connection.executemany('INSERT INTO document_subjects VALUES (?,?)', [(document_id, subject) for subject in subjects])
        relative = preserve_original(db, content, digest, suffix)
        version_id = f'ver-{uuid4().hex}'
        connection.execute('''INSERT INTO document_versions
            (id,document_id,sha256,original_path,source_path,format,imported_at,extractor,metadata_snapshot,status,page_count,warnings,error)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (version_id, document_id, digest, relative, str(source.resolve()), suffix[1:], now(), parsed.extractor,
             json.dumps(meta, ensure_ascii=False), parsed.status, parsed.page_count, json.dumps(parsed.warnings, ensure_ascii=False), parsed.error))
        for ordinal, segment in enumerate(parsed.segments, 1):
            connection.execute('INSERT INTO document_segments(id,version_id,ordinal,text,locator) VALUES (?,?,?,?,?)',
                               (f'{version_id}:{ordinal}', version_id, ordinal, segment['text'], json.dumps(segment['locator'], ensure_ascii=False)))
        if parsed.status != 'failed':
            connection.execute('UPDATE documents SET current_version_id=?,enabled=0 WHERE id=?', (version_id, document_id))
        event(connection, document_id, 'import', {'version_id': version_id, 'status': parsed.status, 'sha256': digest})
    return {'document_id': document_id, 'version_id': version_id, 'changed': True, 'status': parsed.status,
            'error': parsed.error, 'warnings': parsed.warnings, 'segments': len(parsed.segments),
            'message': 'Importación registrada. Revisa el texto y autoriza explícitamente la versión extraída.' if not parsed.error else parsed.error}


def read_connection(db):
    connection = connect(db, readonly=True)
    connection.row_factory = sqlite3.Row
    connection.execute('BEGIN')
    if connection.execute('PRAGMA user_version').fetchone()[0] not in range(2, SCHEMA_VERSION + 1):
        connection.close()
        raise StorageError('Biblioteca no inicializada o versión incompatible. Una primera importación actualiza bases de fase 2.')
    return connection


def list_documents(db: Path, *, subject: str | None = None, category: str | None = None, authorized_only: bool = False) -> list[dict]:
    with closing(read_connection(db)) as connection:
        if subject:
            check_subjects(connection, [subject])
        query = '''SELECT d.id,d.category,d.metadata,d.enabled,d.shared,d.current_version_id,v.status,
                   (SELECT status FROM document_versions WHERE document_id=d.id ORDER BY rowid DESC LIMIT 1) AS latest_import_status
                   FROM documents d LEFT JOIN document_versions v ON v.id=d.current_version_id WHERE 1=1'''
        args = []
        if category:
            query += ' AND d.category=?'
            args.append(category)
        if authorized_only:
            query += ' AND d.enabled=1 AND v.status IN (\'ready\',\'needs_review\')'
        if subject:
            query += ' AND (d.shared=1 OR EXISTS(SELECT 1 FROM document_subjects ds WHERE ds.document_id=d.id AND ds.subject_id=?))'
            args.append(subject)
        rows = []
        for row in connection.execute(query + ' ORDER BY d.created_at,d.id', args):
            item = dict(row)
            item['metadata'] = json.loads(item['metadata'])
            item['subjects'] = subjects_for(connection, item['id'])
            item['enabled'] = bool(item['enabled'])
            item['shared'] = bool(item['shared'])
            rows.append(item)
        return rows


def show_document(db: Path, document_id: str, *, text: bool = False, version_id: str | None = None) -> dict:
    with closing(read_connection(db)) as connection:
        document = get_document(connection, document_id)
        document['metadata'] = json.loads(document['metadata'])
        document['enabled'] = bool(document['enabled'])
        document['shared'] = bool(document['shared'])
        document['subjects'] = subjects_for(connection, document_id)
        document['versions'] = []
        for row in connection.execute('SELECT * FROM document_versions WHERE document_id=? ORDER BY rowid', (document_id,)):
            version = dict(row)
            for key in ('warnings', 'metadata_snapshot'):
                version[key] = json.loads(version[key])
            document['versions'].append(version)
        chosen = version_id or document['current_version_id'] or (document['versions'][-1]['id'] if document['versions'] else None)
        if chosen and chosen not in {item['id'] for item in document['versions']}:
            raise ValueError('La versión solicitada no pertenece a este documento.')
        document['selected_version_id'] = chosen
        if text:
            document['segments'] = []
            for row in connection.execute('SELECT id,ordinal,text,locator FROM document_segments WHERE version_id=? ORDER BY ordinal', (chosen,)):
                item = dict(row)
                item['locator'] = json.loads(item['locator'])
                document['segments'].append(item)
        return document


def update_document(db: Path, document_id: str, *, values: dict | None = None, subjects: list[str] | None = None, shared: bool | None = None) -> dict:
    if not db.is_file():
        raise StorageError('No existe la biblioteca. Importa primero un documento.')
    with closing(connect(db)) as connection, connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN IMMEDIATE')
        migrate(connection)
        document = get_document(connection, document_id)
        before = {'metadata': json.loads(document['metadata']), 'subjects': subjects_for(connection, document_id), 'shared': bool(document['shared'])}
        after = {'metadata': metadata(values or {}, defaults=before['metadata']),
                 'subjects': before['subjects'] if subjects is None else sorted(set(subjects)),
                 'shared': before['shared'] if shared is None else bool(shared)}
        check_subjects(connection, after['subjects'])
        if before == after:
            return {'document_id': document_id, 'changed': False, 'message': 'Sin cambios.'}
        connection.execute('UPDATE documents SET metadata=?,shared=?,enabled=0 WHERE id=?',
                           (json.dumps(after['metadata'], ensure_ascii=False), after['shared'], document_id))
        connection.execute('DELETE FROM document_subjects WHERE document_id=?', (document_id,))
        connection.executemany('INSERT INTO document_subjects VALUES (?,?)', [(document_id, subject) for subject in after['subjects']])
        event(connection, document_id, 'update', {'before': before, 'after': after})
    return {'document_id': document_id, 'changed': True, 'message': 'Metadatos actualizados; revisa y vuelve a autorizar.'}


def authorize_document(db: Path, document_id: str, *, enabled: bool, accept_warnings: bool = False) -> dict:
    if not db.is_file():
        raise StorageError('No existe la biblioteca. Importa primero un documento.')
    with closing(connect(db)) as connection, connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN IMMEDIATE')
        migrate(connection)
        document = get_document(connection, document_id)
        if enabled:
            version = connection.execute('SELECT * FROM document_versions WHERE id=? AND document_id=?', (document['current_version_id'], document_id)).fetchone()
            if not version or version['status'] == 'failed':
                raise ValueError('No hay una versión extraída válida que autorizar.')
            if version['status'] == 'needs_review' and not accept_warnings:
                raise ValueError('La extracción tiene avisos. Revisa library show --text y usa --accept-warnings si aceptas esas limitaciones.')
            if not document['shared'] and not subjects_for(connection, document_id):
                raise ValueError('Asocia al menos una asignatura o marca explícitamente el documento como compartido con library update --shared.')
            original = original_file(db, version['original_path'])
            if not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != version['sha256']:
                raise ValueError('El original falta o ha cambiado; no se puede autorizar.')
        connection.execute('UPDATE documents SET enabled=? WHERE id=?', (enabled, document_id))
        event(connection, document_id, 'authorize' if enabled else 'exclude',
              {'version_id': document['current_version_id'], 'accept_warnings': accept_warnings})
    return {'document_id': document_id, 'enabled': enabled, 'message': 'Fuente autorizada.' if enabled else 'Fuente excluida; se conservan original, versiones y extracción.'}


def delete_document(db: Path, document_id: str) -> dict:
    if not db.is_file():
        raise StorageError('No existe la biblioteca.')
    with closing(connect(db)) as connection, connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN IMMEDIATE')
        migrate(connection)
        _ = get_document(connection, document_id)
        versions = [r['id'] for r in connection.execute('SELECT id FROM document_versions WHERE document_id=?', (document_id,)).fetchall()]
        # Romper primero la referencia circular documents.current_version_id ->
        # document_versions. Las versiones conservan a su vez el documento padre.
        connection.execute('UPDATE documents SET current_version_id=NULL WHERE id=?', (document_id,))
        for vid in versions:
            connection.execute('DELETE FROM rag_chunks WHERE version_id=?', (vid,))
            connection.execute('DELETE FROM rag_indexes WHERE version_id=?', (vid,))
            connection.execute('DELETE FROM document_segments WHERE version_id=?', (vid,))
        connection.execute('DELETE FROM document_versions WHERE document_id=?', (document_id,))
        connection.execute('DELETE FROM document_subjects WHERE document_id=?', (document_id,))
        connection.execute('DELETE FROM library_events WHERE document_id=?', (document_id,))
        connection.execute('DELETE FROM documents WHERE id=?', (document_id,))
    return {'document_id': document_id, 'deleted': True, 'message': 'Documento eliminado de la biblioteca.'}
