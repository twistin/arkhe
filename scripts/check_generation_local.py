"""Prueba manual de generación real; corpus sintético y base temporal."""

import argparse
import json
from pathlib import Path
import tempfile
import time

from docente_ai.config import load
from docente_ai.generation.render import render
from docente_ai.generation.service import ask, get_run
from docente_ai.generation.settings import load_settings as load_generation
from docente_ai.library.service import import_document, authorize_document
from docente_ai.rag.ollama import OllamaEmbedder
from docente_ai.rag.service import index_library
from docente_ai.rag.settings import load_settings as load_rag
from docente_ai.storage import import_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rag-config', type=Path, default=Path('config/rag.yaml'))
    parser.add_argument('--generation-config', type=Path, default=Path('config/generation.yaml'))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    rag, generation = load_rag(args.rag_config), load_generation(args.generation_config)
    report = {'model': generation.model, 'corpus': 'Texto sintético local; ninguna biblioteca personal', 'checks': []}
    with tempfile.TemporaryDirectory(prefix='docente-generation-') as directory:
        root = Path(directory)
        db = root / 'docente.sqlite3'
        import_config(db, load(Path(__file__).resolve().parents[1] / 'config/teaching.example.yaml'))
        source = root / 'pulso.txt'
        source.write_text('El pulso es una referencia temporal regular para organizar el ritmo. En esta actividad sintética, el grupo marca el pulso con palmas y después intercala silencios sin perder la regularidad.', encoding='utf-8')
        doc = import_document(db, source, category='documental', subjects=['historia-i'], values={'title': 'Ejemplo sintético sobre el pulso'})
        authorize_document(db, doc['document_id'], enabled=True)
        with OllamaEmbedder(rag) as embedder:
            index_library(db, rag, embedder)
        for question, expected in [
            ('Según la fuente, ¿qué es el pulso y cómo lo practica el grupo?', 'draft'),
            ('¿Qué temperatura exacta hace ahora mismo en el aula?', 'abstained'),
        ]:
            start = time.perf_counter()
            result = ask(db, rag, generation, question, subject='historia-i')
            report['checks'].append({'question': question, 'expected': expected, 'status': result['status'],
                                     'seconds': round(time.perf_counter() - start, 3), 'metrics': result['metrics'],
                                     'digest': result['digest'], 'markdown': render(result)})
            assert get_run(db, result['id'])['result'] == result['result']
            print(f"{result['status']} · {report['checks'][-1]['seconds']} s", flush=True)
        authorize_document(db, doc['document_id'], enabled=False)
        result = ask(db, rag, generation, '¿Qué es el pulso?', subject='historia-i')
        report['excluded_abstains_without_generation'] = result['status'] == 'abstained' and result['model'] is None
    report['passed'] = all(item['expected'] == item['status'] for item in report['checks']) and report['excluded_abstains_without_generation']
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    print(serialized)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized + '\n', encoding='utf-8')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
