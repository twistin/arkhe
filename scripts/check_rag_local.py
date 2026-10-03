"""Prueba manual reproducible de Ollama real; no forma parte de pytest offline.

Ejecutar desde el proyecto: uv run python scripts/check_rag_local.py
Solo utiliza documentos sintéticos en un directorio temporal.
"""

import argparse
import json
from pathlib import Path
import tempfile
import time

from docente_ai.config import load
from docente_ai.library.service import import_document, authorize_document
from docente_ai.rag.ollama import OllamaEmbedder
from docente_ai.rag.service import index_library, search
from docente_ai.rag.settings import load_settings
from docente_ai.storage import import_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rag-config', type=Path, default=Path('config/rag.yaml'))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    settings = load_settings(args.rag_config)
    fixtures = {
        'ritmo': 'Material sintético: El pulso regular sirve de referencia temporal. El ritmo combina duraciones y silencios. Para practicarlo, el grupo marca un pulso con palmas mientras una segunda parte interpreta un patrón rítmico.',
        'sintesis': 'Material sintético: En la síntesis sustractiva un oscilador genera una señal rica en armónicos. Un filtro modifica su espectro y una envolvente controla la evolución de la amplitud. Una actividad consiste en variar la frecuencia de corte de un filtro paso bajo.',
        'guitarra': 'Material sintético: Una actividad de guitarra trabaja la alternancia de índice y medio de la mano derecha sobre cuerdas al aire. Se comienza lentamente, atendiendo a la relajación y a la regularidad del sonido.',
        'historia': 'Material sintético: El bajo continuo es una práctica característica del Barroco. Un instrumento grave sostiene el bajo y un instrumento armónico realiza los acordes. La actividad propone reconocer sus funciones durante una audición.',
    }
    queries = [
        ('ritmo', '¿Cómo practicar pulso y ritmo con palmas?'),
        ('ritmo', 'Como traballar o pulso e os silencios co grupo?'),
        ('sintesis', 'Actividad para entender el filtro paso bajo en síntesis sustractiva'),
        ('sintesis', 'Como cambia o espectro ao variar a frecuencia de corte?'),
        ('guitarra', 'Ejercicio de alternancia de los dedos índice y medio'),
        ('guitarra', 'Práctica de man dereita con cordas ao aire'),
        ('historia', 'Instrumentos que realizan el bajo continuo barroco'),
        ('historia', 'Como recoñecer as funcións do baixo e dos acordes no Barroco?'),
    ]
    report = {'model': settings.model, 'corpus': '4 documentos sintéticos; ninguna fuente personal', 'queries': []}
    with tempfile.TemporaryDirectory(prefix='docente-rag-check-') as directory:
        root = Path(directory)
        db = root / 'docente.sqlite3'
        import_config(db, load(Path(__file__).resolve().parents[1] / 'config/teaching.example.yaml'))
        ids = {}
        for key, text in fixtures.items():
            source = root / f'{key}.txt'
            source.write_text(text, encoding='utf-8')
            result = import_document(db, source, category='documental', subjects=['historia-i'], values={'title': f'Prueba sintética: {key}'})
            ids[key] = result['document_id']
            authorize_document(db, result['document_id'], enabled=True)
        with OllamaEmbedder(settings) as embedder:
            report['digest'] = embedder.digest
            start = time.perf_counter()
            report['index'] = index_library(db, settings, embedder)
            report['index_seconds'] = round(time.perf_counter() - start, 3)
            report['dimensions'] = embedder.dimensions
            for expected, query in queries:
                start = time.perf_counter()
                result = search(db, settings, embedder, query, subject='historia-i', top_k=1)
                hit = result['results'][0]
                report['queries'].append({'query': query, 'expected': expected, 'matched': hit['document_id'] == ids[expected],
                                          'distance': round(hit['distance'], 4), 'seconds': round(time.perf_counter() - start, 3)})
            authorize_document(db, ids['ritmo'], enabled=False)
            result = search(db, settings, embedder, 'ritmo', subject='historia-i', document_ids=[ids['ritmo']])
            report['excluded_source_returns_no_evidence'] = result['status'] == 'no_evidence'
        report['correct_top1'] = sum(item['matched'] for item in report['queries'])
        report['total_queries'] = len(queries)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + '\n', encoding='utf-8')
    return 0 if report['correct_top1'] == len(queries) and report['excluded_source_returns_no_evidence'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
