"""Índices exactos locales; filtros de autorización antes del cálculo de distancia."""

from contextlib import closing
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from uuid import uuid4

import sqlite_vec

from docente_ai.library.service import check_subjects, now, original_file, read_connection
from docente_ai.rag.chunking import split_segment
from docente_ai.rag.settings import RagSettings
from docente_ai.storage import connect, migrate


NO_EVIDENCE = 'No encuentro información suficiente en las fuentes autorizadas.'


def load_vector_extension(connection):
    if not hasattr(connection, 'enable_load_extension'):
        raise ValueError('Este Python no permite extensiones SQLite. Utiliza el entorno Python validado del proyecto.')
    connection.enable_load_extension(True)
    try:
        sqlite_vec.load(connection)
    finally:
        connection.enable_load_extension(False)


def eligible(connection, *, subject=None, category='all', document_ids=None):
    if category not in {'all', 'documental', 'profesor'}:
        raise ValueError('Categoría de búsqueda inválida.')
    if subject:
        check_subjects(connection, [subject])
    query = '''SELECT d.id AS document_id,d.category,d.metadata,v.id AS version_id,v.sha256,v.original_path
               FROM documents d JOIN document_versions v ON v.id=d.current_version_id
               WHERE d.enabled=1 AND v.status IN ('ready','needs_review')'''
    args = []
    if subject:
        query += ' AND (d.shared=1 OR EXISTS(SELECT 1 FROM document_subjects ds WHERE ds.document_id=d.id AND ds.subject_id=?))'
        args.append(subject)
    if category != 'all':
        query += ' AND d.category=?'
        args.append(category)
    if document_ids is not None:
        if not isinstance(document_ids, list) or any(not isinstance(item, str) or not item for item in document_ids):
            raise ValueError('La selección documental debe ser una lista de IDs no vacíos.')
        if not document_ids:
            return []
        query += ' AND d.id IN (' + ','.join('?' for _ in document_ids) + ')'
        args.extend(document_ids)
    return [dict(row) for row in connection.execute(query + ' ORDER BY d.id', args)]


def verify_original(db, version):
    original = original_file(db, version['original_path'])
    if not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != version['sha256']:
        raise ValueError(f"Original ausente o alterado: {version['document_id']}. Revisa la biblioteca.")


def representation(settings):
    return json.dumps(settings.representation(), sort_keys=True, ensure_ascii=False)


def find_profile(connection, settings, embedder):
    if connection.execute('PRAGMA user_version').fetchone()[0] < 3:
        return None
    row = connection.execute('SELECT * FROM embedding_profiles WHERE model=? AND digest=? AND settings=?',
                             (embedder.model, embedder.digest, representation(settings))).fetchone()
    return dict(row) if row else None


def ensure_current(db, version, *, subject, document_ids):
    with closing(read_connection(db)) as connection:
        allowed = eligible(connection, subject=subject, document_ids=document_ids)
        if not any(item['version_id'] == version['version_id'] for item in allowed):
            raise ValueError('La autorización o versión cambió durante la indexación; se ha cancelado esa versión.')


def index_library(db: Path, settings: RagSettings, embedder, *, subject=None, document_ids=None, progress=None) -> dict:
    with closing(read_connection(db)) as connection:
        versions = eligible(connection, subject=subject, document_ids=document_ids)
    if not versions:
        return {'indexed_versions': 0, 'skipped_versions': 0, 'chunks': 0, 'message': NO_EVIDENCE}
    completed = skipped = total = 0
    for version in versions:
        ensure_current(db, version, subject=subject, document_ids=document_ids)
        verify_original(db, version)
        with closing(read_connection(db)) as connection:
            profile = find_profile(connection, settings, embedder)
            if profile and connection.execute('SELECT 1 FROM rag_indexes WHERE version_id=? AND profile_id=?',
                                              (version['version_id'], profile['id'])).fetchone():
                skipped += 1
                continue
            segments = []
            for row in connection.execute('SELECT id,text,locator FROM document_segments WHERE version_id=? ORDER BY ordinal', (version['version_id'],)):
                segment = dict(row)
                segment['locator'] = json.loads(segment['locator'])
                segments.append(segment)
        chunks = [chunk for segment in segments for chunk in split_segment(segment, settings)]
        if not chunks:
            raise ValueError('La versión autorizada no contiene fragmentos indexables.')
        vectors = []
        if hasattr(embedder, 'keep_alive'):
            embedder.keep_alive = '5m'
        if progress:
            progress(0, len(chunks))
        for offset in range(0, len(chunks), settings.batch_size):
            ensure_current(db, version, subject=subject, document_ids=document_ids)
            batch = embedder.embed([item['text'] for item in chunks[offset:offset + settings.batch_size]])
            vectors.extend(batch)
            if progress:
                progress(len(vectors), len(chunks))
        dimensions = {len(vector) for vector in vectors}
        if len(vectors) != len(chunks) or len(dimensions) != 1:
            raise ValueError('Embeddings incompletos o dimensiones incompatibles; no se guarda un índice parcial.')
        dimension = next(iter(dimensions))
        if profile and profile['dimensions'] != dimension:
            raise ValueError('Dimensión distinta para el mismo perfil; no se mezclarán vectores.')
        verify_original(db, version)
        # Insertar solo después de obtener todos los vectores de esta versión.
        with closing(connect(db)) as connection, connection:
            connection.row_factory = sqlite3.Row
            connection.execute('BEGIN IMMEDIATE')
            migrate(connection)
            allowed = eligible(connection, subject=subject, document_ids=document_ids)
            if not any(item['version_id'] == version['version_id'] for item in allowed):
                raise ValueError('Fuente excluida o sustituida durante la indexación; no se activa el índice.')
            load_vector_extension(connection)
            profile = find_profile(connection, settings, embedder)
            if profile and profile['dimensions'] != dimension:
                raise ValueError('Dimensión incompatible con el perfil persistido.')
            if not profile:
                fingerprint = f'{embedder.model}\n{embedder.digest}\n{dimension}\n{representation(settings)}'
                profile = {'id': hashlib.sha256(fingerprint.encode()).hexdigest(), 'dimensions': dimension}
                connection.execute('INSERT INTO embedding_profiles VALUES (?,?,?,?,?,?)',
                                   (profile['id'], representation(settings), embedder.model, embedder.digest, dimension, now()))
            if connection.execute('SELECT 1 FROM rag_indexes WHERE version_id=? AND profile_id=?', (version['version_id'], profile['id'])).fetchone():
                skipped += 1
                continue
            for ordinal, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True), 1):
                connection.execute('INSERT INTO rag_chunks VALUES (?,?,?,?,?,?,?,?)',
                                   (f'chunk-{uuid4().hex}', version['version_id'], chunk['segment_id'], profile['id'], ordinal,
                                    chunk['text'], json.dumps(chunk['locator'], ensure_ascii=False), sqlite_vec.serialize_float32(vector)))
            connection.execute('INSERT INTO rag_indexes VALUES (?,?,?,?)', (version['version_id'], profile['id'], len(chunks), now()))
        completed += 1
        total += len(chunks)
    return {'indexed_versions': completed, 'skipped_versions': skipped, 'chunks': total,
            'message': 'Indexación local completada; las autorizaciones se vuelven a comprobar en cada búsqueda.'}


def citation(meta, locator):
    author = '; '.join(meta['authors']) if meta['authors'] else 'Sin autor identificado'
    year = str(meta['year']) if meta['year'] is not None else 's. f.'
    if locator['kind'] == 'pdf_page':
        # Esta fase no dispone de un flujo de verificación de página impresa.
        location = f"página {locator['pdf_page_index']} del archivo PDF"
    else:
        location = f"líneas {locator['line_start']}–{locator['line_end']}"
    return f"{author}, {year}, {location}. {meta['title']}"


def search(db: Path, settings: RagSettings, embedder, query: str, *, subject: str,
           category='documental', document_ids=None, top_k=6, max_distance=None, query_variants=None) -> dict:
    if not isinstance(query, str) or not query.strip():
        raise ValueError('La consulta no puede estar vacía.')
    if not subject:
        raise ValueError('La búsqueda requiere una asignatura explícita.')
    if type(top_k) is not int or not 1 <= top_k <= 100:
        raise ValueError('top_k debe estar entre 1 y 100.')
    if max_distance is not None and (not math.isfinite(max_distance) or not 0 <= max_distance <= 2):
        raise ValueError('La distancia máxima debe estar entre 0 y 2.')
    with closing(read_connection(db)) as connection:
        sources = eligible(connection, subject=subject, category=category, document_ids=document_ids)
        if not sources:
            return {'status': 'no_evidence', 'message': NO_EVIDENCE, 'results': []}
        profile = find_profile(connection, settings, embedder)
        if not profile:
            raise ValueError('No existe índice para este modelo, digest y configuración. Ejecuta library index.')
        for source in sources:
            if not connection.execute('SELECT 1 FROM rag_indexes WHERE version_id=? AND profile_id=?', (source['version_id'], profile['id'])).fetchone():
                raise ValueError('Hay fuentes autorizadas sin indexar para este perfil. Ejecuta library index; no se usará un corpus parcial silenciosamente.')
    queries = list(dict.fromkeys([query, *(query_variants or [])]))
    if len(queries)>6 or any(not isinstance(q,str) or not q.strip() or len(q)>4000 for q in queries):
        raise ValueError('Consultas de recuperación inválidas.')
    vectors = embedder.embed(queries, query=True)
    if len(vectors) != len(queries) or any(len(v) != profile['dimensions'] for v in vectors):
        raise ValueError('El vector de consulta es incompatible con el índice.')
    # Nueva instantánea tras la petición a Ollama: una exclusión concurrente
    # durante esa petición debe aplicarse antes de evaluar similitud.
    with closing(read_connection(db)) as connection:
        sources = eligible(connection, subject=subject, category=category, document_ids=document_ids)
        if not sources:
            return {'status': 'no_evidence', 'message': NO_EVIDENCE, 'results': []}
        version_ids = [source['version_id'] for source in sources]
        for version_id in version_ids:
            if not connection.execute('SELECT 1 FROM rag_indexes WHERE version_id=? AND profile_id=?', (version_id, profile['id'])).fetchone():
                raise ValueError('El corpus cambió durante la búsqueda. Indexa las versiones vigentes y repite.')
        load_vector_extension(connection)
        placeholders = ','.join('?' for _ in version_ids)
        # MATERIALIZED impide calcular distancias sobre el conjunto sin filtrar.
        sql = f'''WITH candidates AS MATERIALIZED (
                    SELECT * FROM rag_chunks WHERE profile_id=? AND version_id IN ({placeholders})
                  ), ranked AS MATERIALIZED (
                    SELECT *,vec_distance_cosine(vector,?) AS distance FROM candidates
                  ) SELECT id,version_id,segment_id,text,locator,distance FROM ranked
                    WHERE (? IS NULL OR distance<=?) ORDER BY distance,id LIMIT ?'''
        raw = connection.execute(sql, [profile['id'], *version_ids, sqlite_vec.serialize_float32(vectors[0]), max_distance, max_distance, top_k]).fetchall()
        if query_variants:
            from docente_ai.rag.ranking import hybrid
            pool={};rankings=[]
            for vector in vectors:
                ranked=connection.execute(sql, [profile['id'], *version_ids, sqlite_vec.serialize_float32(vector), max_distance, max_distance, 1000000]).fetchall()
                rankings.append([r['id'] for r in ranked[:60]])
                for row in ranked:
                    if row['id'] not in pool or row['distance']<pool[row['id']]['distance']:
                        pool[row['id']]=dict(row)
            raw=hybrid(list(pool.values()),rankings,queries,top_k)
        by_version = {source['version_id']: source for source in sources}
        checked = set()
        results = []
        for row in raw:
            source = by_version[row['version_id']]
            if source['version_id'] not in checked:
                verify_original(db, source)
                checked.add(source['version_id'])
            meta = json.loads(source['metadata'])
            locator = json.loads(row['locator'])
            results.append({'chunk_id': row['id'], 'document_id': source['document_id'], 'version_id': row['version_id'],
                            'segment_id': row['segment_id'], 'category': source['category'], 'text': row['text'],
                            'locator': locator, 'distance': row['distance'], 'metadata': meta, 'citation': citation(meta, locator)})
    return {'status': 'candidates' if results else 'no_evidence',
            'message': 'Fragmentos candidatos; la similitud no verifica afirmaciones ni garantiza que respondan a la pregunta.' if results else NO_EVIDENCE,
            'profile_id': profile['id'], 'results': results}
