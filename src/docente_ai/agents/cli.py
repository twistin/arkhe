"""Invocación explícita del rol pedagógico con selección opcional de sesión del calendario."""

from datetime import date
from pathlib import Path

from docente_ai.agents.pedagogy import context_for
from docente_ai.generation.cli import add_ask_options, present, validate_output
from docente_ai.generation.service import ask
from docente_ai.generation.settings import load_settings
from docente_ai.rag.settings import load_settings as load_rag_settings


def add_commands(commands):
    command = commands.add_parser('pedagogy', help='Proponer una sesión como borrador pedagógico fundamentado.')
    command.add_argument('question', help='Tema elegido por el profesor.')
    command.add_argument('--group', required=True)
    command.add_argument('--duration', required=True, type=int, help='Minutos de la sesión, entre 5 y 240.')
    command.add_argument('--unit', help='Unidad elegida de la programación del grupo.')
    command.add_argument('--criteria', default='', help='Indicaciones pedagógicas del profesor.')
    command.add_argument('--session', type=date.fromisoformat, metavar='YYYY-MM-DD',
                         help='Fecha de la sesión en el calendario del grupo (opcional).')
    add_ask_options(command)
    command.set_defaults(generation_config=Path('config/pedagogy.yaml'))


def run(args):
    validate_output(args.output, args.db)
    context = context_for(args.db, args.group, args.duration, unit_id=args.unit, criteria=args.criteria,
                          session_date=getattr(args, 'session', None))
    result = ask(args.db, load_rag_settings(args.rag_config), load_settings(args.generation_config),
                 args.question, subject=context['group']['subject_id'], category=args.category,
                 document_ids=args.document_ids, top_k=args.top_k, max_distance=args.max_distance,
                 pedagogy_context=context)
    return present(result, args)
