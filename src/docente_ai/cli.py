"""Interfaz de línea de comandos y lanzador gráfico local."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from docente_ai import __version__
from docente_ai.agents.cli import add_commands as add_pedagogy_commands, run as run_pedagogy
from docente_ai.generation.cli import add_commands as add_generation_commands, run as run_generation
from docente_ai.rag.cli import add_search, run as run_rag
from docente_ai.teaching.cli import add_commands, run
from docente_ai.library.cli import add_commands as add_library_commands, run as run_library
from docente_ai.record.cli import add_commands as add_record_commands, run as run_record
from docente_ai.doctor import DEFAULT_HOST, diagnose, local_url, positive_timeout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="docente-ai", description="ENJAMBRE IA DOCENTE LOCAL",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")
    doctor = commands.add_parser("doctor", help="Diagnosticar Python, SQLite y Ollama sin modificar datos.")
    doctor.add_argument("--offline", action="store_true", help="No consultar Ollama ni realizar peticiones HTTP.")
    doctor.add_argument("--json", action="store_true", dest="as_json", help="Mostrar diagnóstico estructurado.")
    doctor.add_argument("--ollama-host", type=local_url, default=DEFAULT_HOST, help="URL HTTP de loopback de Ollama.")
    doctor.add_argument("--timeout", type=positive_timeout, default=3.0, help="Timeout HTTP por operación, en segundos (0 < valor <= 30).")
    add_commands(commands)
    add_library_commands(commands)
    add_search(commands)
    add_generation_commands(commands)
    add_pedagogy_commands(commands)
    add_record_commands(commands)
    web = commands.add_parser('ui', help='Abrir la interfaz gráfica local de Enjambre.')
    web.add_argument('--host', type=str, default='127.0.0.1', help='Dirección IP de escucha (ej. 127.0.0.1 o 0.0.0.0 para Tailscale / red local).')
    web.add_argument('--port', type=int, default=8765)
    web.add_argument('--no-browser', action='store_true')
    web.add_argument('--workspace', type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command != "doctor":
        try:
            if args.command == 'ui':
                from docente_ai.web.launch import launch
                return launch(args)
            if args.command == "pedagogy":
                return run_pedagogy(args)
            if args.command in ("ask", "generation", "runs"):
                return run_generation(args)
            if args.command == "search":
                return run_rag(args)
            if args.command == "record":
                return run_record(args)
            return run_library(args) if args.command == "library" else run(args)
        except (ValueError, OSError, sqlite3.Error) as exc:
            if getattr(args, "as_json", False):
                print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
            else:
                print(f"Error: {exc}", file=sys.stderr)
            return 1
        except KeyboardInterrupt as exc:
            print(str(exc) or "Operación cancelada.", file=sys.stderr)
            return 130
    try:
        checks = diagnose(host=args.ollama_host, timeout=args.timeout, offline=args.offline)
    except KeyboardInterrupt:
        print("Diagnóstico cancelado.")
        return 130
    success = all(check.status != "error" for check in checks)
    if args.as_json:
        print(json.dumps({"ok": success, "checks": [check.to_dict() for check in checks]}, ensure_ascii=False, indent=2))
    else:
        labels = {"ok": "OK", "warning": "AVISO", "error": "ERROR", "skipped": "OMITIDO"}
        for check in checks:
            print(f"[{labels[check.status]}] {check.name}: {check.detail}")
    return 0 if success else 1
