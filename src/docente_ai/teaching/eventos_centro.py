"""Eventos del centro separados de las clases y de las fuentes del asistente."""

from datetime import datetime, timezone
import json

from docente_ai.teaching.calendar import _escape_ical


def cargar_eventos(root):
    ruta = root / 'config/eventos-centro.json'
    if not ruta.exists():
        return []
    datos = json.loads(ruta.read_text(encoding='utf-8'))
    if not isinstance(datos, list) or len(datos) > 500:
        raise ValueError('El calendario del centro admite una lista de hasta 500 eventos.')
    identificadores = set()
    for evento in datos:
        if not isinstance(evento, dict) or set(evento) != {'id', 'titulo', 'inicio', 'lugar', 'prioritario', 'fuente'}:
            raise ValueError('Evento del centro con campos inválidos.')
        for campo in ('id', 'titulo', 'inicio', 'lugar', 'fuente'):
            valor = evento[campo]
            if not isinstance(valor, str) or len(valor) > 500 or any(ord(c) < 32 for c in valor):
                raise ValueError('Texto inválido en el calendario del centro.')
        if not evento['id'] or not evento['titulo'] or evento['id'] in identificadores:
            raise ValueError('Identificador vacío o repetido en el calendario del centro.')
        identificadores.add(evento['id'])
        if type(evento['prioritario']) is not bool:
            raise ValueError('La prioridad de un evento debe ser booleana.')
        inicio = datetime.fromisoformat(evento['inicio'])
        if inicio.tzinfo is None:
            raise ValueError('El evento debe indicar su zona horaria.')
    return sorted(datos, key=lambda evento: datetime.fromisoformat(evento['inicio']))


def calendario_eventos(eventos, *, solo_prioritarios=False):
    lineas = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Arkhe//Eventos del centro//ES',
              'CALSCALE:GREGORIAN', 'X-WR-CALNAME:Audiciones y conciertos del centro']
    sello = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for evento in eventos:
        if solo_prioritarios and not evento['prioritario']:
            continue
        inicio = datetime.fromisoformat(evento['inicio']).astimezone(timezone.utc)
        lineas.extend(['BEGIN:VEVENT', f"UID:{_escape_ical(evento['id'])}@arkhe.local", f'DTSTAMP:{sello}',
                       f"DTSTART:{inicio.strftime('%Y%m%dT%H%M%SZ')}",
                       f"SUMMARY:{_escape_ical(evento['titulo'])}", f"LOCATION:{_escape_ical(evento['lugar'])}",
                       f"DESCRIPTION:{_escape_ical(evento['fuente'])}"])
        # El documento no indica duración: no inventar una hora de finalización.
        for minutos in (1440, 60):
            lineas.extend(['BEGIN:VALARM', 'ACTION:DISPLAY', f'TRIGGER:-PT{minutos}M',
                           f"DESCRIPTION:{_escape_ical('Aviso: ' + evento['titulo'])}", 'END:VALARM'])
        lineas.append('END:VEVENT')
    lineas.append('END:VCALENDAR')
    # RFC 5545: plegar líneas a un máximo de 75 octetos, sin cortar UTF-8.
    plegadas = []
    for linea in lineas:
        fragmento = ''
        for caracter in linea:
            if len((fragmento + caracter).encode('utf-8')) > 75:
                plegadas.append(fragmento)
                fragmento = ' '
            fragmento += caracter
        plegadas.append(fragmento)
    return '\r\n'.join(plegadas) + '\r\n'
