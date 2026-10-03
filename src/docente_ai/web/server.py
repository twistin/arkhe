"""Modo servidor explícito: origen único y frontera de confianza del proxy."""

from dataclasses import dataclass
import ipaddress
import re
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass(frozen=True)
class ServerSettings:
    public_host: str
    proxy_ip: str = '172.30.0.2'
    bind: str = '172.30.0.3'

    def __post_init__(self):
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', self.public_host) or '.' not in self.public_host:
            raise ValueError('public-host debe ser un dominio DNS sin protocolo, ruta ni puerto.')
        for address in (self.proxy_ip, self.bind):
            ip = ipaddress.ip_address(address)
            if not ip.is_private or ip.is_unspecified or ip.is_loopback:
                raise ValueError('El servidor y el proxy necesitan IP privadas explícitas de Docker.')


def public_data(value):
    """Ocultar solo campos de rutas: jamás modificar claims, citas ni metadatos textuales."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key == 'knowledge_path':
                result[key] = 'Biblioteca privada del servidor'
            elif key in {'source_path', 'original_path', 'folder', 'workspace_path'} and isinstance(item, str):
                result[key] = item.replace('\\', '/').rsplit('/', 1)[-1]
            else:
                result[key] = public_data(item)
        return result
    if isinstance(value, list):
        return [public_data(item) for item in value]
    return value


class ServerOnly(BaseHTTPMiddleware):
    def __init__(self, app, *, settings, token):
        super().__init__(app)
        self.settings, self.token = settings, token

    async def dispatch(self, request, call_next):
        host = request.headers.get('host', '')
        if host not in (self.settings.public_host, self.settings.public_host + ':443'):
            return JSONResponse({'error': 'Host público no permitido.'}, status_code=403)
        if request.client is None or request.client.host != self.settings.proxy_ip:
            return JSONResponse({'error': 'Solo se acepta el proxy configurado.'}, status_code=403)
        if request.headers.get('x-forwarded-proto') != 'https':
            return JSONResponse({'error': 'Se requiere HTTPS desde el proxy.'}, status_code=403)
        try:
            client_ip = str(ipaddress.ip_address(request.headers['x-forwarded-for']))
        except (KeyError, ValueError):
            return JSONResponse({'error': 'Dirección del cliente inválida.'}, status_code=403)
        request.state.client_ip = client_ip
        request.scope['scheme'] = 'https'
        origin = request.headers.get('origin')
        if origin and origin != 'https://' + self.settings.public_host:
            return JSONResponse({'error': 'Origen no permitido.'}, status_code=403)
        path = request.url.path
        if path in ('/api/shutdown', '/api/reveal', '/api/reveal-diary') or path.endswith('/reveal'):
            return JSONResponse({'error': 'Acción local desactivada; utiliza subida o descarga.'}, status_code=403)
        if path.startswith('/api/') and not secrets.compare_digest(request.headers.get('x-docente-token', ''), self.token):
            return JSONResponse({'error': 'La sesión ha caducado. Recarga la página.'}, status_code=403)
        response = await call_next(request)
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response


def serve(args):
    import uvicorn
    from docente_ai.web.app import create_app
    if not args.server:
        raise ValueError('serve requiere --server; utiliza ui para el modo local.')
    settings = ServerSettings(args.public_host, args.proxy_ip, args.bind)
    app = create_app(args.workspace, port=args.port, server=settings)
    uvicorn.run(app, host=settings.bind, port=args.port, proxy_headers=False, access_log=False, log_level='warning')
    return 0
