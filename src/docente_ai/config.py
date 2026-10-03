"""Entrada YAML estricta; ninguna escritura ocurre antes de validar todo."""

from copy import deepcopy
from datetime import date, time
from pathlib import Path
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

from docente_ai.teaching.calendar import check_overlaps, sessions


class ConfigError(ValueError):
    pass


class StrictLoader(yaml.SafeLoader):
    pass


# Mantener fechas como texto para un round-trip YAML/JSON estable.
StrictLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in values if tag != 'tag:yaml.org,2002:timestamp']
    for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ConfigError('Todas las claves YAML deben ser texto.')
        if key in result:
            raise ConfigError(f'Clave YAML duplicada: {key}.')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)

# Campos requeridos y opcionales. Relaciones y campos semánticos se validan abajo.
SCHEMAS = {
    'centers': ('id name', ''),
    'teachers': ('id name', ''),
    'academic_years': ('id name start_date end_date', ''),
    'subjects': ('id name', 'description color periods'),
    'groups': ('id name subject_id center_id academic_year_id teacher_id level', 'language'),
    'schedule_rules': ('id group_id weekday start_time duration_minutes valid_from valid_to', 'room timezone'),
    'calendar_exceptions': ('id schedule_rule_id date', 'cancelled start_time duration_minutes room'),
    'curricula': ('id subject_id academic_year_id version name', ''),
    'curriculum_units': ('id curriculum_id order title objectives contents', 'competencies assessment_criteria activities repertoire resources start_date end_date'),
    'group_curricula': ('id group_id curriculum_id', ''),
}
TEXT_LISTS = {'objectives', 'contents', 'competencies', 'assessment_criteria', 'activities', 'repertoire', 'resources'}


RELATIONS = {
    'groups': {'subject_id': 'subjects', 'center_id': 'centers', 'academic_year_id': 'academic_years', 'teacher_id': 'teachers'},
    'schedule_rules': {'group_id': 'groups'},
    'calendar_exceptions': {'schedule_rule_id': 'schedule_rules'},
    'curricula': {'subject_id': 'subjects', 'academic_year_id': 'academic_years'},
    'curriculum_units': {'curriculum_id': 'curricula'},
    'group_curricula': {'group_id': 'groups', 'curriculum_id': 'curricula'},
}

def fail(message):
    raise ConfigError(message)


def fields(value, required, optional, where):
    if not isinstance(value, dict):
        fail(f'{where}: se esperaba un objeto.')
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        fail(f'{where}: campos ausentes {sorted(missing)}; desconocidos {sorted(extra)}.')


def iso_date(value, where):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        fail(f'{where}: utiliza fecha YYYY-MM-DD.')
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail(f'{where}: fecha inválida.')


# Compatibilidad de carpetas existentes; solo se aplica cuando falta periods.
LEGACY_PERIODS = {
    'historia-i': [
        ('00 Xeral e Tratados', 'Xeral e Tratados'),
        ('01 Antiguedade', 'Antigüidade'),
        ('02 Idade Media', 'Idade Media'),
        ('03 Renacemento', 'Renacemento'),
    ],
    'historia-ii': [
        ('00 Xeral e Tratados', 'Xeral e Tratados'),
        ('01 Barroco e Preclasicismo', 'Barroco e Preclasicismo'),
        ('02 Clasicismo', 'Clasicismo'),
        ('03 Romanticismo', 'Romanticismo'),
        ('04 Seculo XX e Contemporanea', 'Século XX e Contemporánea'),
    ],
}


def migrate_subject(subject):
    if 'periods' not in subject and subject['id'] in LEGACY_PERIODS:
        subject['periods'] = [{'id': key, 'nombre': name} for key, name in LEGACY_PERIODS[subject['id']]]
    return subject


def validate_periods(value):
    if not isinstance(value, list):
        fail('subjects.periods: se esperaba una lista ordenada.')
    seen = set()
    for period in value:
        fields(period, ['id', 'nombre'], [], 'período')
        key, name = period['id'], period['nombre']
        if (not isinstance(key, str) or not key.strip() or len(key) > 128
                or key.startswith('.') or any(c in key for c in '/\\\x00')
                or key != key.strip() or any(ord(c) < 32 for c in key)):
            fail('Período: identificador de carpeta inválido.')
        if not isinstance(name, str) or not name.strip() or len(name) > 200:
            fail('Período: nombre inválido.')
        if key.casefold() in seen:
            fail('Período: identificador duplicado.')
        seen.add(key.casefold())


def validate(raw: dict) -> dict:
    fields(raw, ['schema_version', *SCHEMAS], ['timezone'], 'configuración')
    if type(raw['schema_version']) is not int or raw['schema_version'] != 1:
        fail('schema_version debe ser 1.')
    data = deepcopy(raw)
    data.setdefault('timezone', 'Europe/Madrid')
    try:
        if not isinstance(data['timezone'], str):
            fail('timezone debe ser texto.')
        ZoneInfo(data['timezone'])
    except (ZoneInfoNotFoundError, ValueError):
        fail('Zona horaria desconocida.')
    indexes = {}
    for table, (required, optional) in SCHEMAS.items():
        rows = data[table]
        if not isinstance(rows, list):
            fail(f'{table}: se esperaba una lista, usa [] si está vacía.')
        indexes[table] = {}
        for row in rows:
            fields(row, required.split(), optional.split(), table)
            for key, value in row.items():
                where = f'{table}.{key}'
                if key == 'color':
                    if not isinstance(value, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
                        fail('subjects.color: utiliza un color hexadecimal #RRGGBB.')
                elif key == 'periods':
                    validate_periods(value)
                elif key in TEXT_LISTS:
                    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
                        fail(f'{where}: se esperaba una lista de textos no vacíos.')
                elif key in {'weekday', 'duration_minutes', 'order', 'version'}:
                    if type(value) is not int or value < 1:
                        fail(f'{where}: se esperaba un entero positivo.')
                    if key == 'weekday' and value > 7:
                        fail(f'{where}: utiliza 1 (lunes) a 7 (domingo).')
                    if key == 'duration_minutes' and value > 1440:
                        fail(f'{where}: máximo 1440 minutos.')
                elif key == 'cancelled':
                    if type(value) is not bool:
                        fail(f'{where}: se esperaba true o false.')
                else:
                    if not isinstance(value, str) or (not value.strip() and key != 'room'):
                        fail(f'{where}: se esperaba texto no vacío.')
                    if (key == 'id' or key.endswith('_id')) and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', value):
                        fail(f'{where}: identificador inválido; usa letras, números, punto, guion o guion bajo.')
                    if key in {'start_date', 'end_date', 'date', 'valid_from', 'valid_to'}:
                        iso_date(value, where)
                    if key == 'start_time':
                        try:
                            if not re.fullmatch(r'\d{2}:\d{2}', value):
                                raise ValueError
                            time.fromisoformat(value)
                        except ValueError:
                            fail(f'{where}: utiliza una hora válida HH:MM.')
            if table == 'subjects':
                migrate_subject(row)
            if row['id'] in indexes[table]:
                fail(f"{table}: ID duplicado {row['id']}.")
            indexes[table][row['id']] = row

    for table, relations in RELATIONS.items():
        for row in data[table]:
            for key, target in relations.items():
                if row[key] not in indexes[target]:
                    fail(f"{table}/{row['id']}: {key} inexistente: {row[key]}.")
    for year in data['academic_years']:
        start, end = iso_date(year['start_date'], 'curso'), iso_date(year['end_date'], 'curso')
        if not 0 <= (end - start).days <= 730:
            fail('El curso debe durar entre 1 día y 2 años.')
    for rule in data['schedule_rules']:
        rule.setdefault('timezone', data['timezone'])
        try:
            ZoneInfo(rule['timezone'])
        except (ZoneInfoNotFoundError, ValueError):
            fail(f"Zona horaria inválida en {rule['id']}.")
        group = indexes['groups'][rule['group_id']]
        year = indexes['academic_years'][group['academic_year_id']]
        if not year['start_date'] <= rule['valid_from'] <= rule['valid_to'] <= year['end_date']:
            fail(f"{rule['id']}: vigencia fuera del curso o invertida.")
    seen = set()
    for exception in data['calendar_exceptions']:
        key = exception['schedule_rule_id'], exception['date']
        if key in seen:
            fail('Excepciones duplicadas para la misma regla y fecha.')
        seen.add(key)
        rule = indexes['schedule_rules'][exception['schedule_rule_id']]
        day = iso_date(exception['date'], 'excepción')
        if not rule['valid_from'] <= exception['date'] <= rule['valid_to'] or day.isoweekday() != rule['weekday']:
            fail(f"{exception['id']}: no corresponde a una sesión del horario.")
        overrides = exception.keys() & {'start_time', 'duration_minutes', 'room'}
        if exception.get('cancelled', False) and overrides:
            fail('Una cancelación no puede modificar también hora, duración o aula.')
        if not exception.get('cancelled', False) and not overrides:
            fail('La excepción debe cancelar o modificar una sesión.')
    seen = set()
    for unit in data['curriculum_units']:
        key = unit['curriculum_id'], unit['order']
        if key in seen:
            fail('Orden de unidad duplicado dentro de la programación.')
        seen.add(key)
        if ('start_date' in unit) != ('end_date' in unit):
            fail('La temporalización necesita start_date y end_date.')
        if 'start_date' in unit:
            curriculum = indexes['curricula'][unit['curriculum_id']]
            year = indexes['academic_years'][curriculum['academic_year_id']]
            if not year['start_date'] <= unit['start_date'] <= unit['end_date'] <= year['end_date']:
                fail('Temporalización de unidad fuera del curso o invertida.')
    seen = set()
    for binding in data['group_curricula']:
        group = indexes['groups'][binding['group_id']]
        curriculum = indexes['curricula'][binding['curriculum_id']]
        if group['id'] in seen:
            fail('Cada grupo debe tener como máximo una programación activa.')
        seen.add(group['id'])
        if any(group[key] != curriculum[key] for key in ('subject_id', 'academic_year_id')):
            fail('La programación debe coincidir con la asignatura y el curso del grupo.')
    if data['academic_years']:
        start = min(iso_date(y['start_date'], 'curso') for y in data['academic_years'])
        end = max(iso_date(y['end_date'], 'curso') for y in data['academic_years'])
        try:
            check_overlaps(sessions(data, start, end))
        except ValueError as exc:
            fail(str(exc))
    return data


def load(path: Path) -> dict:
    try:
        if path.stat().st_size > 2_000_000:
            fail('Configuración demasiado grande (máximo 2 MB).')
        raw = yaml.load(path.read_text(encoding='utf-8'), Loader=StrictLoader)
        return validate(raw)
    except (OSError, UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise ConfigError(f'No se pudo leer la configuración: {exc}') from exc
