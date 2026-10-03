from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sqlite3

import pytest

from docente_ai.cli import main
from docente_ai.config import ConfigError, load, validate
from docente_ai.storage import StorageError, import_config, read_config
from docente_ai.teaching.calendar import local_start, sessions
from docente_ai.teaching.curriculum import show_curriculum

EXAMPLE = Path(__file__).resolve().parents[1] / 'config/teaching.example.yaml'


@pytest.fixture
def config():
    return load(EXAMPLE)


def test_new_subject_and_group_without_code_change(config):
    config['subjects'].append({'id': 'composition', 'name': 'Composición libre'})
    config['groups'].append({**config['groups'][0], 'id': 'new-group', 'subject_id': 'composition'})
    assert len(validate(config)['groups']) == 2


@pytest.mark.parametrize(('table', 'field', 'value'), [
    ('groups', 'subject_id', 'missing'), ('groups', 'academic_year_id', 'missing'),
    ('groups', 'teacher_id', 'missing'), ('groups', 'center_id', 'missing'),
    ('schedule_rules', 'weekday', 8), ('schedule_rules', 'weekday', True),
    ('schedule_rules', 'duration_minutes', 0), ('schedule_rules', 'duration_minutes', -1),
    ('schedule_rules', 'duration_minutes', '60'), ('schedule_rules', 'start_time', '25:00'),
    ('schedule_rules', 'start_time', '8:00'), ('schedule_rules', 'timezone', 'Invalid/Zone'),
    ('schedule_rules', 'valid_from', '2025-01-01'), ('schedule_rules', 'valid_to', '2026-08-31'),
    ('academic_years', 'end_date', '2026-02-30'), ('academic_years', 'end_date', '2025-01-01'),
    ('curriculum_units', 'objectives', 'not a list'), ('curriculum_units', 'order', 0),
    ('curriculum_units', 'end_date', '2028-01-01'), ('calendar_exceptions', 'date', '2026-10-13'),
])
def test_invalid_data(config, table, field, value):
    config[table][0][field] = value
    with pytest.raises(ConfigError):
        validate(config)


def test_duplicate_ids_unknown_fields_and_references(config):
    for mutate in (
        lambda c: c['subjects'].append(deepcopy(c['subjects'][0])),
        lambda c: c['groups'][0].update(typo='value'),
        lambda c: c['group_curricula'][0].update(curriculum_id='missing'),
        lambda c: c['calendar_exceptions'][0].update(start_time='10:00'),
        lambda c: c['curriculum_units'][0].pop('end_date'),
    ):
        changed = deepcopy(config)
        mutate(changed)
        with pytest.raises(ConfigError):
            validate(changed)


@pytest.mark.parametrize('text', [
    'schema_version: 1\nschema_version: 1\n',
    '!!python/object/apply:os.system ["touch should-not-exist"]',
    '[]', 'schema_version: [', 'true: value',
])
def test_unsafe_or_invalid_yaml_rejected(text, tmp_path):
    path = tmp_path / 'bad.yaml'
    path.write_text(text)
    with pytest.raises(ConfigError):
        load(path)
    assert not (tmp_path / 'should-not-exist').exists()


def test_calendar_exceptions_and_bounds(config):
    items = sessions(config, date(2026, 10, 1), date(2026, 10, 31))
    assert [item['start'][:10] for item in items] == ['2026-10-05', '2026-10-19', '2026-10-26']
    assert items[1]['start'] == '2026-10-19T18:00:00+02:00'
    assert items[1]['room'] == 'Aula 2'
    assert items[2]['start'].endswith('+01:00')
    assert all(item['status'] == 'planned' for item in items)
    assert not sessions(config, date(2027, 7, 1), date(2027, 8, 1))
    assert len({item['id'] for item in items}) == len(items)


@pytest.mark.parametrize('day', [date(2026, 3, 29), date(2026, 10, 25)])
def test_dst_invalid_or_ambiguous_hour(day):
    with pytest.raises(ValueError, match='inexistente o ambigua'):
        local_start(day, '02:30', 'Europe/Madrid')


def test_overlap_detected_and_adjacent_allowed(config):
    rule = {**config['schedule_rules'][0], 'id': 'other', 'start_time': '17:30'}
    config['schedule_rules'].append(rule)
    with pytest.raises(ConfigError, match='Solapamiento'):
        validate(config)
    # Eliminar excepción que mueve una sesión a las 18:00.
    config['calendar_exceptions'] = []
    rule['start_time'] = '18:00'
    validate(config)


def test_same_teacher_overlap_across_groups(config):
    config['groups'].append({**config['groups'][0], 'id': 'other'})
    config['schedule_rules'].append({**config['schedule_rules'][0], 'id': 'other-rule', 'group_id': 'other', 'room': 'Otra aula'})
    with pytest.raises(ConfigError, match='Solapamiento'):
        validate(config)


def test_same_room_overlap_across_teachers(config):
    config['teachers'].append({'id': 'other-teacher', 'name': 'Otro profesor'})
    config['groups'].append({**config['groups'][0], 'id': 'other', 'teacher_id': 'other-teacher'})
    config['schedule_rules'].append({**config['schedule_rules'][0], 'id': 'other-rule', 'group_id': 'other'})
    with pytest.raises(ConfigError, match='Solapamiento'):
        validate(config)


def test_curriculum_binding_must_match_subject(config):
    config['subjects'].append({'id': 'other', 'name': 'Otra asignatura'})
    config['curricula'][0]['subject_id'] = 'other'
    with pytest.raises(ConfigError, match='coincidir'):
        validate(config)


def test_curriculum_suggests_without_progress(config):
    before = deepcopy(config)
    result = show_curriculum(config, 'historia-3gp', date(2026, 10, 1))
    assert result['suggested_units'] == ['unidad-1']
    assert not show_curriculum(config, 'historia-3gp', date(2026, 12, 1))['suggested_units']
    assert config == before
    with pytest.raises(ValueError):
        show_curriculum(config, 'missing')


def test_import_idempotent_and_round_trip(config, tmp_path):
    db = tmp_path / 'data' / 'db.sqlite3'
    assert import_config(db, config)['changed']
    assert not import_config(db, config)['changed']
    assert read_config(db) == config
    with sqlite3.connect(db) as connection:
        assert connection.execute('SELECT count(*) FROM config_imports').fetchone()[0] == 1
        assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
        assert connection.execute('PRAGMA user_version').fetchone()[0] == 7


def test_invalid_import_does_not_create_database(config, tmp_path):
    config['groups'][0]['subject_id'] = 'missing'
    db = tmp_path / 'data' / 'db.sqlite3'
    with pytest.raises(ConfigError):
        import_config(db, config)
    assert not db.parent.exists()


def test_explicit_replace_preserves_snapshot(config, tmp_path):
    db = tmp_path / 'db.sqlite3'
    import_config(db, config)
    changed = deepcopy(config)
    changed['subjects'][0]['name'] = 'Nombre revisado'
    with pytest.raises(StorageError, match='--replace'):
        import_config(db, changed)
    assert read_config(db) == config
    import_config(db, changed, replace=True)
    assert read_config(db) == changed
    with sqlite3.connect(db) as connection:
        snapshots = connection.execute('SELECT snapshot FROM config_imports ORDER BY id').fetchall()
        assert len(snapshots) == 2
        assert json.loads(snapshots[0][0])['subjects'][0]['name'] == config['subjects'][0]['name']


def test_transaction_rolls_back_on_database_failure(config, tmp_path):
    db = tmp_path / 'db.sqlite3'
    import_config(db, config)
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON subjects BEGIN SELECT RAISE(ABORT, 'simulated failure'); END")
    changed = deepcopy(config)
    changed['subjects'][0]['name'] = 'Cambio'
    with pytest.raises(sqlite3.IntegrityError):
        import_config(db, changed, replace=True)
    assert read_config(db) == config


def test_missing_and_newer_database_not_modified(config, tmp_path):
    db = tmp_path / 'db.sqlite3'
    with pytest.raises(StorageError):
        read_config(db)
    assert not db.exists()
    with sqlite3.connect(db) as connection:
        connection.execute('PRAGMA user_version = 99')
    before = db.read_bytes()
    with pytest.raises(StorageError):
        import_config(db, config)
    assert db.read_bytes() == before


def test_cli_end_to_end(tmp_path, capsys):
    db = str(tmp_path / 'teaching.sqlite3')
    assert main(['config', 'validate', str(EXAMPLE), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['valid']
    assert not Path(db).exists()
    assert main(['config', 'import', str(EXAMPLE), '--db', db, '--json']) == 0
    assert json.loads(capsys.readouterr().out)['changed']
    assert main(['calendar', 'list', '--db', db, '--from', '2026-10-01', '--to', '2026-10-31', '--json']) == 0
    assert len(json.loads(capsys.readouterr().out)) == 3
    assert main(['curriculum', 'show', '--db', db, '--group', 'historia-3gp', '--date', '2026-10-01', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['suggested_units'] == ['unidad-1']
    output = tmp_path / 'export.yaml'
    assert main(['config', 'export', '--db', db, '--output', str(output)]) == 0
    assert load(output) == load(EXAMPLE)
    assert main(['config', 'export', '--db', db, '--output', str(output)]) == 1


def test_cli_errors_are_actionable(tmp_path, capsys):
    assert main(['calendar', 'list', '--db', str(tmp_path / 'missing.db'), '--from', '2026-10-01', '--to', '2026-10-31', '--json']) == 1
    assert json.loads(capsys.readouterr().out)['ok'] is False
    with pytest.raises(SystemExit) as exc:
        main(['calendar', 'list', '--from', 'wrong', '--to', '2026-10-31'])
    assert exc.value.code == 2


def test_reversed_interval_and_unknown_group(config):
    with pytest.raises(ValueError):
        sessions(config, date(2026, 10, 31), date(2026, 10, 1))
    with pytest.raises(ValueError):
        sessions(config, date(2026, 10, 1), date(2026, 10, 31), 'missing')


def test_duplicate_exception_and_unit_order(config):
    for table in ('calendar_exceptions', 'curriculum_units', 'group_curricula'):
        changed = deepcopy(config)
        changed[table].append({**changed[table][0], 'id': 'duplicate-with-new-id'})
        with pytest.raises(ConfigError):
            validate(changed)


def test_dst_problem_rejected_during_configuration(config):
    config['calendar_exceptions'] = []
    config['schedule_rules'][0].update(weekday=7, start_time='02:30')
    with pytest.raises(ConfigError, match='ambigua'):
        validate(config)
    # Cancelar la ocurrencia problemática permite guardar el horario.
    config['calendar_exceptions'] = [
        {'id': 'dst-autumn', 'schedule_rule_id': 'historia-lunes', 'date': '2026-10-25', 'cancelled': True},
        {'id': 'dst-spring', 'schedule_rule_id': 'historia-lunes', 'date': '2027-03-28', 'cancelled': True},
    ]
    validate(config)


def test_duration_is_elapsed_time_across_dst(config):
    config['calendar_exceptions'] = []
    config['schedule_rules'][0].update(weekday=7, start_time='01:30', duration_minutes=180)
    items = sessions(config, date(2026, 10, 25), date(2026, 10, 25))
    assert items[0]['start'] == '2026-10-25T01:30:00+02:00'
    assert items[0]['end'] == '2026-10-25T03:30:00+01:00'
    assert items[0]['duration_minutes'] == 180


def test_foreign_keys_enforced(config, tmp_path):
    db = tmp_path / 'db.sqlite3'
    import_config(db, config)
    from docente_ai.storage import connect
    connection = connect(db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM subjects WHERE id = 'historia-i'")
    finally:
        connection.close()


def test_unknown_database_preserved(config, tmp_path):
    db = tmp_path / 'other.sqlite3'
    with sqlite3.connect(db) as connection:
        connection.execute('CREATE TABLE unrelated (id INTEGER)')
    before = db.read_bytes()
    with pytest.raises(StorageError):
        import_config(db, config)
    assert db.read_bytes() == before


def test_to_ical_generation(config):
    from docente_ai.teaching.calendar import to_ical
    ical = to_ical(config, start=date(2026, 10, 1), end=date(2026, 10, 31), reminder_minutes=15)
    assert "BEGIN:VCALENDAR" in ical
    assert "END:VCALENDAR" in ical
    assert "BEGIN:VEVENT" in ical
    assert "BEGIN:VALARM" in ical
    assert "TRIGGER:-PT15M" in ical
    assert "ACTION:DISPLAY" in ical
    assert "SUMMARY:Historia de la Música I · Grupo A" in ical


