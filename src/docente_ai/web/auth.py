"""Acceso del piloto: scrypt, sesiones opacas y límites en memoria por instancia."""

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
from threading import RLock
import time
from urllib.parse import parse_qs

from starlette.concurrency import run_in_threadpool
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

COOKIE = '__Host-arkhe-session'
CSRF = '__Host-arkhe-login'
PARAMS = dict(n=16384, r=8, p=1, dklen=64, maxmem=64 * 1024 * 1024)


def password_hash(password, salt=None):
    if not isinstance(password, str) or not 12 <= len(password) <= 1024:
        raise ValueError('La contraseña debe tener entre 12 y 1024 caracteres.')
    salt = salt or secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, **PARAMS)
    return {'algorithm': 'scrypt-v1', 'salt': salt.hex(), 'hash': key.hex()}


def create_user(path, username, password):
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,64}', username):
        raise ValueError('Usuario: utiliza 1–64 letras, cifras, puntos, guiones o guiones bajos.')
    path = Path(path)
    if path.exists():
        raise ValueError('Ya existe un usuario en esta instancia; no se sustituye automáticamente.')
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {'username': username, **password_hash(password)}
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(payload, output)


class AuthStore:
    def __init__(self, path, clock=time.monotonic):
        self.path, self.clock = Path(path), clock
        self.lock = RLock()
        self.sessions, self.attempts = {}, {}
        self.dummy = password_hash('contraseña-ficticia-sin-usuario')

    def user(self):
        try:
            data = json.loads(self.path.read_text())
            if data['algorithm'] != 'scrypt-v1' or len(bytes.fromhex(data['salt'])) != 16:
                raise ValueError
            if len(bytes.fromhex(data['hash'])) != 64: raise ValueError
            return data
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def login(self, username, password, ip):
        now = self.clock()
        # Reservar el intento antes de calcular scrypt: también limita peticiones concurrentes.
        with self.lock:
            self.attempts = {key: value for key, value in self.attempts.items() if value[1] > now}
            count, until = self.attempts.get(ip, (0, now + 900))
            if count >= 5 or len(self.attempts) >= 4096: return None, 429
            self.attempts[ip] = (count + 1, until)
        user = self.user()
        reference = user or self.dummy
        try:
            key = hashlib.scrypt(password.encode(), salt=bytes.fromhex(reference['salt']), **PARAMS)
            valid = hmac.compare_digest(key.hex(), reference['hash'])
        except (ValueError, UnicodeError):
            valid = False
        if not user or not valid or not hmac.compare_digest(username.encode(), user['username'].encode()):
            return None, 401
        with self.lock:
            self.attempts.pop(ip, None)
            self.sessions = {key: value for key, value in self.sessions.items() if value > now}
            if len(self.sessions) >= 128: return None, 429
            session = secrets.token_urlsafe(32)
            self.sessions[hashlib.sha256(session.encode()).hexdigest()] = now + 8 * 3600
        return session, 200

    def authenticated(self, value):
        key = hashlib.sha256(value.encode()).hexdigest()
        with self.lock:
            expiry = self.sessions.get(key, 0)
            if expiry <= self.clock():
                self.sessions.pop(key, None)
                return False
            return True

    def logout(self, value):
        with self.lock:
            self.sessions.pop(hashlib.sha256(value.encode()).hexdigest(), None)


def routes(auth, public_host):
    async def login(request):
        if request.method == 'GET':
            nonce = secrets.token_urlsafe(32)
            html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8">
            <meta name="viewport" content="width=device-width"><title>Acceso · Arkhé</title>
            <link rel="stylesheet" href="/assets/access.css"></head><body><main>
            <img src="/assets/mark.svg" width="48" alt=""><h1>Tu espacio Arkhé</h1>
            <p>Acceso privado al piloto docente.</p><form method="post" action="/login">
            <input type="hidden" name="csrf" value="{nonce}">
            <label>Usuario<input name="username" autocomplete="username" maxlength="64" required></label>
            <label>Contraseña<input name="password" type="password" autocomplete="current-password"
            maxlength="1024" required></label><button>Entrar</button></form>
            <p><a href="/privacy">Privacidad del piloto</a></p></main></body></html>'''
            response = HTMLResponse(html)
            response.set_cookie(CSRF, nonce, secure=True, httponly=True, samesite='strict', max_age=600)
            return response
        chunks, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 8192: return JSONResponse({'error': 'Solicitud demasiado grande.'}, status_code=413)
            chunks.append(chunk)
        if request.headers.get('origin') != 'https://' + public_host:
            return JSONResponse({'error': 'Origen de acceso inválido.'}, status_code=403)
        try:
            data = parse_qs(b''.join(chunks).decode(), strict_parsing=True)
            username, password = data['username'][0], data['password'][0]
            csrf = data['csrf'][0]
            if len(username) > 64 or not 1 <= len(password) <= 1024: raise ValueError
        except (ValueError, KeyError, UnicodeError):
            return JSONResponse({'error': 'Datos de acceso inválidos.'}, status_code=400)
        if not csrf or not hmac.compare_digest(csrf, request.cookies.get(CSRF, '')):
            return JSONResponse({'error': 'Recarga la pantalla de acceso.'}, status_code=403)
        session, status = await run_in_threadpool(auth.login, username, password, request.state.client_ip)
        if not session:
            message = 'Demasiados intentos. Espera 15 minutos.' if status == 429 else 'Usuario o contraseña incorrectos.'
            return HTMLResponse('<!doctype html><html lang="es"><head><meta charset="utf-8">'
                '<link rel="stylesheet" href="/assets/access.css"><title>Acceso · Arkhé</title></head>'
                '<body><main><h1>No se pudo acceder</h1><p>' + message + '</p>'
                '<a href="/login">Volver al acceso</a></main></body></html>', status_code=status,
                headers={'Retry-After': '900'} if status == 429 else {})
        response = RedirectResponse('/', status_code=303)
        response.set_cookie(COOKIE, session, secure=True, httponly=True, samesite='strict', max_age=8 * 3600)
        response.delete_cookie(CSRF, secure=True, httponly=True, samesite='strict')
        return response

    async def logout(request):
        auth.logout(request.cookies.get(COOKIE, ''))
        response = JSONResponse({'ok': True})
        response.delete_cookie(COOKIE, secure=True, httponly=True, samesite='strict')
        return response
    return login, logout
