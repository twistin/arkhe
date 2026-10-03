"""Registro de impartición real: solo el profesor crea y confirma; el asistente lee."""

from contextlib import closing
from datetime import date
import json
from pathlib import Path
from uuid import uuid4

from docente_ai.library.service import now, read_connection
from docente_ai.storage import connect, migrate


def _dump(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def _require_group(connection, group_id):
    """Verifica que el grupo existe en la configuración importada."""
    row = connection.execute(
        "SELECT id FROM groups WHERE id=?", (group_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f'Grupo inexistente: {group_id}.')


def _require_record(connection, record_id):
    row = connection.execute(
        'SELECT id FROM session_records WHERE id=?', (record_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f'Registro de sesión inexistente: {record_id}.')


def add_record(db: Path, group_id: str, session_date: date, duration_minutes: int, topic: str,
               *, run_id: str | None = None, objectives_met: list | None = None,
               activities: list | None = None, notes: str = '') -> dict:
    """Registrar una sesión impartida. Solo el profesor; no se genera automáticamente."""
    if not isinstance(topic, str) or not topic.strip() or len(topic) > 2000:
        raise ValueError('El tema impartido debe tener entre 1 y 2000 caracteres.')
    if not isinstance(notes, str) or len(notes) > 4000:
        raise ValueError('Las notas admiten hasta 4000 caracteres.')
    if not isinstance(duration_minutes, int) or not 1 <= duration_minutes <= 480:
        raise ValueError('La duración debe ser un entero entre 1 y 480 minutos.')
    objectives_met = objectives_met or []
    activities = activities or []
    if not isinstance(objectives_met, list):
        raise ValueError('objectives_met debe ser una lista.')
    if not isinstance(activities, list):
        raise ValueError('activities debe ser una lista.')
    record_id = 'sr-' + uuid4().hex
    with closing(connect(db)) as connection, connection:
        migrate(connection)
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        _require_group(connection, group_id)
        if run_id is not None:
            row = connection.execute(
                'SELECT id FROM generation_runs WHERE id=?', (run_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f'Registro generativo inexistente: {run_id}.')
        connection.execute(
            '''INSERT INTO session_records
               (id, group_id, session_date, duration_minutes, run_id, topic,
                objectives_met, activities_json, notes, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (record_id, group_id, session_date.isoformat(), duration_minutes, run_id,
             topic.strip(), _dump(objectives_met), _dump(activities), notes, now())
        )
    return get_record(db, record_id)


def add_progress(db: Path, record_id: str, unit_id: str, *, note: str = '') -> dict:
    """Confirmar que una unidad avanzó en esta sesión."""
    if not isinstance(note, str) or len(note) > 2000:
        raise ValueError('La nota de progreso admite hasta 2000 caracteres.')
    progress_id = 'up-' + uuid4().hex
    with closing(connect(db)) as connection, connection:
        migrate(connection)
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        _require_record(connection, record_id)
        group_id = connection.execute(
            'SELECT group_id FROM session_records WHERE id=?', (record_id,)
        ).fetchone()[0]
        connection.execute(
            '''INSERT INTO session_unit_progress (id, session_record_id, group_id, unit_id, progress_note)
               VALUES (?,?,?,?,?)
               ON CONFLICT(session_record_id, unit_id) DO UPDATE SET progress_note=excluded.progress_note''',
            (progress_id, record_id, group_id, unit_id, note)
        )
    return get_record(db, record_id)


def add_feedback(db: Path, record_id: str, *, what_worked: str = '',
                 what_failed: str = '', next_session_note: str = '') -> dict:
    """Guardar feedback del profesor sobre la sesión. Sobreescribe si ya existía."""
    for field, value in [('what_worked', what_worked), ('what_failed', what_failed),
                         ('next_session_note', next_session_note)]:
        if not isinstance(value, str) or len(value) > 2000:
            raise ValueError(f'{field} admite hasta 2000 caracteres.')
    fb_id = 'fb-' + uuid4().hex
    with closing(connect(db)) as connection, connection:
        migrate(connection)
        connection.row_factory = None
        connection.execute('BEGIN IMMEDIATE')
        _require_record(connection, record_id)
        connection.execute(
            '''INSERT INTO session_feedback
               (id, session_record_id, what_worked, what_failed, next_session_note, created_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(session_record_id) DO UPDATE SET
                   what_worked=excluded.what_worked,
                   what_failed=excluded.what_failed,
                   next_session_note=excluded.next_session_note,
                   created_at=excluded.created_at''',
            (fb_id, record_id, what_worked, what_failed, next_session_note, now())
        )
    return get_record(db, record_id)


def get_record(db: Path, record_id: str) -> dict:
    with closing(read_connection(db)) as connection:
        row = connection.execute(
            'SELECT * FROM session_records WHERE id=?', (record_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f'Registro de sesión inexistente: {record_id}.')
        record = dict(row)
        record['objectives_met'] = json.loads(record['objectives_met'])
        record['activities'] = json.loads(record.pop('activities_json'))
        progress = [dict(r) for r in connection.execute(
            'SELECT unit_id, progress_note FROM session_unit_progress WHERE session_record_id=?',
            (record_id,)
        )]
        record['progress'] = progress
        fb = connection.execute(
            'SELECT what_worked, what_failed, next_session_note, created_at FROM session_feedback WHERE session_record_id=?',
            (record_id,)
        ).fetchone()
        record['feedback'] = dict(fb) if fb else None
    return record


def list_records(db: Path, group_id: str, *, limit: int = 10) -> list[dict]:
    with closing(read_connection(db)) as connection:
        if connection.execute('PRAGMA user_version').fetchone()[0] < 6:
            return []
        return [dict(row) for row in connection.execute(
            '''SELECT id, group_id, session_date, duration_minutes, topic, notes, created_at
               FROM session_records WHERE group_id=?
               ORDER BY session_date DESC, created_at DESC LIMIT ?''',
            (group_id, limit)
        )]


def recent_experience(db: Path, group_id: str, *, limit: int = 3) -> list[dict]:
    """Resumen compacto de las últimas N sesiones del grupo para el contexto del agente."""
    with closing(read_connection(db)) as connection:
        if connection.execute('PRAGMA user_version').fetchone()[0] < 6:
            return []
        rows = connection.execute(
            '''SELECT id, session_date, duration_minutes, topic, notes
               FROM session_records WHERE group_id=?
               ORDER BY session_date DESC, created_at DESC LIMIT ?''',
            (group_id, limit)
        ).fetchall()
        if not rows:
            return []
        result = []
        for row in rows:
            record_id = row['id']
            progress = [dict(r) for r in connection.execute(
                'SELECT unit_id, progress_note FROM session_unit_progress WHERE session_record_id=?',
                (record_id,)
            )]
            fb = connection.execute(
                'SELECT what_worked, what_failed, next_session_note FROM session_feedback WHERE session_record_id=?',
                (record_id,)
            ).fetchone()
            result.append({
                'date': row['session_date'],
                'duration_minutes': row['duration_minutes'],
                'topic': row['topic'],
                'notes': row['notes'],
                'units_advanced': [p['unit_id'] for p in progress],
                'feedback': dict(fb) if fb else None,
            })
        return result
