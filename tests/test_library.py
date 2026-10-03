from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import sqlite3

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
import pytest

from docente_ai.cli import main
from docente_ai.config import load
from docente_ai.library.parsers import extract
from docente_ai.library.service import (
    authorize_document, import_document, list_documents, metadata,
    show_document, update_document,
)
from docente_ai.storage import import_config, read_config, StorageError

EXAMPLE = Path(__file__).resolve().parents[1] / 'config/teaching.example.yaml'


def pdf_bytes(*pages, encrypted=False):
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=300, height=300)
        if text:
            font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
            page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
            stream = DecodedStreamObject()
            stream.set_data(f'BT /F1 12 Tf 20 200 Td ({text}) Tj ET'.encode('ascii'))
            page[NameObject('/Contents')] = writer._add_object(stream)
    if encrypted:
        writer.encrypt('test-password')
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


@pytest.fixture
def library(tmp_path):
    db = tmp_path / 'data' / 'docente.sqlite3'
    import_config(db, load(EXAMPLE))
    source = tmp_path / 'notas.md'
    source.write_text('# Ars Nova\n\nNotas ficticias del profesor.\n', encoding='utf-8')
    return db, source


def ingest(library, **kwargs):
    db, source = library
    return import_document(db, source, category='profesor', subjects=['historia-i'], **kwargs)


@pytest.mark.parametrize('suffix', ['.txt', '.md'])
def test_utf8_text_exact_and_line_provenance(suffix):
    content = '\ufeff# Título\r\n\r\nTexto con acentos.\r\n'.encode('utf-8')
    result = extract(content, suffix)
    assert result.status == 'ready'
    segment = result.segments[0]
    assert segment['text'] == content.decode('utf-8-sig')
    assert segment['locator']['line_end'] == 3
    assert segment['locator']['char_end'] == len(segment['text'])
    assert segment['locator']['printed_page'] is None
    assert segment['locator']['pdf_page_index'] is None


def test_pdf_physical_pages_and_unknown_printed_numbers():
    result = extract(pdf_bytes('Page one synthetic with sufficient text', 'Page two synthetic with sufficient text'), '.pdf')
    assert result.status == 'ready'
    assert result.page_count == 2
    assert [s['locator']['pdf_page_index'] for s in result.segments] == [1, 2]
    assert all(s['locator']['printed_page'] is None for s in result.segments)
    assert 'Page two synthetic' in result.segments[1]['text']


@pytest.mark.parametrize(('content', 'suffix'), [
    (b'', '.txt'), (b'   \n', '.md'), (b'\xff', '.txt'), (b'abc\x00def', '.txt'),
    (b'not a pdf', '.pdf'),
])
def test_bad_documents_fail(content, suffix):
    assert extract(content, suffix).status == 'failed'


def test_blank_and_encrypted_pdf_fail():
    assert extract(pdf_bytes(None), '.pdf').status == 'failed'
    assert extract(pdf_bytes('Text', encrypted=True), '.pdf').status == 'failed'


def test_partial_pdf_requires_ocr_before_authorization():
    result = extract(pdf_bytes('Known text', None), '.pdf')
    assert result.status == 'failed'
    assert len(result.warnings) == 2
    assert 'brew install ocrmypdf' in result.error
    assert result.page_count == 2
    assert len(result.segments) == 1


def test_import_preserves_original_and_is_not_authorized(library):
    db, source = library
    result = ingest(library)
    doc = show_document(db, result['document_id'], text=True)
    original = db.parent / doc['versions'][0]['original_path']
    assert original.read_bytes() == source.read_bytes()
    assert doc['metadata']['authors'] == []
    assert doc['metadata']['year'] is None
    assert not doc['enabled']
    assert not list_documents(db, authorized_only=True)
    assert doc['segments'][0]['text'] == source.read_text()
    source.unlink()
    assert original.exists()
    authorize_document(db, result['document_id'], enabled=True)
    assert len(list_documents(db, authorized_only=True, subject='historia-i')) == 1


def test_duplicate_does_not_reset_authorization(library):
    db, _ = library
    result = ingest(library)
    authorize_document(db, result['document_id'], enabled=True)
    duplicate = ingest(library)
    assert not duplicate['changed']
    assert duplicate['version_id'] == result['version_id']
    assert show_document(db, result['document_id'])['enabled']
    assert len(show_document(db, result['document_id'])['versions']) == 1


def test_new_version_preserves_previous_and_requires_review(library):
    db, source = library
    first = ingest(library)
    authorize_document(db, first['document_id'], enabled=True)
    source.write_text('Nueva versión con contenido distinto.')
    second = ingest(library, document_id=first['document_id'])
    doc = show_document(db, first['document_id'], text=True)
    assert not doc['enabled']
    assert len(doc['versions']) == 2
    assert doc['current_version_id'] == second['version_id']
    old = show_document(db, first['document_id'], text=True, version_id=first['version_id'])
    assert 'Notas ficticias' in old['segments'][0]['text']


def test_failed_new_version_keeps_previous_authorized(library):
    db, source = library
    first = ingest(library)
    authorize_document(db, first['document_id'], enabled=True)
    source.write_bytes(b'\xff')
    second = ingest(library, document_id=first['document_id'])
    assert second['status'] == 'failed'
    doc = show_document(db, first['document_id'])
    assert doc['enabled']
    assert doc['current_version_id'] == first['version_id']
    assert doc['versions'][-1]['error']
    assert list_documents(db)[0]['latest_import_status'] == 'failed'


def test_failed_first_import_is_recorded_and_cannot_be_authorized(library):
    db, source = library
    source.write_bytes(b'')
    result = ingest(library)
    assert result['status'] == 'failed'
    doc = show_document(db, result['document_id'])
    assert doc['current_version_id'] is None
    assert (db.parent / doc['versions'][0]['original_path']).exists()
    with pytest.raises(ValueError, match='versión'):
        authorize_document(db, result['document_id'], enabled=True)


def test_warning_acceptance_is_explicit(library, monkeypatch):
    monkeypatch.setattr('docente_ai.library.ocr.recognize', lambda content, pages: pdf_bytes('Texto reconocido suficiente para revisar', None))
    db, source = library
    source = source.with_suffix('.pdf')
    source.write_bytes(pdf_bytes('Some text', None))
    result = import_document(db, source, category='documental', shared=True)
    with pytest.raises(ValueError, match='avisos'):
        authorize_document(db, result['document_id'], enabled=True)
    authorize_document(db, result['document_id'], enabled=True, accept_warnings=True)
    assert list_documents(db, authorized_only=True)


def test_exclude_keeps_history_and_original(library):
    db, _ = library
    result = ingest(library)
    authorize_document(db, result['document_id'], enabled=True)
    authorize_document(db, result['document_id'], enabled=False)
    assert not list_documents(db, authorized_only=True)
    assert len(show_document(db, result['document_id'])['versions']) == 1


def test_categories_do_not_merge_identical_bytes(library):
    db, source = library
    first = ingest(library)
    second = import_document(db, source, category='documental', shared=True)
    assert first['document_id'] != second['document_id']
    assert len(list_documents(db, category='profesor')) == 1
    assert len(list((db.parent / 'library' / 'originals').iterdir())) == 1
    with pytest.raises(ValueError, match='categoría'):
        import_document(db, source, category='documental', document_id=first['document_id'])


def test_scope_required_and_filtered(library):
    db, source = library
    result = import_document(db, source, category='documental')
    with pytest.raises(ValueError, match='asignatura'):
        authorize_document(db, result['document_id'], enabled=True)
    update_document(db, result['document_id'], shared=True)
    authorize_document(db, result['document_id'], enabled=True)
    assert list_documents(db, subject='historia-i', authorized_only=True)
    with pytest.raises(ValueError, match='inexistente'):
        list_documents(db, subject='missing')


def test_unknown_subject_rolls_back_import(library):
    db, source = library
    with pytest.raises(ValueError, match='inexistente'):
        import_document(db, source, category='profesor', subjects=['missing'])
    assert not list_documents(db)


def test_metadata_update_invalidates_authorization_and_preserves_snapshot(library):
    db, _ = library
    result = ingest(library, values={'title': 'Original', 'authors': ['Autora'], 'year': 2000})
    authorize_document(db, result['document_id'], enabled=True)
    update_document(db, result['document_id'], values={'title': 'Corregido', 'year': None})
    doc = show_document(db, result['document_id'])
    assert not doc['enabled']
    assert doc['metadata']['year'] is None
    assert doc['versions'][0]['metadata_snapshot']['title'] == 'Original'
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT count(*) FROM library_events WHERE action='update'").fetchone()[0] == 1


@pytest.mark.parametrize('values', [{'year': '2000'}, {'year': True}, {'year': -1}, {'doi': 'invented'}, {'url': 'file:///tmp'}, {'authors': 'Someone'}, {'title': ''}])
def test_invalid_metadata(values):
    with pytest.raises(ValueError):
        metadata(values, defaults={'title': 'Known'})


def test_reimport_cannot_silently_change_metadata(library):
    ingest(library)
    with pytest.raises(ValueError, match='library update'):
        ingest(library, values={'title': 'Changed'})


def test_tampered_original_blocks_authorization(library):
    db, _ = library
    result = ingest(library)
    doc = show_document(db, result['document_id'])
    original = db.parent / doc['versions'][0]['original_path']
    original.chmod(0o600)
    original.write_bytes(b'changed')
    with pytest.raises(ValueError, match='falta o ha cambiado'):
        authorize_document(db, result['document_id'], enabled=True)


def test_configuration_replace_preserves_document_associations(library):
    db, _ = library
    result = ingest(library)
    config = load(EXAMPLE)
    config['subjects'][0]['name'] = 'Nombre corregido'
    import_config(db, config, replace=True)
    assert read_config(db)['subjects'][0]['name'] == 'Nombre corregido'
    assert show_document(db, result['document_id'])['subjects'] == ['historia-i']
    config['groups'] = []
    config['schedule_rules'] = []
    config['calendar_exceptions'] = []
    config['group_curricula'] = []
    config['curricula'] = []
    config['curriculum_units'] = []
    config['subjects'] = []
    with pytest.raises(StorageError, match='biblioteca'):
        import_config(db, config, replace=True)
    assert read_config(db)['subjects']


def test_library_can_start_before_teaching_configuration(tmp_path):
    db = tmp_path / 'library.sqlite3'
    source = tmp_path / 'test.txt'
    source.write_text('Synthetic text')
    result = import_document(db, source, category='documental', shared=True)
    authorize_document(db, result['document_id'], enabled=True)
    import_config(db, load(EXAMPLE))
    assert show_document(db, result['document_id'])['enabled']


def test_cli_library_flow(library, capsys):
    db, source = library
    assert main(['library', 'import', str(source), '--db', str(db), '--category', 'profesor', '--subject', 'historia-i', '--json']) == 0
    result = json.loads(capsys.readouterr().out)
    document_id = result['document_id']
    assert main(['library', 'show', document_id, '--db', str(db), '--text', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['segments']
    assert main(['library', 'authorize', document_id, '--db', str(db)]) == 0
    capsys.readouterr()
    assert main(['library', 'list', '--db', str(db), '--authorized-only', '--json']) == 0
    assert len(json.loads(capsys.readouterr().out)) == 1
    assert main(['library', 'update', document_id, '--db', str(db), '--author', 'Profesor de prueba', '--year', '2020']) == 0
    capsys.readouterr()
    assert main(['library', 'update', document_id, '--db', str(db), '--clear', 'year', '--json']) == 0
    capsys.readouterr()
    assert show_document(db, document_id)['metadata']['year'] is None
    assert main(['library', 'exclude', document_id, '--db', str(db)]) == 0


def test_cli_failure_is_visible(library, capsys):
    db, source = library
    source.write_text('')
    assert main(['library', 'import', str(source), '--db', str(db), '--category', 'profesor', '--json']) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'failed'
    assert result['document_id']


def test_v1_migration_preserves_configuration(tmp_path):
    from docente_ai.config import RELATIONS, SCHEMAS
    db = tmp_path / 'v1.sqlite3'
    # Base de fase 2 construida con su esquema real, sin utilizar migrate actual.
    config = load(EXAMPLE)
    with sqlite3.connect(db) as connection:
        connection.execute('CREATE TABLE settings (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        connection.execute('CREATE TABLE config_imports(id INTEGER PRIMARY KEY,imported_at TEXT NOT NULL,sha256 TEXT NOT NULL,snapshot TEXT NOT NULL)')
        for table in SCHEMAS:
            refs = ''.join(f', {key} TEXT NOT NULL REFERENCES {target}(id)' for key, target in RELATIONS.get(table, {}).items())
            connection.execute(f'CREATE TABLE {table}(id TEXT PRIMARY KEY,position INTEGER NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)){refs})')
            for position, row in enumerate(config[table]):
                keys = list(RELATIONS.get(table, {}))
                columns = ['id', 'position', 'payload', *keys]
                connection.execute(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',
                                   [row['id'], position, json.dumps(row), *[row[key] for key in keys]])
        for key in ('schema_version', 'timezone'):
            connection.execute('INSERT INTO settings VALUES (?,?)', (key, json.dumps(config[key])))
        connection.execute('PRAGMA user_version=1')
    assert read_config(db) == config
    source = tmp_path / 'new.txt'
    source.write_text('Synthetic source')
    import_document(db, source, category='documental', subjects=['historia-i'])
    assert read_config(db) == config
    with sqlite3.connect(db) as connection:
        assert connection.execute('PRAGMA user_version').fetchone()[0] == 8


def test_missing_original_prevents_duplicate_success(library):
    db, _ = library
    result = ingest(library)
    doc = show_document(db, result['document_id'])
    (db.parent / doc['versions'][0]['original_path']).unlink()
    with pytest.raises(ValueError, match='falta o ha cambiado'):
        ingest(library)


def test_reject_newer_database_without_changing_it(library):
    db, _ = library
    with sqlite3.connect(db) as connection:
        connection.execute('PRAGMA user_version=99')
    before = db.read_bytes()
    with pytest.raises(StorageError):
        ingest(library)
    assert db.read_bytes() == before


def test_library_updates_never_create_missing_database(tmp_path):
    db = tmp_path / 'absent.sqlite3'
    with pytest.raises(StorageError):
        authorize_document(db, 'missing', enabled=True)
    with pytest.raises(StorageError):
        update_document(db, 'missing', values={'title': 'New'})
    assert not db.exists()
