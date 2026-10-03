"""Comandos docentes de fase 2."""

import argparse
import json
from pathlib import Path

import yaml

from docente_ai.config import load, iso_date
from docente_ai.storage import import_config, read_config
from docente_ai.teaching.calendar import sessions
from docente_ai.teaching.curriculum import show_curriculum


def add_commands(commands):
    config = commands.add_parser('config', help='Validar, importar o exportar configuración docente YAML.')
    sub = config.add_subparsers(dest='action', required=True)
    for action in ('validate', 'import', 'export'):
        command = sub.add_parser(action)
        if action != 'export':
            command.add_argument('file', type=Path)
        if action != 'validate':
            command.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
        if action == 'import':
            command.add_argument('--replace', action='store_true', help='Sustituir toda la configuración docente conservando instantánea.')
        if action == 'export':
            command.add_argument('--output', type=Path, help='Archivo nuevo; sin esta opción se imprime YAML.')
        else:
            command.add_argument('--json', action='store_true', dest='as_json')
    calendar = commands.add_parser('calendar', help='Consultar sesiones previstas.')
    listing = calendar.add_subparsers(dest='action', required=True).add_parser('list')
    listing.add_argument('--from', dest='start', type=lambda s: iso_date(s, '--from'), required=True)
    listing.add_argument('--to', dest='end', type=lambda s: iso_date(s, '--to'), required=True)
    listing.add_argument('--group')
    listing.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    listing.add_argument('--json', action='store_true', dest='as_json')
    curriculum = commands.add_parser('curriculum', help='Consultar programación y temporalización.')
    show = curriculum.add_subparsers(dest='action', required=True).add_parser('show')
    show.add_argument('--group', required=True)
    show.add_argument('--date', type=lambda s: iso_date(s, '--date'))
    show.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    show.add_argument('--json', action='store_true', dest='as_json')


def run(args: argparse.Namespace) -> int:
    if args.command == 'config':
        if args.action == 'validate':
            data = load(args.file)
            result = {'valid': True, 'groups': len(data['groups']), 'subjects': len(data['subjects']), 'message': 'Configuración válida.'}
        elif args.action == 'import':
            result = import_config(args.db, load(args.file), replace=args.replace)
        else:
            output = yaml.safe_dump(read_config(args.db), allow_unicode=True, sort_keys=False)
            if args.output:
                # Evitar sobrescrituras accidentales, incluida la propia base.
                with args.output.open('x', encoding='utf-8') as stream:
                    stream.write(output)
                print(f'Configuración exportada a {args.output}.')
            else:
                print(output, end='')
            return 0
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result['message'])
        return 0
    data = read_config(args.db)
    if args.command == 'calendar':
        result = sessions(data, args.start, args.end, args.group)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif not result:
            print('No hay sesiones previstas en ese intervalo.')
        else:
            for item in result:
                print(f"{item['start']} — {item['subject']} · {item['group']} · {item['duration_minutes']} min · aula {item['room'] or 'sin indicar'} [{item['id']}]")
    else:
        result = show_curriculum(data, args.group, args.date)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result['note'])
            if result['curriculum']:
                print(result['curriculum']['name'])
            for unit in result['units']:
                marker = ' (sugerida por fecha)' if unit['id'] in result['suggested_units'] else ''
                print(f"{unit['order']}. {unit['title']}{marker}")
                labels = {'objectives': 'Objetivos', 'contents': 'Contenidos', 'competencies': 'Competencias', 'assessment_criteria': 'Criterios de evaluación', 'activities': 'Actividades', 'repertoire': 'Repertorio', 'resources': 'Recursos'}
                for field in labels:
                    if unit.get(field):
                        print(f"  {labels[field]}: {'; '.join(unit[field])}")
    return 0
