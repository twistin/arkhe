from dataclasses import replace
import json
from pathlib import Path
import sqlite3

import httpx
import pytest

from docente_ai.config import load
from docente_ai.library.service import import_document, authorize_document, delete_document
from docente_ai.rag.chunking import split_segment
from docente_ai.rag.ollama import OllamaEmbedder, EmbeddingError, normalize
from docente_ai.rag.service import index_library, search
from docente_ai.rag.settings import RagSettings, load_settings
from docente_ai.storage import import_config

EXAMPLE = Path(__file__).resolve().parents[1] / 'config/teaching.example.yaml'


class FakeEmbedder:
    model = 'fake:1'
    digest = 'digest-1'

    def __init__(self, callback=None):
        self.calls = []
        self.callback = callback

    def embed(self, texts, *, query=False):
        self.calls.append((texts, query))
        if self.callback:
            self.callback(query)
        return [normalize([1, 0.1, 0.1]) if 'ritmo' in text.lower() else normalize([0.1, 1, 0.1]) for text in texts]


@pytest.fixture
def corpus(tmp_path):
    db = tmp_path / 'data' / 'docente.sqlite3'
    config = load(EXAMPLE)
    config['subjects'].append({'id': 'otra', 'name': 'Otra asignatura'})
    import_config(db, config)

    def add(text, *, subject='historia-i', enabled=True, category='documental'):
        path = tmp_path / f'source-{len(list(tmp_path.glob("source-*")))}.txt'
        path.write_text(text)
        result = import_document(db, path, category=category, subjects=[subject])
        if enabled:
            authorize_document(db, result['document_id'], enabled=True)
        return result

    return db, add


def test_chunks_cover_text_and_keep_exact_offsets():
    text = ('Primera línea.\r\nSegunda línea.\r\n\r\n' * 15) + 'Final.'
    segment = {'id': 'segment-1', 'text': text, 'locator': {'kind': 'lines', 'line_start': 1, 'line_end': 50, 'printed_page': None}}
    chunks = split_segment(segment, RagSettings('fake', chunk_chars=100, overlap_chars=20))
    covered = set()
    for chunk in chunks:
        loc = chunk['locator']
        assert chunk['text'] == text[loc['char_start']:loc['char_end']]
        assert 0 < len(chunk['text']) <= 100
        assert loc['printed_page'] is None
        assert loc['line_start'] <= loc['line_end']
        covered.update(range(loc['char_start'], loc['char_end']))
    assert covered == set(range(len(text)))
    assert chunks[-1]['text'].endswith('Final.')


def test_chunk_pdf_page_kept():
    segment = {'id': 'seg', 'text': 'Texto de página. ' * 40,
               'locator': {'kind': 'pdf_page', 'pdf_page_index': 9, 'printed_page': None, 'page_label': 'v'}}
    chunks = split_segment(segment, RagSettings('fake', chunk_chars=100, overlap_chars=10))
    assert len(chunks) > 1
    assert all(chunk['locator']['pdf_page_index'] == 9 for chunk in chunks)
    assert all(chunk['locator']['printed_page'] is None for chunk in chunks)


def test_index_search_and_reuse_after_restart(corpus):
    db, add = corpus
    relevant = add('El ritmo organiza duraciones en el tiempo.')
    add('La melodía enlaza alturas musicales.')
    settings = RagSettings('fake:1')
    embedder = FakeEmbedder()
    result = index_library(db, settings, embedder)
    assert result['indexed_versions'] == 2
    assert index_library(db, settings, FakeEmbedder())['skipped_versions'] == 2
    found = search(db, settings, FakeEmbedder(), 'ritmo', subject='historia-i', top_k=1)
    assert found['results'][0]['document_id'] == relevant['document_id']
    assert found['results'][0]['locator']['printed_page'] is None
    assert 'Sin autor identificado, s. f., líneas' in found['results'][0]['citation']


def test_delete_indexed_document_removes_rag_dependencies(corpus):
    db, add = corpus
    document = add('El ritmo organiza duraciones en el tiempo.')
    index_library(db, RagSettings('fake:1'), FakeEmbedder())

    result = delete_document(db, document['document_id'])

    assert result['deleted'] is True
    with sqlite3.connect(db) as connection:
        assert connection.execute(
            'SELECT count(*) FROM documents WHERE id=?', (document['document_id'],)
        ).fetchone()[0] == 0
        assert connection.execute(
            'SELECT count(*) FROM rag_indexes WHERE version_id=?', (document['version_id'],)
        ).fetchone()[0] == 0
        assert connection.execute(
            'SELECT count(*) FROM rag_chunks WHERE version_id=?', (document['version_id'],)
        ).fetchone()[0] == 0


def test_filters_applied_before_top_k(corpus):
    db, add = corpus
    wanted = add('Una melodía para la asignatura autorizada.')
    excluded = add('ritmo', enabled=False)
    wrong_subject = add('ritmo exacto', subject='otra')
    teacher = add('ritmo del profesor', category='profesor')
    settings = RagSettings('fake:1')
    index_library(db, settings, FakeEmbedder())
    result = search(db, settings, FakeEmbedder(), 'ritmo', subject='historia-i', top_k=1)
    assert [item['document_id'] for item in result['results']] == [wanted['document_id']]
    assert result['results'][0]['document_id'] not in {excluded['document_id'], wrong_subject['document_id'], teacher['document_id']}
    result = search(db, settings, FakeEmbedder(), 'ritmo', subject='historia-i', category='profesor')
    assert [item['document_id'] for item in result['results']] == [teacher['document_id']]


def test_exclusion_after_index_applied_immediately(corpus):
    db, add = corpus
    doc = add('ritmo')
    settings = RagSettings('fake:1')
    index_library(db, settings, FakeEmbedder())
    authorize_document(db, doc['document_id'], enabled=False)
    embedder = FakeEmbedder()
    result = search(db, settings, embedder, 'ritmo', subject='historia-i')
    assert result['status'] == 'no_evidence'
    assert embedder.calls == []


def test_exclusion_during_query_is_respected(corpus):
    db, add = corpus
    doc = add('ritmo')
    settings = RagSettings('fake:1')
    index_library(db, settings, FakeEmbedder())

    def exclude(query):
        if query:
            authorize_document(db, doc['document_id'], enabled=False)

    result = search(db, settings, FakeEmbedder(exclude), 'ritmo', subject='historia-i')
    assert result['status'] == 'no_evidence'


def test_exclusion_during_index_prevents_commit(corpus):
    db, add = corpus
    doc = add('ritmo')
    settings = RagSettings('fake:1')
    with pytest.raises(ValueError, match='excluida'):
        index_library(db, settings, FakeEmbedder(lambda query: authorize_document(db, doc['document_id'], enabled=False)))
    with sqlite3.connect(db) as connection:
        assert connection.execute('SELECT count(*) FROM rag_chunks').fetchone()[0] == 0
        assert connection.execute('SELECT count(*) FROM rag_indexes').fetchone()[0] == 0


def test_failure_mid_batch_does_not_activate_partial_index(corpus):
    db, add = corpus
    add('ritmo musical ' * 100)
    settings = RagSettings('fake:1', chunk_chars=100, overlap_chars=10, batch_size=1)
    count = 0

    def fail(query):
        nonlocal count
        count += 1
        if count == 2:
            raise EmbeddingError('simulated')

    with pytest.raises(EmbeddingError):
        index_library(db, settings, FakeEmbedder(fail))
    with sqlite3.connect(db) as connection:
        assert connection.execute('SELECT count(*) FROM rag_indexes').fetchone()[0] == 0
        assert connection.execute('SELECT count(*) FROM rag_chunks').fetchone()[0] == 0
    assert index_library(db, settings, FakeEmbedder())['indexed_versions'] == 1


def test_changed_digest_or_prefix_requires_own_index(corpus):
    db, add = corpus
    add('ritmo')
    settings = RagSettings('fake:1')
    index_library(db, settings, FakeEmbedder())
    newer = FakeEmbedder()
    newer.digest = 'new-digest'
    with pytest.raises(ValueError, match='No existe índice'):
        search(db, settings, newer, 'ritmo', subject='historia-i')
    assert index_library(db, settings, newer)['indexed_versions'] == 1
    with pytest.raises(ValueError, match='No existe índice'):
        search(db, replace(settings, query_prefix='Different'), newer, 'ritmo', subject='historia-i')


def test_dimension_mismatch_rejected(corpus):
    db, add = corpus
    add('ritmo')
    settings = RagSettings('fake:1')
    index_library(db, settings, FakeEmbedder())
    fake = FakeEmbedder()
    fake.embed = lambda texts, query=False: [[1, 0] for _ in texts]
    with pytest.raises(ValueError, match='incompatible'):
        search(db, settings, fake, 'ritmo', subject='historia-i')


def test_no_silent_partial_corpus_and_document_selection(corpus):
    db, add = corpus
    first = add('ritmo')
    settings = RagSettings('fake:1')
    index_library(db, settings, FakeEmbedder())
    add('Otro texto autorizado aún sin índice.')
    with pytest.raises(ValueError, match='sin indexar'):
        search(db, settings, FakeEmbedder(), 'ritmo', subject='historia-i')
    assert search(db, settings, FakeEmbedder(), 'ritmo', subject='historia-i', document_ids=[first['document_id']])['results']


def test_distance_threshold_can_produce_abstention(corpus):
    db, add = corpus
    add('Una melodía')
    settings = RagSettings('fake:1')
    index_library(db, settings, FakeEmbedder())
    result = search(db, settings, FakeEmbedder(), 'ritmo', subject='historia-i', max_distance=0.1)
    assert result['status'] == 'no_evidence'


def test_new_document_version_requires_new_index(corpus, tmp_path):
    db, add = corpus
    first = add('ritmo')
    settings = RagSettings('fake:1')
    index_library(db, settings, FakeEmbedder())
    path = tmp_path / 'updated.txt'
    path.write_text('melodía')
    new = import_document(db, path, category='documental', document_id=first['document_id'])
    authorize_document(db, first['document_id'], enabled=True)
    with pytest.raises(ValueError, match='sin indexar'):
        search(db, settings, FakeEmbedder(), 'ritmo', subject='historia-i')
    index_library(db, settings, FakeEmbedder())
    assert search(db, settings, FakeEmbedder(), 'melodía', subject='historia-i')['results'][0]['version_id'] == new['version_id']


@pytest.mark.parametrize('kwargs', [
    {'model': ''}, {'model': 'example:cloud'}, {'host': 'https://external.invalid'},
    {'timeout_seconds': float('nan')}, {'chunk_chars': True}, {'overlap_chars': 1200},
    {'batch_size': 0}, {'document_prefix': None},
])
def test_settings_invalid(kwargs):
    with pytest.raises(ValueError):
        RagSettings(**({'model': 'fake'} | kwargs))


def test_settings_yaml_round_trip(tmp_path):
    path = tmp_path / 'rag.yaml'
    path.write_text('schema_version: 1\nembeddings:\n  model: fake:1\n')
    assert load_settings(path).model == 'fake:1'
    path.write_text('schema_version: 1\nembeddings:\n  modle: typo\n')
    with pytest.raises(ValueError):
        load_settings(path)


def mock_ollama(*, payload=None, remote=False, capabilities=None, status=200):
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path == '/api/tags':
            return httpx.Response(200, json={'models': [{'name': 'fake:1', 'digest': 'hash', 'size': 100}]})
        if request.url.path == '/api/show':
            return httpx.Response(200, json={'capabilities': ['embedding'] if capabilities is None else capabilities,
                                            'remote_host': 'https://cloud.invalid' if remote else None})
        return httpx.Response(status, json=payload if payload is not None else {'embeddings': [[3, 4, 0]]})

    return httpx.MockTransport(handle), requests


def test_ollama_contract_no_truncation_prefixes_and_no_proxy(monkeypatch):
    monkeypatch.setenv('ALL_PROXY', 'http://external.invalid:8888')
    transport, requests = mock_ollama()
    settings = RagSettings('fake:1', query_prefix='Query: ')
    with OllamaEmbedder(settings, transport=transport) as embedder:
        assert embedder.embed(['ritmo'], query=True) == [[0.6, 0.8, 0.0]]
    request = next(request for request in requests if request.url.path == '/api/embed')
    payload = json.loads(request.content)
    assert payload['truncate'] is False
    assert payload['input'] == ['Query: ritmo']
    assert payload['keep_alive'] == 0
    assert all(request.url.host == '127.0.0.1' for request in requests)


@pytest.mark.parametrize('kwargs', [{'remote': True}, {'capabilities': ['completion']}])
def test_remote_or_non_embedding_model_rejected(kwargs):
    transport, requests = mock_ollama(**kwargs)
    with pytest.raises(EmbeddingError):
        with OllamaEmbedder(RagSettings('fake:1'), transport=transport):
            pytest.fail('Should reject')
    assert not any(request.url.path == '/api/embed' for request in requests)


@pytest.mark.parametrize('vector', [[], [0, 0], [float('nan'), 1], ['x'], [True, 1]])
def test_invalid_vectors_rejected(vector):
    transport, _ = mock_ollama(payload={'embeddings': [vector]})
    with OllamaEmbedder(RagSettings('fake:1'), transport=transport) as embedder:
        with pytest.raises(EmbeddingError):
            embedder.embed(['text'])


def test_ollama_overlong_input_never_silently_truncated():
    transport, _ = mock_ollama(status=400)
    with OllamaEmbedder(RagSettings('fake:1'), transport=transport) as embedder:
        with pytest.raises(EmbeddingError, match='no se trunca'):
            embedder.embed(['text'])


def test_remote_redirect_never_followed():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(302, headers={'Location': 'https://external.invalid'})

    with pytest.raises(EmbeddingError, match='302'):
        with OllamaEmbedder(RagSettings('fake:1'), transport=httpx.MockTransport(respond)):
            pytest.fail('redirect followed')
    assert len(requests) == 1
    assert requests[0].url.host == '127.0.0.1'


def test_changed_model_during_embedding_rejected():
    calls = 0

    def respond(request):
        nonlocal calls
        if request.url.path == '/api/tags':
            calls += 1
            return httpx.Response(200, json={'models': [{'name': 'fake:1', 'size': 100, 'digest': 'old' if calls < 3 else 'new'}]})
        if request.url.path == '/api/show':
            return httpx.Response(200, json={'capabilities': ['embedding']})
        return httpx.Response(200, json={'embeddings': [[1, 0, 0]]})

    with OllamaEmbedder(RagSettings('fake:1'), transport=httpx.MockTransport(respond)) as embedder:
        with pytest.raises(EmbeddingError, match='cambiado'):
            embedder.embed(['text'])


def test_missing_model_does_not_pull_automatically():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={'models': []})

    with pytest.raises(EmbeddingError, match='no está instalado'):
        with OllamaEmbedder(RagSettings('fake:1'), transport=httpx.MockTransport(respond)):
            pytest.fail('missing model accepted')
    assert [request.url.path for request in requests] == ['/api/tags']


def test_embedding_timeout_has_no_fallback():
    def respond(request):
        raise httpx.ReadTimeout('simulated', request=request)

    with pytest.raises(EmbeddingError, match='no se usa ningún servicio alternativo'):
        with OllamaEmbedder(RagSettings('fake:1'), transport=httpx.MockTransport(respond)):
            pytest.fail('timeout ignored')


def test_cli_search_and_index_with_mock_model(corpus, tmp_path, monkeypatch, capsys):
    from docente_ai.cli import main
    import docente_ai.rag.cli as rag_cli
    db, add = corpus
    doc = add('ritmo musical')
    path = tmp_path / 'rag.yaml'
    path.write_text('schema_version: 1\nembeddings:\n  model: fake:1\n')

    class ManagedFake(FakeEmbedder):
        def __init__(self, settings):
            super().__init__()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(rag_cli, 'OllamaEmbedder', ManagedFake)
    options = ['--db', str(db), '--rag-config', str(path), '--json']
    assert main(['library', 'index', *options]) == 0
    assert json.loads(capsys.readouterr().out)['indexed_versions'] == 1
    assert main(['search', 'ritmo', '--subject', 'historia-i', *options]) == 0
    assert json.loads(capsys.readouterr().out)['results'][0]['document_id'] == doc['document_id']


def test_migrate_library_v2_without_losing_documents(corpus):
    from docente_ai.library.service import show_document
    db, add = corpus
    doc = add('ritmo')
    with sqlite3.connect(db) as connection:
        for table in ('session_feedback', 'session_unit_progress', 'session_records', 'generation_runs', 'rag_indexes', 'rag_chunks', 'embedding_profiles'):
            connection.execute(f'DROP TABLE {table}')
        connection.execute('PRAGMA user_version=2')
    assert index_library(db, RagSettings('fake:1'), FakeEmbedder())['indexed_versions'] == 1
    assert show_document(db, doc['document_id'])['enabled']
    with sqlite3.connect(db) as connection:
        assert connection.execute('PRAGMA user_version').fetchone()[0] == 8
        assert connection.execute('PRAGMA foreign_key_check').fetchall() == []


def test_explicit_empty_document_selection_never_expands_corpus(corpus):
    db, add = corpus
    add('ritmo')
    settings = RagSettings('fake:1')
    embedder = FakeEmbedder()
    assert index_library(db, settings, embedder, document_ids=[])['indexed_versions'] == 0
    assert search(db, settings, embedder, 'ritmo', subject='historia-i', document_ids=[])['status'] == 'no_evidence'
    assert embedder.calls == []


def test_embedding_index_session_keeps_model_then_unloads():
    transport, requests = mock_ollama()
    with OllamaEmbedder(RagSettings('fake:1'), transport=transport) as embedder:
        embedder.keep_alive = '5m'
        embedder.embed(['uno'])
        embedder.embed(['dos'])
    payloads = [json.loads(r.content) for r in requests if r.url.path == '/api/embed']
    assert [p['keep_alive'] for p in payloads] == ['5m', '5m', 0]
    assert payloads[-1]['input'] == []

def test_hybrid_variants_cannot_reintroduce_excluded_source(corpus):
    db, add = corpus
    allowed=add('isorhythm tenor rhythmic talea')
    excluded=add('isorhythm tenor rhythmic talea color')
    settings=RagSettings('fake:1')
    index_library(db,settings,FakeEmbedder())
    authorize_document(db,excluded['document_id'],enabled=False)
    result=search(db,settings,FakeEmbedder(),'isorrítmico',subject='historia-i',query_variants=['isorhythm talea'])
    assert result['results']
    assert {r['document_id'] for r in result['results']}=={allowed['document_id']}
