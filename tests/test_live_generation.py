"""Progreso SSE y cancelación con corpus y transportes estrictamente sintéticos."""

import json
from threading import Event

import httpx
import pytest

from docente_ai.generation.live import LiveExecution, current_execution, emit_live, live_transport
from docente_ai.generation.service import ask, get_run
from docente_ai.llm.generation import OllamaGenerator
from docente_ai.llm.openai_compatible import OpenAICompatibleGenerator
from docente_ai.generation.settings import GenerationSettings
from test_generation import FakeGenerator, FakeEmbedder, TEXT, mock_chat
from test_web import web, add, wait


def events(response):
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    result = []
    for block in response.text.strip().split('\n\n'):
        lines = dict(line.split(':', 1) for line in block.splitlines() if ':' in line)
        if 'data' in lines:
            result.append({'event': lines['event'].strip(), 'id': int(lines['id']),
                           'data': json.loads(lines['data'])})
    return result


class StreamingFake(FakeGenerator):
    def generate_stream(self, messages, on_chunk):
        response = super().generate(messages)
        for start in range(0, len(response['content']), 17):
            current_execution().check()
            on_chunk(response['content'][start:start + 17])
        return response


def ready(web):
    client, ws = web
    doc, _ = add(web)
    client.post('/api/documents/' + doc + '/authorize', json={})
    assert wait(ws)['status'] == 'done'
    return client, ws


def test_sse_generador_streaming_repara_y_solo_publica_resultado_validado(web):
    client, ws = ready(web)
    calls = []
    class Repairing(StreamingFake):
        def generate_stream(self, messages, on_chunk):
            calls.append(messages)
            if len(calls) == 1:
                on_chunk('{"status":"incorrecto","claims":[]}')
                return {'content': '{"status":"incorrecto","claims":[]}', 'metrics': {'eval_count': 9}}
            return super().generate_stream(messages, on_chunk)
    ws.ask_function = lambda *args, **kw: ask(*args, **kw, embedder_factory=FakeEmbedder,
                                             generator_factory=Repairing)
    response = client.post('/api/generate', json={'mode': 'ask', 'subject': 'historia-i', 'question': 'El pulso'})
    identifier = response.json()['job_id']
    assert wait(ws)['status'] == 'done'
    stream = events(client.get(f'/api/jobs/{identifier}/events'))
    names = [event['event'] for event in stream]
    assert names[0] == 'stage' and names[-1] == 'terminal'
    assert names.count('attempt') == 2 and names.count('repair') == 1
    assert names.count('token') > 2 and 'usage' in names
    assert 'quote' in ''.join(event['data']['text'] for event in stream if event['event'] == 'token')
    terminal = stream[-1]['data']
    run = client.get('/api/runs/' + terminal['result']['run_id']).json()
    assert run['status'] == 'draft'
    assert len(get_run(ws.db, run['id'])['metrics']['attempts']) == 2
    cursor = next(event['id'] for event in stream if event['event'] == 'repair')
    resumed = events(client.get(f'/api/jobs/{identifier}/events', headers={'Last-Event-ID': str(cursor)}))
    assert all(event['id'] > cursor for event in resumed)
    assert 'incorrecto' not in ''.join(event['data'].get('text', '') for event in resumed)
    assert ws.live_jobs[identifier]['text'] == ''
    assert client.get(f'/api/jobs/{identifier}/events', headers={'X-Docente-Token': 'invalido'}).status_code == 403
    assert client.get('/api/jobs/inexistente/events').status_code == 404
    assert client.get(f'/api/jobs/{identifier}/events?after=-1').status_code == 400


def test_cancelacion_cierra_peticion_y_sqlite_nunca_publica_el_borrador(web):
    client, ws = ready(web)
    started, closed = Event(), Event()
    class Blocking(StreamingFake):
        def close(self): closed.set()
        def generate_stream(self, messages, on_chunk):
            with live_transport(self):
                on_chunk('{"status":"answered","claims":[{"text":"Todavía sin verificar')
                started.set()
                assert closed.wait(5), 'La cancelación no cerró el transporte.'
            raise AssertionError('No debe continuar después de cancelar.')
    ws.ask_function = lambda *args, **kw: ask(*args, **kw, embedder_factory=FakeEmbedder,
                                             generator_factory=Blocking)
    identifier = client.post('/api/generate', json={
        'mode': 'ask', 'subject': 'historia-i', 'question': 'El pulso'}).json()['job_id']
    assert started.wait(5)
    run_id = ws.live_jobs[identifier]['control'].run_id
    assert get_run(ws.db, run_id)['status'] != 'draft'
    assert client.post(f'/api/jobs/{identifier}/cancel', json={}).json()['accepted'] is True
    assert closed.is_set()
    assert wait(ws)['status'] == 'cancelled'
    stream = events(client.get(f'/api/jobs/{identifier}/events'))
    assert stream[-1]['data']['status'] == 'cancelled'
    record = get_run(ws.db, run_id)
    assert record['status'] == 'cancelled' and record['result'] is None
    assert ws.live_jobs[identifier]['text'] == ''
    assert client.post(f'/api/jobs/{identifier}/cancel', json={}).json()['accepted'] is False


def test_citas_alteradas_streaming_siguen_rechazadas_tras_reparacion(web):
    client, ws = ready(web)
    class Altered(StreamingFake):
        def __init__(self, settings):
            super().__init__(settings, response={'status': 'answered', 'claims': [{
                'kind': 'summary', 'text': 'No válido', 'evidence': [{'source_id': 'S1', 'quote': TEXT + ' inventado'}]}]})
    ws.ask_function = lambda *args, **kw: ask(*args, **kw, embedder_factory=FakeEmbedder,
                                             generator_factory=Altered)
    identifier = client.post('/api/generate', json={
        'mode': 'ask', 'subject': 'historia-i', 'question': 'El pulso'}).json()['job_id']
    assert wait(ws)['status'] == 'failed'
    stream = events(client.get(f'/api/jobs/{identifier}/events'))
    assert sum(event['event'] == 'repair' for event in stream) == 2
    assert stream[-1]['data']['status'] == 'failed'
    runs = client.get('/api/state').json()['runs']
    assert runs[0]['status'] == 'failed'
    run = get_run(ws.db, runs[0]['id'])
    assert run['result'] is None and len(run['metrics']['attempts']) == 3


def test_sse_lotes_y_reconexion_acotada(web):
    client, ws = web
    def operation():
        emit_live('relevance', batch=1, total=2)
        emit_live('relevance', batch=2, total=2)
        for i in range(1100): emit_live('token', text='a', attempt=1)
        return {'ok': True}
    identifier = ws.submit('Prueba', operation)['job_id']
    wait(ws)
    stream = events(client.get(f'/api/jobs/{identifier}/events'))
    assert stream[0]['event'] == 'snapshot' and stream[0]['data']['status'] == 'done'
    assert len(ws.live_jobs[identifier]['events']) == 1024
    unknown_cursor = events(client.get(f'/api/jobs/{identifier}/events?after=99999'))
    assert unknown_cursor[0]['event'] == 'snapshot'
    identifier = ws.submit('Lotes', lambda: emit_live('relevance', batch=1, total=1))['job_id']
    wait(ws)
    assert any(event['event'] == 'relevance' for event in events(client.get(f'/api/jobs/{identifier}/events')))


def test_ollama_streaming_ndjson_conserva_validacion_de_fin():
    transport, _ = mock_chat()
    original = transport.handle_request
    def handle(request):
        if request.url.path == '/api/chat':
            assert json.loads(request.content)['stream'] is True
            rows = [
                {'message': {'role': 'assistant', 'content': '{"status":'}, 'done': False},
                {'message': {'role': 'assistant', 'content': '"abstained","claims":[]}'}, 'done': False},
                {'message': {'role': 'assistant', 'content': ''}, 'done': True, 'done_reason': 'stop',
                 'prompt_eval_count': 30, 'eval_count': 8},
            ]
            return httpx.Response(200, text='\n'.join(json.dumps(row) for row in rows))
        return original(request)
    chunks = []
    with OllamaGenerator(GenerationSettings('gen:1'), transport=httpx.MockTransport(handle)) as generator:
        result = generator.generate_stream([{'role': 'user', 'content': 'Prueba'}], chunks.append)
    assert result['content'] == ''.join(chunks)
    assert json.loads(result['content'])['status'] == 'abstained'
    assert result['metrics']['eval_count'] == 8


def test_remoto_streaming_no_expone_razonamiento_y_tokens_ausentes_no_son_cero():
    settings = GenerationSettings('deepseek-chat', provider='deepseek')
    generator = OpenAICompatibleGenerator(settings)
    def handle(request):
        body = json.loads(request.content)
        assert body['stream'] is True
        assert 'JSON' in body['messages'][0]['content']
        rows = [
            {'choices': [{'delta': {'reasoning_content': 'razonamiento privado'}, 'finish_reason': None}]},
            {'choices': [{'delta': {'content': '{"status":"abstained",'}, 'finish_reason': None}]},
            {'choices': [{'delta': {'content': '"claims":[]}'}, 'finish_reason': 'stop'}]},
        ]
        return httpx.Response(200, text='\n\n'.join('data: ' + json.dumps(row) for row in rows) + '\n\ndata: [DONE]\n\n')
    generator.client = httpx.Client(base_url='https://proveedor.invalid/', transport=httpx.MockTransport(handle))
    try:
        chunks = []
        result = generator.generate_stream([{'role': 'system', 'content': 'Prueba'}], chunks.append)
        assert result['content'] == ''.join(chunks)
        assert 'privado' not in str(result)
        assert result['metrics']['eval_count'] is None
    finally:
        generator.client.close()


def test_endpoint_entrega_eventos_antes_de_validar_sin_esperar_al_resultado(web):
    from concurrent.futures import ThreadPoolExecutor
    from starlette.testclient import TestClient
    client, ws = ready(web)
    drafting, delivered, release = Event(), Event(), Event()
    class Paused(StreamingFake):
        def generate_stream(self, messages, on_chunk):
            on_chunk('{"status":')
            drafting.set()
            assert release.wait(5)
            return super().generate_stream(messages, on_chunk)
    ws.ask_function = lambda *args, **kw: ask(*args, **kw, embedder_factory=FakeEmbedder,
                                             generator_factory=Paused)
    identifier = client.post('/api/generate', json={
        'mode': 'ask', 'subject': 'historia-i', 'question': 'El pulso'}).json()['job_id']
    assert drafting.wait(5)
    async def observed(scope, receive, send):
        async def capture(message):
            if message['type'] == 'http.response.body' and b'event: token' in message.get('body', b''):
                delivered.set()
            await send(message)
        await client.app(scope, receive, capture)
    with TestClient(observed, base_url='http://127.0.0.1:8765') as observer, ThreadPoolExecutor() as pool:
        response = pool.submit(observer.get, f'/api/jobs/{identifier}/events', headers=dict(client.headers))
        try:
            assert delivered.wait(5), 'SSE debe enviar deltas antes de completar la generación.'
            assert not response.done()
            assert get_run(ws.db, ws.live_jobs[identifier]['control'].run_id)['status'] != 'draft'
        finally:
            release.set()
        assert events(response.result(timeout=5))[-1]['data']['status'] == 'done'


def test_cancelar_en_cola_no_llama_al_proveedor(web):
    client, ws = web
    release = Event()
    ws.submit('Tarea anterior', lambda: release.wait(5))
    called = []
    identifier = ws.submit('En cola', lambda: called.append(True), cancellable=True)['job_id']
    try:
        response = client.post(f'/api/jobs/{identifier}/cancel', json={})
        assert response.json()['accepted'] is True
        stream = events(client.get(f'/api/jobs/{identifier}/events'))
        assert stream[-1]['data']['status'] == 'cancelled'
        assert called == []
    finally:
        release.set()
        wait(ws)


def test_cancelacion_interrumpe_socket_antes_de_cabeceras():
    closed = []
    class Socket:
        def shutdown(self, how): closed.append('shutdown')
    class Network:
        def get_extra_info(self, name):
            assert name == 'socket'
            return Socket()
        def close(self): closed.append('close')
    control = LiveExecution(lambda *args, **kwargs: None)
    control.trace('connection.connect_tcp.complete', {'return_value': Network()})
    assert control.cancel() is True
    assert closed == ['shutdown', 'close']
    from docente_ai.generation.live import GenerationCancelled
    with pytest.raises(GenerationCancelled): control.check()


def test_generador_sin_streaming_entrega_solo_etapas_y_resultado_final(web):
    client, ws = ready(web)
    class Complete(StreamingFake):
        supports_streaming = False
        def generate_stream(self, *args): raise AssertionError('Capacidad no declarada.')
    ws.ask_function = lambda *args, **kw: ask(*args, **kw, embedder_factory=FakeEmbedder,
                                             generator_factory=Complete)
    identifier = client.post('/api/generate', json={
        'mode': 'ask', 'subject': 'historia-i', 'question': 'El pulso'}).json()['job_id']
    assert wait(ws)['status'] == 'done'
    stream = events(client.get(f'/api/jobs/{identifier}/events'))
    assert not any(event['event'] == 'token' for event in stream)
    assert any(event['event'] == 'streaming' and event['data']['enabled'] is False for event in stream)


def test_propuesta_utiliza_el_mismo_streaming_y_validacion(web):
    from test_pedagogy import proposal
    client, ws = ready(web)
    config = ws.root / 'config/pedagogy.yaml'  # Solo el espacio temporal del fixture.
    config.write_text(config.read_text().replace('num_ctx: 6144', 'num_ctx: 8192'))
    ws.ask_function = lambda *args, **kw: ask(*args, **kw, embedder_factory=FakeEmbedder,
        generator_factory=lambda settings: StreamingFake(settings, response=proposal()))
    identifier = client.post('/api/generate', json={
        'mode': 'pedagogy', 'group': 'historia-3gp', 'duration': 30,
        'question': 'El pulso'}).json()['job_id']
    job = wait(ws)
    assert job['status'] == 'done', job
    stream = events(client.get(f'/api/jobs/{identifier}/events'))
    assert any(event['event'] == 'token' for event in stream)
    assert get_run(ws.db, job['result']['run_id'])['result']['plan'] is not None


@pytest.mark.parametrize('status,requests', [(401, 1), (403, 1), (429, 2), (503, 2)])
def test_streaming_remoto_reintenta_solo_errores_transitorios(monkeypatch, status, requests):
    from docente_ai.generation.errors import AuthorizationError
    monkeypatch.setattr('docente_ai.llm.openai_compatible.time.sleep', lambda _: None)
    generator = OpenAICompatibleGenerator(GenerationSettings('deepseek-chat', provider='deepseek'))
    calls = []
    def handle(request):
        calls.append(request)
        if len(calls) == 1: return httpx.Response(status)
        return httpx.Response(200, text='data: ' + json.dumps({'choices': [{
            'delta': {'content': '{"status":"abstained","claims":[]}'}, 'finish_reason': 'stop'}]}) + '\n\n')
    with httpx.Client(base_url='https://proveedor.invalid/', transport=httpx.MockTransport(handle)) as client:
        generator.client = client
        if status in (401, 403):
            with pytest.raises(AuthorizationError): generator.generate_stream([], lambda _: None)
        else:
            assert generator.generate_stream([], lambda _: None)['metrics']['transport_retries'] == 1
    assert len(calls) == requests


def test_length_streaming_repara_sin_aumentar_tokens(web):
    from docente_ai.generation.errors import GenerationLengthError
    client, ws = ready(web)
    messages_seen = []
    class Truncated(StreamingFake):
        def generate_stream(self, messages, on_chunk):
            messages_seen.append(messages)
            if len(messages_seen) == 1:
                on_chunk('{"status":"answered"')
                raise GenerationLengthError('Salida truncada.', content='{"status":"answered"',
                                             metrics={'eval_count': 100})
            return super().generate_stream(messages, on_chunk)
    ws.ask_function = lambda *args, **kw: ask(*args, **kw, embedder_factory=FakeEmbedder,
                                             generator_factory=Truncated)
    identifier = client.post('/api/generate', json={
        'mode': 'ask', 'subject': 'historia-i', 'question': 'El pulso'}).json()['job_id']
    job = wait(ws)
    assert job['status'] == 'done'
    stream = events(client.get(f'/api/jobs/{identifier}/events'))
    assert any(event['event'] == 'repair' and event['data']['error_type'] == 'length' for event in stream)
    instruction = json.loads(messages_seen[1][-1]['content'])
    assert instruction['max_claims'] == 5
    assert get_run(ws.db, job['result']['run_id'])['metrics']['attempts'][0]['tokens']['output'] == 100
