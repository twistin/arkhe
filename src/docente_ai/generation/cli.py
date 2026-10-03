"""Preguntas documentadas e historial; no es todavía prepare class."""

import json
from pathlib import Path

from docente_ai.generation.render import render
from docente_ai.generation.service import ask, edit_run, get_run, list_runs, review_run
from docente_ai.generation.settings import load_settings
from docente_ai.rag.settings import load_settings as load_rag_settings


def add_commands(commands):
    command = commands.add_parser('ask', help='Generar un borrador documentado con Ollama local.')
    command.add_argument('question')
    command.add_argument('--subject', required=True)
    add_ask_options(command)
    history = commands.add_parser('generation', help='Consultar y revisar registros generativos locales.')
    subcommands = history.add_subparsers(dest='action', required=True)
    for action in ('list', 'show', 'approve', 'reject', 'edit'):
        command = subcommands.add_parser(action)
        command.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
        command.add_argument('--json', action='store_true', dest='as_json')
        if action in ('show', 'approve', 'reject', 'edit'):
            command.add_argument('run_id')
        if action == 'show':
            command.add_argument('--output', type=Path)
        if action in ('approve', 'reject'):
            command.add_argument('--notes', default='', help='Notas del profesor (hasta 2000 caracteres).')
        if action == 'edit':
            command.add_argument('--output', type=Path)
            command.add_argument('--objectives', nargs='+', help='Nueva lista de objetivos.')
            command.add_argument('--difficulty', help='Nueva descripción de dificultad.')
            command.add_argument('--observations', help='Nuevas observaciones del plan.')


def add_ask_options(command):
    command.add_argument('--category', choices=['documental', 'profesor', 'all'], default='documental')
    command.add_argument('--document', action='append', dest='document_ids')
    command.add_argument('--top-k', type=int, default=6)
    command.add_argument('--max-distance', type=float)
    command.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    command.add_argument('--rag-config', type=Path, default=Path('config/rag.yaml'))
    command.add_argument('--generation-config', type=Path, default=Path('config/generation.yaml'))
    command.add_argument('--json', action='store_true', dest='as_json')
    command.add_argument('--output', type=Path, help='Exportar Markdown a un archivo nuevo, sin sobrescribir.')


def validate_output(path, db):
    if path is None:
        return
    if path.exists():
        raise ValueError('El archivo de salida ya existe; elige otro nombre.')
    if path.suffix.lower() != '.md' or not path.parent.is_dir():
        raise ValueError('La salida debe ser un archivo .md dentro de un directorio existente.')
    if path.resolve().is_relative_to(db.resolve().parent / 'library'):
        raise ValueError('Guarda las generaciones fuera de la biblioteca de fuentes.')


def run(args):
    if args.command == 'generation' and args.action == 'list':
        result = list_runs(args.db)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if not result:
                print('No hay registros generativos.')
            for item in result:
                print(f"{item['id']} · {item['created_at']} · {item['status']} · {item['model'] or 'sin generación'}")
        return 0
    if args.command == 'generation' and args.action in ('approve', 'reject'):
        result = review_run(args.db, args.run_id, action=args.action, notes=args.notes)
        label = 'aprobada' if args.action == 'approved' else 'rechazada'
        if args.as_json:
            print(json.dumps({'ok': True, 'action': args.action, 'run_id': result['id'],
                              'reviewed_at': result['review']['reviewed_at']}, ensure_ascii=False, indent=2))
        else:
            print(f"Propuesta {label}: {result['id']} · {result['review']['reviewed_at']}")
            if args.notes:
                print(f"Notas: {args.notes}")
        return 0
    if args.command == 'generation' and args.action == 'edit':
        patch = {}
        if args.objectives:
            patch['objectives'] = args.objectives
        if args.difficulty:
            patch['difficulty'] = args.difficulty
        if args.observations:
            patch['observations'] = args.observations
        if not patch:
            raise ValueError('Indica al menos un campo a editar (--objectives, --difficulty, --observations).')
        validate_output(getattr(args, 'output', None), args.db)
        result = edit_run(args.db, args.run_id, plan_patch=patch)
        return present(result, args)
    validate_output(getattr(args, 'output', None), args.db)
    if args.command == 'ask':
        result = ask(args.db, load_rag_settings(args.rag_config), load_settings(args.generation_config),
                     args.question, subject=args.subject, category=args.category,
                     document_ids=args.document_ids, top_k=args.top_k, max_distance=args.max_distance)
    else:
        result = get_run(args.db, args.run_id)
    return present(result, args)


def present(result, args):
    markdown = render(result)
    if getattr(args, 'output', None):
        try:
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(markdown)
        except OSError as exc:
            raise ValueError(f"El registro {result['id']} está guardado, pero no se pudo exportar: {exc}") from exc
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(markdown, end='')
    return 1 if result['status'] in ('failed', 'cancelled', 'running') else 0
