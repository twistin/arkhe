"""Comandos explícitos de biblioteca; sin búsqueda semántica todavía."""

import argparse
import json
from pathlib import Path

from docente_ai.rag.cli import add_index, run as run_rag

from docente_ai.library.service import (
    FIELDS, LIST_FIELDS, authorize_document, import_document, list_documents,
    show_document, update_document,
)


def add_metadata_options(command):
    command.add_argument('--title')
    command.add_argument('--author', action='append', dest='authors')
    command.add_argument('--year', type=int)
    command.add_argument('--publisher')
    command.add_argument('--doi')
    command.add_argument('--url')
    command.add_argument('--type', dest='document_type')
    command.add_argument('--tag', action='append', dest='tags')
    command.add_argument('--collection', action='append', dest='collections')
    command.add_argument('--origin')
    subjects = command.add_mutually_exclusive_group()
    subjects.add_argument('--subject', action='append', dest='subjects')
    subjects.add_argument('--clear-subjects', action='store_true')
    command.add_argument('--shared', action=argparse.BooleanOptionalAction, default=None,
                         help='Fuente compartida entre asignaturas; no se activa por defecto.')


def add_commands(commands):
    library = commands.add_parser('library', help='Importar y revisar la biblioteca local.')
    sub = library.add_subparsers(dest='action', required=True)
    add_index(sub)
    for action in ('import', 'list', 'show', 'update', 'authorize', 'exclude'):
        command = sub.add_parser(action)
        command.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
        command.add_argument('--json', action='store_true', dest='as_json')
        if action in {'show', 'update', 'authorize', 'exclude'}:
            command.add_argument('document_id')
        if action == 'import':
            command.add_argument('file', type=Path)
            command.add_argument('--category', choices=['documental', 'profesor'], required=True)
            command.add_argument('--document-id', help='Añadir una versión a este documento existente.')
            command.add_argument('--max-mb', type=int, default=100)
            add_metadata_options(command)
        elif action == 'list':
            command.add_argument('--subject')
            command.add_argument('--category', choices=['documental', 'profesor'])
            command.add_argument('--authorized-only', action='store_true')
        elif action == 'show':
            command.add_argument('--text', action='store_true', help='Mostrar extracción y localizadores.')
            command.add_argument('--version-id', help='Inspeccionar una versión anterior.')
        elif action == 'update':
            add_metadata_options(command)
            command.add_argument('--clear', action='append', choices=sorted(FIELDS - {'title'}), default=[],
                                 help='Retirar un metadato. Repetible; no se permite retirar el título.')
        elif action == 'authorize':
            command.add_argument('--accept-warnings', action='store_true')


def metadata_values(args):
    values = {key: getattr(args, key) for key in FIELDS if getattr(args, key, None) is not None}
    for key in getattr(args, 'clear', []):
        if key in values:
            raise ValueError(f'No puedes definir y borrar {key} en el mismo comando.')
        values[key] = [] if key in LIST_FIELDS else None
    return values


def run(args):
    if args.action == 'index':
        return run_rag(args)
    if args.action == 'import':
        result = import_document(args.db, args.file, category=args.category,
                                 values=metadata_values(args), subjects=[] if args.clear_subjects else args.subjects,
                                 shared=args.shared, document_id=args.document_id, max_mb=args.max_mb)
    elif args.action == 'list':
        result = list_documents(args.db, subject=args.subject, category=args.category, authorized_only=args.authorized_only)
    elif args.action == 'show':
        result = show_document(args.db, args.document_id, text=args.text, version_id=args.version_id)
    elif args.action == 'update':
        result = update_document(args.db, args.document_id, values=metadata_values(args),
                                 subjects=[] if args.clear_subjects else args.subjects, shared=args.shared)
    else:
        result = authorize_document(args.db, args.document_id, enabled=args.action == 'authorize',
                                    accept_warnings=getattr(args, 'accept_warnings', False))
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == 'list':
        if not result:
            print('No hay documentos que coincidan.')
        for item in result:
            state = 'autorizado' if item['enabled'] else 'no autorizado'
            print(f"{item['id']} · {item['metadata']['title']} · {item['category']} · {state} · última importación: {item['latest_import_status']}")
    elif args.action == 'show':
        print(f"{result['id']} · {result['metadata']['title']} · {result['category']}")
        print(f"Autorizado: {'sí' if result['enabled'] else 'no'} · Compartido: {'sí' if result['shared'] else 'no'}")
        print(f"Asignaturas: {', '.join(result['subjects']) or 'sin asignar'}")
        print(json.dumps(result['metadata'], ensure_ascii=False, indent=2))
        for version in result['versions']:
            marker = ' [actual]' if version['id'] == result['current_version_id'] else ''
            print(f"Versión {version['id']}{marker}: {version['status']} · {version['sha256']}")
            if version['error']:
                print(f"Error: {version['error']}")
            for warning in version['warnings']:
                print(f'Aviso: {warning}')
        for segment in result.get('segments', []):
            locator = segment['locator']
            location = f"Página {locator['pdf_page_index']} del archivo PDF" if locator['kind'] == 'pdf_page' else f"Líneas {locator['line_start']}–{locator['line_end']}"
            print(f"\n[{segment['id']}] {location}\n{segment['text']}")
    else:
        print(result['message'])
        print(f"Documento: {result['document_id']}")
        if 'version_id' in result:
            print(f"Versión: {result['version_id']} · {result['status']}")
        for warning in result.get('warnings', []):
            print(f'Aviso: {warning}')
    return 1 if isinstance(result, dict) and result.get('status') == 'failed' else 0
