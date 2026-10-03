"""Microbenchmark sintético de búsqueda exacta SQLite; no mide Ollama."""

import json
from pathlib import Path
import resource
import sqlite3
import statistics
import tempfile
import time

import sqlite_vec

from docente_ai.rag.service import load_vector_extension


def main():
    report = {'dimensions': 1024, 'scope': 'SQL exacto filtrado, datos sintéticos; sin embeddings ni Ollama', 'runs': []}
    with tempfile.TemporaryDirectory(prefix='docente-vector-bench-') as directory:
        connection = sqlite3.connect(Path(directory) / 'benchmark.sqlite3')
        try:
            load_vector_extension(connection)
            connection.execute('CREATE TABLE chunks(id INTEGER PRIMARY KEY,allowed INTEGER,text TEXT,vector BLOB)')
            query = sqlite_vec.serialize_float32([1.0] + [0.0] * 1023)
            for size in (1000, 10000):
                connection.execute('DELETE FROM chunks')
                connection.executemany('INSERT INTO chunks VALUES (?,?,?,?)',
                    ((i, i % 2, 'Texto sintético de prueba. ' * 4,
                      sqlite_vec.serialize_float32([i / size, 1.0] + [0.0] * 1022)) for i in range(size)))
                connection.commit()
                sql = '''WITH candidates AS MATERIALIZED (SELECT * FROM chunks WHERE allowed=1),
                         ranked AS MATERIALIZED (SELECT id,vec_distance_cosine(vector,?) AS distance FROM candidates)
                         SELECT id,distance FROM ranked ORDER BY distance,id LIMIT 6'''
                connection.execute(sql, (query,)).fetchall()
                durations = []
                for _ in range(20):
                    start = time.perf_counter()
                    connection.execute(sql, (query,)).fetchall()
                    durations.append(time.perf_counter() - start)
                report['runs'].append({'stored_vectors': size, 'authorized_candidates': size // 2,
                                       'median_seconds': round(statistics.median(durations), 5),
                                       'p95_seconds': round(sorted(durations)[18], 5)})
        finally:
            connection.close()
    # ru_maxrss se expresa en bytes en macOS, plataforma objetivo de esta prueba.
    import sys
    divisor = 1024 * 1024 if sys.platform == 'darwin' else 1024
    report['python_peak_rss_mib'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / divisor, 1)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
