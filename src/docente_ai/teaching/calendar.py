"""Expandir horarios locales sin confundir planes con clases impartidas."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def local_start(day: date, clock: str, zone: str) -> datetime:
    naive = datetime.combine(day, time.fromisoformat(clock))
    tz = ZoneInfo(zone)
    candidates = {
        candidate.astimezone(timezone.utc)
        for fold in (0, 1)
        if (candidate := naive.replace(tzinfo=tz, fold=fold))
        .astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) == naive
    }
    if len(candidates) != 1:
        raise ValueError(f"Hora local inexistente o ambigua: {day} {clock} ({zone}).")
    return next(iter(candidates)).astimezone(tz)


def sessions(config: dict, start: date, end: date, group_id: str | None = None) -> list[dict]:
    if start > end:
        raise ValueError("La fecha inicial debe ser anterior o igual a la final.")
    groups = {g['id']: g for g in config['groups']}
    if group_id is not None and group_id not in groups:
        raise ValueError(f"Grupo inexistente: {group_id}.")
    subjects = {s['id']: s for s in config['subjects']}
    years = {y['id']: y for y in config['academic_years']}
    exceptions = {(e['schedule_rule_id'], e['date']): e for e in config['calendar_exceptions']}
    result = []
    for rule in config['schedule_rules']:
        group = groups[rule['group_id']]
        if group_id is not None and group['id'] != group_id:
            continue
        year = years[group['academic_year_id']]
        first = max(start, date.fromisoformat(rule['valid_from']), date.fromisoformat(year['start_date']))
        last = min(end, date.fromisoformat(rule['valid_to']), date.fromisoformat(year['end_date']))
        day = first + timedelta(days=(rule['weekday'] - first.isoweekday()) % 7)
        while day <= last:
            exception = exceptions.get((rule['id'], day.isoformat()), {})
            if exception.get('cancelled', False):
                day += timedelta(days=7)
                continue
            clock = exception.get('start_time', rule['start_time'])
            duration = exception.get('duration_minutes', rule['duration_minutes'])
            room = exception.get('room', rule.get('room', ''))
            begin = local_start(day, clock, rule['timezone'])
            finish = (begin.astimezone(timezone.utc) + timedelta(minutes=duration)).astimezone(begin.tzinfo)
            result.append({
                'id': f"{rule['id']}:{day.isoformat()}",
                'schedule_rule_id': rule['id'], 'group_id': group['id'],
                'group': group['name'], 'subject_id': group['subject_id'],
                'subject': subjects[group['subject_id']]['name'],
                'center_id': group['center_id'], 'teacher_id': group['teacher_id'],
                'start': begin.isoformat(), 'end': finish.isoformat(),
                'duration_minutes': duration, 'room': room, 'timezone': rule['timezone'],
                'status': 'planned',
            })
            day += timedelta(days=7)
    return sorted(result, key=lambda s: (datetime.fromisoformat(s['start']), s['id']))


def check_overlaps(items: list[dict]) -> None:
    active = []
    for item in items:
        begin = datetime.fromisoformat(item['start'])
        active = [other for other in active if datetime.fromisoformat(other['end']) > begin]
        for other in active:
            same_group = item['group_id'] == other['group_id']
            same_teacher = item['teacher_id'] == other['teacher_id']
            same_room = bool(item['room']) and (item['center_id'], item['room']) == (other['center_id'], other['room'])
            if same_group or same_teacher or same_room:
                raise ValueError(f"Solapamiento entre {other['id']} y {item['id']} (grupo, profesor o aula).")
        active.append(item)


def _escape_ical(text: str) -> str:
    return text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def to_ical(
    config: dict,
    start: date | None = None,
    end: date | None = None,
    group_id: str | None = None,
    reminder_minutes: int = 15,
) -> str:
    """Generar archivo iCalendar (.ics) estándar (RFC 5545) con avisos/alarmas."""
    if start is None or end is None:
        years = config.get('academic_years', [])
        if years:
            start_date = min(date.fromisoformat(y['start_date']) for y in years)
            end_date = max(date.fromisoformat(y['end_date']) for y in years)
        else:
            today = date.today()
            start_date = date(today.year, 9, 1) if today.month >= 9 else date(today.year - 1, 9, 1)
            end_date = date(start_date.year + 1, 6, 30)
        start = start or start_date
        end = end or end_date

    session_list = sessions(config, start, end, group_id=group_id)
    cal_name = "Horario Docente"
    teachers = config.get('teachers', [])
    if teachers:
        cal_name = f"Horario Docente - {teachers[0]['name']}"

    now_str = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Docente AI//Enjambre Docente//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_ical(cal_name)}",
        f"X-WR-TIMEZONE:{config.get('timezone', 'Europe/Madrid')}",
    ]

    for s in session_list:
        begin = datetime.fromisoformat(s['start'])
        finish = datetime.fromisoformat(s['end'])
        tzid = s.get('timezone', config.get('timezone', 'Europe/Madrid'))
        dtstart = begin.strftime('%Y%m%dT%H%M%S')
        dtend = finish.strftime('%Y%m%dT%H%M%S')
        uid = f"{s['id']}@enjambre.local"
        summary = f"{s['subject']} · {s['group']}"
        desc = f"Materia: {s['subject']}\\nGrupo: {s['group']}"
        if s.get('room'):
            desc += f"\\nAula: {s['room']}"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_str}",
            f"DTSTART;TZID={tzid}:{dtstart}",
            f"DTEND;TZID={tzid}:{dtend}",
            f"SUMMARY:{_escape_ical(summary)}",
        ])
        if s.get('room'):
            lines.append(f"LOCATION:{_escape_ical(s['room'])}")
        lines.append(f"DESCRIPTION:{desc}")
        lines.append("STATUS:CONFIRMED")

        if reminder_minutes > 0:
            lines.extend([
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{_escape_ical(f'Aviso: {summary}')}",
                f"TRIGGER:-PT{int(reminder_minutes)}M",
                "END:VALARM",
            ])
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

