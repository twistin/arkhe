"""CLI de registro de impartición: el profesor anota lo que realmente ocurrió."""

from datetime import date
import json
from pathlib import Path

from docente_ai.record.service import (
    add_feedback, add_progress, add_record, get_record, list_records,
)


def add_commands(commands):
    record = commands.add_parser('record', help='Registrar clases impartidas y feedback.')
    sub = record.add_subparsers(dest='action', required=True)

    # record add
    cmd_add = sub.add_parser('add', help='Registrar una sesión impartida.')
    cmd_add.add_argument('--group', required=True, help='ID del grupo.')
    cmd_add.add_argument('--date', required=True, type=date.fromisoformat, metavar='YYYY-MM-DD')
    cmd_add.add_argument('--duration', required=True, type=int, help='Duración real en minutos.')
    cmd_add.add_argument('--topic', required=True, help='Qué se impartió realmente.')
    cmd_add.add_argument('--run', dest='run_id', default=None, help='ID de la propuesta usada (opcional).')
    cmd_add.add_argument('--notes', default='', help='Notas libres sobre la sesión.')
    cmd_add.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    cmd_add.add_argument('--json', action='store_true', dest='as_json')

    # record progress
    cmd_prog = sub.add_parser('progress', help='Confirmar avance de una unidad de programación.')
    cmd_prog.add_argument('record_id', help='ID del registro de sesión.')
    cmd_prog.add_argument('--unit', required=True, help='ID de la unidad que avanzó.')
    cmd_prog.add_argument('--note', default='', help='Nota sobre el progreso.')
    cmd_prog.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    cmd_prog.add_argument('--json', action='store_true', dest='as_json')

    # record feedback
    cmd_fb = sub.add_parser('feedback', help='Añadir feedback sobre la sesión.')
    cmd_fb.add_argument('record_id', help='ID del registro de sesión.')
    cmd_fb.add_argument('--worked', dest='what_worked', default='', help='Qué funcionó bien.')
    cmd_fb.add_argument('--failed', dest='what_failed', default='', help='Qué no funcionó.')
    cmd_fb.add_argument('--next', dest='next_session_note', default='', help='Notas para la siguiente sesión.')
    cmd_fb.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    cmd_fb.add_argument('--json', action='store_true', dest='as_json')

    # record list
    cmd_list = sub.add_parser('list', help='Listar sesiones registradas de un grupo.')
    cmd_list.add_argument('--group', required=True)
    cmd_list.add_argument('--limit', type=int, default=10)
    cmd_list.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    cmd_list.add_argument('--json', action='store_true', dest='as_json')

    # record show
    cmd_show = sub.add_parser('show', help='Ver un registro de sesión completo.')
    cmd_show.add_argument('record_id')
    cmd_show.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    cmd_show.add_argument('--json', action='store_true', dest='as_json')


def run(args) -> int:
    if args.action == 'add':
        result = add_record(args.db, args.group, args.date, args.duration, args.topic,
                            run_id=args.run_id, notes=args.notes)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Sesión registrada: {result['id']} · {result['session_date']} · {result['topic'][:60]}")
        return 0

    if args.action == 'progress':
        result = add_progress(args.db, args.record_id, args.unit, note=args.note)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            units = ', '.join(p['unit_id'] for p in result['progress'])
            print(f"Progreso registrado en {result['id']}. Unidades: {units or 'ninguna'}.")
        return 0

    if args.action == 'feedback':
        result = add_feedback(args.db, args.record_id, what_worked=args.what_worked,
                              what_failed=args.what_failed, next_session_note=args.next_session_note)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Feedback guardado en {result['id']}.")
        return 0

    if args.action == 'list':
        items = list_records(args.db, args.group, limit=args.limit)
        if args.as_json:
            print(json.dumps(items, ensure_ascii=False, indent=2))
        elif not items:
            print('No hay sesiones registradas para este grupo.')
        else:
            for item in items:
                print(f"{item['session_date']} · {item['duration_minutes']} min · {item['topic'][:60]} [{item['id']}]")
        return 0

    # show
    result = get_record(args.db, args.record_id)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        fb = result.get('feedback') or {}
        print(f"{result['session_date']} · {result['duration_minutes']} min · {result['topic']}")
        if result['notes']:
            print(f"Notas: {result['notes']}")
        if result['progress']:
            print(f"Unidades: {', '.join(p['unit_id'] for p in result['progress'])}")
        if fb:
            if fb.get('what_worked'):
                print(f"✓ {fb['what_worked']}")
            if fb.get('what_failed'):
                print(f"✗ {fb['what_failed']}")
            if fb.get('next_session_note'):
                print(f"→ {fb['next_session_note']}")
    return 0
