"""Copia offline consistente y restauración a un espacio nuevo, nunca sobre datos existentes."""
import argparse
from datetime import date, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tarfile
import tempfile

import sqlite_vec
import yaml


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_config(value):
    if isinstance(value, dict):
        if 'api_key' in value: raise ValueError('No se admite api_key en una copia de configuración.')
        for item in value.values(): verify_config(item)
    elif isinstance(value, list):
        for item in value: verify_config(item)


def create(workspace, directory, today=None):
    """El servicio debe estar detenido para sincronizar SQLite con los documentos."""
    root, directory = Path(workspace).resolve(), Path(directory).resolve()
    if directory.is_relative_to(root): raise ValueError('Las copias deben estar fuera del workspace.')
    database = root / 'data/docente.sqlite3'
    if not database.is_file() or database.is_symlink():
        raise ValueError('No hay una base regular que copiar; no se crea una base vacía.')
    today = today or date.today()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        snapshot = Path(temporary) / 'docente.sqlite3'
        subprocess.run(['sqlite3', str(root / 'data/docente.sqlite3'), '.backup ' + str(snapshot)],
                       check=True, capture_output=True)
        files = {'data/docente.sqlite3': snapshot}
        for name in ('data/library', 'Conocimiento', 'config'):
            source = root / name
            if source.is_symlink(): raise ValueError('No se copian enlaces simbólicos.')
            for path in sorted(source.rglob('*')):
                if path.is_symlink(): raise ValueError('No se copian enlaces simbólicos.')
                if path.is_file():
                    if name == 'config': verify_config(yaml.safe_load(path.read_text()))
                    files[path.relative_to(root).as_posix()] = path
        manifest = {'version': 1, 'date': today.isoformat(), 'files': {name: digest(path) for name, path in files.items()}}
        target = directory / ('arkhe-' + today.isoformat() + '.tar.gz')
        pending = directory / ('.' + target.name + '.tmp')
        try:
            with pending.open('wb') as output:
                os.chmod(pending, 0o600)
                with tarfile.open(fileobj=output, mode='w:gz') as archive:
                    for name, path in files.items(): archive.add(path, arcname=name, recursive=False)
                    content = json.dumps(manifest).encode()
                    member = tarfile.TarInfo('manifest.json')
                    member.size, member.mode = len(content), 0o600
                    archive.addfile(member, io.BytesIO(content))
            os.replace(pending, target)
        finally:
            pending.unlink(missing_ok=True)
    for path in directory.glob('arkhe-????-??-??.tar.gz'):
        if date.fromisoformat(path.name[6:16]) < today - timedelta(days=13): path.unlink()
    return target


def restore(archive_path, workspace):
    target = Path(workspace).resolve()
    if target.exists() and any(target.iterdir()):
        raise ValueError('Restaurar requiere un workspace nuevo y vacío.')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        staging = Path(temporary)
        with tarfile.open(archive_path, 'r:gz') as archive:
            members = archive.getmembers()
            names = set()
            if sum(member.size for member in members) > 20 * 1024**3:
                raise ValueError('Copia demasiado grande.')
            for member in members:
                name = member.name
                if name in names or not member.isfile() or Path(name).is_absolute() or '..' in Path(name).parts:
                    raise ValueError('Copia insegura o duplicada.')
                names.add(name)
                if name != 'manifest.json' and not (name == 'data/docente.sqlite3' or
                        name.startswith(('data/library/', 'Conocimiento/', 'config/'))):
                    raise ValueError('Contenido no permitido en la copia.')
                path = staging / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, path.open('xb') as output:
                    while chunk := source.read(1024 * 1024): output.write(chunk)
                os.chmod(path, 0o600)
        manifest = json.loads((staging / 'manifest.json').read_text())
        if manifest.get('version') != 1 or set(manifest['files']) != names - {'manifest.json'}:
            raise ValueError('Manifest de copia inválido.')
        for name, expected in manifest['files'].items():
            if digest(staging / name) != expected: raise ValueError('Checksum incorrecto en la copia.')
        for path in (staging / 'config').rglob('*'):
            if path.is_file(): verify_config(yaml.safe_load(path.read_text()))
        with sqlite3.connect(staging / 'data/docente.sqlite3') as connection:
            connection.enable_load_extension(True)
            sqlite_vec.load(connection)
            connection.enable_load_extension(False)
            if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Base restaurada no íntegra.')
        (staging / 'manifest.json').unlink()
        if target.exists(): target.rmdir()
        os.replace(staging, target)
    return target


def restore_volume(archive_path, workspace):
    """Un punto de montaje no se puede renombrar; publicar solo en un volumen vacío."""
    target = Path(workspace).resolve()
    if not target.is_dir() or any(target.iterdir()):
        raise ValueError('El volumen debe existir y estar vacío.')
    staged = restore(archive_path, target / '.restauracion')
    for child in staged.iterdir():
        os.replace(child, target / child.name)
    staged.rmdir()
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    backup = commands.add_parser('create')
    backup.add_argument('--workspace', type=Path, required=True)
    backup.add_argument('--backup-dir', type=Path, required=True)
    restoration = commands.add_parser('restore')
    restoration.add_argument('--workspace', type=Path, required=True)
    restoration.add_argument('--archive', type=Path, required=True)
    restoration.add_argument('--volume-root', action='store_true', help='Restaurar en la raíz de un volumen vacío.')
    args = parser.parse_args(argv)
    if args.action == 'create':
        result = create(args.workspace, args.backup_dir)
    else:
        restoration = restore_volume if args.volume_root else restore
        result = restoration(args.archive, args.workspace)
    print(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
