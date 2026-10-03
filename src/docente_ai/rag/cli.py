"""Indexación y búsqueda; seleccionar un perfil explícito antes de usar Ollama."""

import json
from pathlib import Path

from docente_ai.rag.ollama import OllamaEmbedder
from docente_ai.rag.service import index_library, search
from docente_ai.rag.settings import load_settings


def add_options(parser):
    parser.add_argument('--db', type=Path, default=Path('data/docente.sqlite3'))
    parser.add_argument('--rag-config', type=Path, default=Path('config/rag.yaml'))
    parser.add_argument('--document', action='append', dest='document_ids', help='Restringir a estos IDs de documento; repetible.')
    parser.add_argument('--json', action='store_true', dest='as_json')


def add_index(subcommands):
    parser = subcommands.add_parser('index', help='Indexar versiones vigentes y autorizadas con Ollama local.')
    add_options(parser)
    parser.add_argument('--subject', help='Restringir la indexación a una asignatura.')


def add_search(commands):
    parser = commands.add_parser('search', help='Buscar fragmentos autorizados de una asignatura.')
    parser.add_argument('query')
    add_options(parser)
    parser.add_argument('--subject', required=True)
    parser.add_argument('--category', choices=['documental', 'profesor', 'all'], default='documental')
    parser.add_argument('--top-k', type=int, default=6)
    parser.add_argument('--max-distance', type=float, help='Umbral opcional de distancia coseno 0–2; requiere calibración.')


def run(args):
    settings = load_settings(args.rag_config)
    with OllamaEmbedder(settings) as embedder:
        if args.command == 'library':
            result = index_library(args.db, settings, embedder, subject=args.subject, document_ids=args.document_ids)
        else:
            result = search(args.db, settings, embedder, args.query, subject=args.subject,
                            category=args.category, document_ids=args.document_ids,
                            top_k=args.top_k, max_distance=args.max_distance)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result['message'])
        if args.command == 'library':
            print(f"Versiones indexadas: {result['indexed_versions']} · ya indexadas: {result['skipped_versions']} · fragmentos nuevos: {result['chunks']}")
        else:
            for item in result['results']:
                label = 'Fuente documental' if item['category'] == 'documental' else 'Material del profesor'
                print(f"\n[{item['chunk_id']}] {label} · distancia {item['distance']:.4f}")
                print(item['citation'])
                print(item['text'])
    return 0
