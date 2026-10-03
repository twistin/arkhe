"""Arranque de contenedor: espacio vacío, configuración mínima sin credenciales."""
import os
from pathlib import Path
import sys
import yaml
from docente_ai.cli import main as cli_main


def main():
    args = sys.argv[1:]
    if args and args[0] == 'serve':
        os.environ['ARKHE_SERVER_MODE'] = '1'
        root = Path(args[args.index('--workspace') + 1])
        folder = root / 'config'
        folder.mkdir(parents=True, exist_ok=True)
        rag = folder / 'rag.yaml'
        if not rag.exists():
            rag.write_text(yaml.safe_dump({'schema_version': 1, 'embeddings': {
                'model': 'bge-m3', 'host': 'http://ollama:11434'}}))
        for name in ('generation', 'pedagogy'):
            path = folder / (name + '.yaml')
            if not path.exists():
                path.write_text(yaml.safe_dump({'schema_version': 1, 'generation': {
                    'provider': 'mistral', 'model': 'mistral-small-latest', 'num_ctx': 65536,
                    'max_output_tokens': 4096, 'base_url': 'https://api.eu.mistral.ai/v1'}}))
    return cli_main(args)


if __name__ == '__main__':
    raise SystemExit(main())
