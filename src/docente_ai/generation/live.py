"""Progreso efímero y cancelación cooperativa por ejecución, aislados por contexto."""

from contextlib import contextmanager
from contextvars import ContextVar
import socket
from threading import Event, RLock

from docente_ai.generation.errors import NonRecoverableGenerationError


class GenerationCancelled(NonRecoverableGenerationError):
    error_type = 'cancelled'


_current = ContextVar('docente_execution', default=None)


def current_execution():
    return _current.get()


def emit_live(event, **data):
    execution = current_execution()
    if execution:
        execution.emit(event, **data)


class LiveExecution:
    def __init__(self, emit):
        self.emit = emit
        self.cancelled = Event()
        self.lock = RLock()
        self.aborters = set()
        self.finished = False
        self.run_id = None

    @contextmanager
    def activate(self):
        token = _current.set(self)
        try:
            self.check()
            yield self
        finally:
            _current.reset(token)

    def check(self):
        if self.cancelled.is_set():
            raise GenerationCancelled('Consulta cancelada por el usuario.')

    def cancel(self):
        with self.lock:
            if self.finished:
                return False
            self.cancelled.set()
            callbacks = list(self.aborters)
        for callback in callbacks:
            try:
                callback()
            except (OSError, RuntimeError):
                pass
        return True

    def trace(self, event, info):
        # Capturar el socket antes de recibir cabeceras permite cancelar también esa espera.
        if event.endswith('connect_tcp.complete') or event.endswith('start_tls.complete'):
            stream = info.get('return_value')
            if stream:
                def abort():
                    sock = stream.get_extra_info('socket')
                    if sock:
                        try:
                            sock.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass
                    stream.close()
                with self.lock:
                    if self.cancelled.is_set():
                        abort()
                        self.check()
                    self.aborters.add(abort)

    @contextmanager
    def transport(self, resource):
        """Cerrar también el socket: interrumpir una lectura HTTP bloqueada."""
        def abort():
            stream = getattr(resource, 'extensions', {}).get('network_stream')
            if stream:
                sock = stream.get_extra_info('socket')
                if sock:
                    try:
                        sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
            resource.close()
        with self.lock:
            self.check()
            self.aborters.add(abort)
        try:
            yield
            self.check()
        except Exception:
            self.check()
            raise
        finally:
            with self.lock:
                self.aborters.discard(abort)

    def complete(self, operation):
        # Cancelar y publicar una versión validada son mutuamente excluyentes.
        with self.lock:
            self.check()
            result = operation()
            self.finished = True
            return result


@contextmanager
def live_transport(resource):
    execution = current_execution()
    if execution:
        with execution.transport(resource):
            yield
    else:
        yield


def generate_live(generator, messages, on_chunk):
    execution = current_execution()
    if execution:
        execution.check()
    if execution and getattr(generator, 'supports_streaming', True) and callable(
            getattr(generator, 'generate_stream', None)):
        emit_live('streaming', enabled=True)
        return generator.generate_stream(messages, on_chunk)
    if execution:
        emit_live('streaming', enabled=False)
    transport = live_transport(generator.client) if execution and hasattr(generator, 'client') else _empty()
    with transport:
        response = generator.generate(messages)
    if execution:
        execution.check()
    return response


@contextmanager
def _empty():
    yield


def transport_extensions():
    execution = current_execution()
    return {'trace': execution.trace} if execution else {}
