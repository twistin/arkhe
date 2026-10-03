"""Restauración real de copias sintéticas y rechazo de archivos hostiles."""
from datetime import date
import io
from pathlib import Path
import sqlite3
import tarfile
import pytest
from docente_ai.web.backup import create, restore, main


def corpus(root):
    (root / 'data/library/originals').mkdir(parents=True)
    with sqlite3.connect(root / 'data/docente.sqlite3') as connection:
        connection.execute('CREATE TABLE ejemplo(texto TEXT)')
        connection.execute("INSERT INTO ejemplo VALUES ('fuente sintética')")
    (root / 'data/library/originals/fuente.txt').write_text('Texto original')
    (root / 'Conocimiento').mkdir()
    (root / 'Conocimiento/apuntes.txt').write_text('Apuntes sintéticos')
    (root / 'config').mkdir()
    (root / 'config/rag.yaml').write_text('schema_version: 1\nembeddings:\n  model: bge-m3\n')


def test_backup_y_script_restauracion_roundtrip(tmp_path):
    original, restored, backups = tmp_path / 'original', tmp_path / 'restaurado', tmp_path / 'copias'
    corpus(original)
    copy = create(original, backups, date(2026, 10, 3))
    assert main(['restore', '--workspace', str(restored), '--archive', str(copy)]) == 0
    with sqlite3.connect(restored / 'data/docente.sqlite3') as connection:
        assert connection.execute('SELECT texto FROM ejemplo').fetchone()[0] == 'fuente sintética'
    assert (restored / 'Conocimiento/apuntes.txt').read_text() == 'Apuntes sintéticos'
    assert (restored / 'data/library/originals/fuente.txt').read_text() == 'Texto original'
    with pytest.raises(ValueError): restore(copy, restored)
    assert copy.stat().st_mode & 0o777 == 0o600


def test_rotacion_14_dias_y_no_incluye_claves(tmp_path):
    root, backups = tmp_path / 'original', tmp_path / 'copias'
    corpus(root)
    older = create(root, backups, date(2026, 9, 19))
    recent = create(root, backups, date(2026, 9, 20))
    create(root, backups, date(2026, 10, 3))
    assert not older.exists() and recent.exists()
    (root / 'config/generation.yaml').write_text('generation:\n  api_key: secreto\n')
    with pytest.raises(ValueError): create(root, backups)


@pytest.mark.parametrize('name,link', [('../../fuera', False), ('Conocimiento/enlace', True)])
def test_restore_rechaza_rutas_y_enlaces(tmp_path, name, link):
    archive = tmp_path / 'hostil.tar.gz'
    with tarfile.open(archive, 'w:gz') as output:
        member = tarfile.TarInfo(name)
        if link: member.type, member.linkname = tarfile.SYMTYPE, '/etc/passwd'
        else: member.size = 3
        output.addfile(member, None if link else io.BytesIO(b'bad'))
    with pytest.raises(ValueError): restore(archive, tmp_path / 'nuevo')
    assert not (tmp_path / 'nuevo').exists()


def test_backup_no_crea_base_ausente(tmp_path):
    root = tmp_path / 'vacio'
    root.mkdir()
    with pytest.raises(ValueError): create(root, tmp_path / 'copias')
    assert not (root / 'data/docente.sqlite3').exists()


def test_restauracion_raiz_de_volumen_vacio(tmp_path):
    root, volume = tmp_path / 'original', tmp_path / 'volumen'
    corpus(root)
    copy = create(root, tmp_path / 'copias')
    volume.mkdir()
    assert main(['restore', '--workspace', str(volume), '--archive', str(copy), '--volume-root']) == 0
    assert (volume / 'data/docente.sqlite3').is_file()
    assert not (volume / '.restauracion').exists()
    with pytest.raises(ValueError):
        main(['restore', '--workspace', str(volume), '--archive', str(copy), '--volume-root'])
