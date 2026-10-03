"""Lanzador local sin procesos ni configuración global adicionales."""

import socket
import hashlib
import httpx
from threading import Timer
import webbrowser

import uvicorn

from docente_ai.web.app import create_app


def launch(args):
    host = getattr(args, 'host', '127.0.0.1') or '127.0.0.1'
    if not 1024 <= args.port <= 65535:
        raise ValueError('El puerto debe estar entre 1024 y 65535.')
    # Bind before opening the browser so an occupied port never opens another app.
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, args.port))
        except OSError:
            url = f'http://127.0.0.1:{args.port}'
            try:
                with httpx.Client(timeout=2, trust_env=False) as client:
                    response = client.get(url)
                workspace_id = hashlib.sha256(str(args.workspace.resolve()).encode()).hexdigest()
                if workspace_id in [response.headers.get('X-Arkhe-Workspace'),
                                    response.headers.get('X-Enjambre-Workspace')]:
                    if not args.no_browser:
                        webbrowser.open(url)
                    print(f'Arkhé ya está abierto: {url}')
                    return 0
            except httpx.HTTPError:
                pass
            raise ValueError('El puerto está ocupado por otro servicio. Elige otro con --port.') from None
        allowed_hosts = [f'{host}:{args.port}', host] if host != '127.0.0.1' else []
        app = create_app(args.workspace, port=args.port, allowed_hosts=allowed_hosts)
        local_url = f'http://{"127.0.0.1" if host == "0.0.0.0" else host}:{args.port}'
        print(f'Arkhé · {local_url}\nBiblioteca: {app.state.workspace.knowledge}', flush=True)
        if host == '0.0.0.0':
            print('Acceso remoto activado para Tailscale y red local.')
        timer = None
        if not args.no_browser:
            timer = Timer(1.2, lambda: webbrowser.open(local_url))
            timer.daemon = True
            timer.start()
        try:
            server = uvicorn.Server(uvicorn.Config(app, host=host, port=args.port, log_level='warning', access_log=False))
            app.state.shutdown = lambda: setattr(server, 'should_exit', True)
            server.run(sockets=[sock])
        finally:
            if timer:
                timer.cancel()
    return 0
