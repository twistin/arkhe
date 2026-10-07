"""Reparaciones auditadas y estadísticas con corpus temporal y proveedores falsos."""

from copy import deepcopy
from dataclasses import replace
import json
import sqlite3

import httpx
import pytest

from docente_ai.cli import main
from docente_ai.generation.errors import GenerationLengthError, NetworkError, AuthorizationError
from docente_ai.generation.prompt import response_schema
from docente_ai.generation.repair import sanitize
from docente_ai.generation.service import ask, get_run, list_runs, run_stats, GenerationFailure
from docente_ai.generation.validation import validate_response, QuoteResolutionError
from docente_ai.library.service import authorize_document
from docente_ai.llm.deepseek import DeepSeekGenerator, DeepSeekError
from docente_ai.secrets import set_secret
from test_generation import corpus, FakeGenerator, FakeEmbedder, TEXT, run_ask
from test_pedagogy import proposal, perform


def valid():
    return {'status': 'answered', 'claims': [{'kind': 'summary', 'text': 'Referencia temporal.',
            'evidence': [{'source_id': 'S1', 'quote': 'quote_001'}]}], 'visualizations': []}


class SequenceGenerator(FakeGenerator):
    def __init__(self, outcomes):
        super().__init__()
        self.outcomes = outcomes
        self.dialogues = []

    def generate(self, messages):
        self.dialogues.append(deepcopy(messages))
        outcome = self.outcomes[min(len(self.dialogues) - 1, len(self.outcomes) - 1)]
        if isinstance(outcome, BaseException):
            raise outcome
        if callable(outcome):
            outcome = outcome()
        return {'content': outcome if isinstance(outcome, str) else json.dumps(outcome),
                'metrics': {'prompt_eval_count': 200, 'eval_count': 40}}


@pytest.mark.parametrize('mutation,error_type', [
    (lambda p: 'mal JSON', 'json_format'),
    (lambda p: {'status': 'answered'}, 'contract'),
    (lambda p: {**p, 'status': 'inventado'}, 'invalid_enum'),
    (lambda p: {**p, 'inventado': 1}, 'extra_fields'),
    (lambda p: {**p, 'claims': [{**p['claims'][0], 'page': 1}]}, 'extra_fields'),
    (lambda p: {**p, 'claims': [{**p['claims'][0], 'kind': 'inventado'}]}, 'invalid_enum'),
    (lambda p: {**p, 'claims': [{**p['claims'][0], 'evidence': [{'source_id': 'S1', 'quote': 'quote_999'}]}]}, 'quote_unresolved'),
    (lambda p: {**p, 'claims': [{**p['claims'][0], 'evidence': [{'source_id': 'S1', 'quote': 'quote_001', 'page': 1}]}]}, 'extra_fields'),
])
def test_reparable_luego_valido(corpus, mutation, error_type):
    generator = SequenceGenerator([mutation(valid()), valid()])
    result = run_ask(corpus, generator_factory=lambda _: generator)
    assert result['status'] == 'draft'
    assert len(list_runs(corpus[0])) == 1
    assert len(generator.dialogues) == 2
    metrics = result['metrics']['attempts']
    assert [a['error_type'] for a in metrics] == [error_type, None]
    assert metrics[0]['tokens'] == {'input': 200, 'output': 40}
    correction = json.loads(generator.dialogues[1][-1]['content'])
    assert correction['error_type'] == error_type and correction['repair'] is True
    assert generator.dialogues[1][-2]['role'] == 'assistant'
    assert response_schema(generator.dialogues[1])['properties']['claims']['items']['properties']['evidence']['items']['anyOf'][0]['properties']['quote']['enum'] == ['quote_001']


def test_dos_reintentos_y_nunca_borrador_invalido(corpus):
    data = valid()
    data['claims'][0]['evidence'][0]['quote'] = TEXT.replace('pulso', 'pulsos')
    generator = SequenceGenerator([data])
    with pytest.raises(GenerationFailure):
        run_ask(corpus, generator_factory=lambda _: generator)
    assert len(generator.dialogues) == 3
    run = get_run(corpus[0], list_runs(corpus[0])[0]['id'])
    assert run['status'] == 'failed' and run['result'] is None
    assert run['metrics']['error_type'] == 'quote_unresolved'
    assert len(run['metrics']['attempts']) == 3
    assert 'raw_response' not in run


def test_exito_en_tercer_intento(corpus):
    generator = SequenceGenerator(['mal JSON', {'status': 'inventado', 'claims': []}, valid()])
    result = run_ask(corpus, generator_factory=lambda _: generator)
    assert result['status'] == 'draft'
    assert [item['error_type'] for item in result['metrics']['attempts']] == ['json_format', 'invalid_enum', None]
    assert [len(messages) for messages in generator.dialogues] == [2, 4, 6]
    assert len(result['messages']) == 6


def test_length_es_solo_recuperable():
    from docente_ai.generation.errors import RecoverableGenerationError, NonRecoverableGenerationError
    error = GenerationLengthError('Truncada.')
    assert isinstance(error, RecoverableGenerationError)
    assert not isinstance(error, NonRecoverableGenerationError)


def test_cita_puntuacion_y_elipsis_no_se_aproximan():
    source = {'source_id': 'S1', 'text': 'The color is melodic. The talea is rhythmic.'}
    data = valid()
    for quote in ('the color is melodic', 'The color ... melodic.', 'The color is melodic!'):
        data['claims'][0]['evidence'][0]['quote'] = quote
        with pytest.raises(QuoteResolutionError):
            validate_response(json.dumps(data), [source])


def test_length_reduce_claims_sin_subir_tokens(corpus):
    generator = SequenceGenerator([GenerationLengthError('Salida truncada.', content='{"claims":[', metrics={'eval_count': 512}), valid()])
    result = run_ask(corpus, generator_factory=lambda _: generator)
    assert result['status'] == 'draft'
    correction = json.loads(generator.dialogues[1][-1]['content'])
    assert correction['max_claims'] == 5
    assert response_schema(generator.dialogues[1])['properties']['claims']['maxItems'] == 5
    assert result['request']['generation']['max_output_tokens'] == 512
    assert result['metrics']['attempts'][0]['tokens']['output'] == 512


@pytest.mark.parametrize('error', [NetworkError('Red.'), AuthorizationError('Autorización.'), KeyboardInterrupt()])
def test_no_reparar_red_autorizacion_cancelacion(corpus, error):
    generator = SequenceGenerator([error, valid()])
    with pytest.raises(KeyboardInterrupt if isinstance(error, KeyboardInterrupt) else GenerationFailure):
        run_ask(corpus, generator_factory=lambda _: generator)
    assert len(generator.dialogues) == 1
    assert list_runs(corpus[0])[0]['status'] != 'draft'


def test_fuente_excluida_no_se_reintenta(corpus):
    def invalid_and_exclude():
        authorize_document(corpus[0], corpus[1]['document_id'], enabled=False)
        return {'status': 'inventado'}
    generator = SequenceGenerator([invalid_and_exclude, valid()])
    with pytest.raises(GenerationFailure):
        run_ask(corpus, generator_factory=lambda _: generator)
    assert len(generator.dialogues) == 1
    run = get_run(corpus[0], list_runs(corpus[0])[0]['id'])
    assert run['metrics']['error_type'] == 'source_changed'


def test_reparacion_pedagogica_mantiene_plan_y_fuentes(corpus):
    invalid = proposal()
    invalid['plan']['activities'][0]['claim_ids'] = [99]
    generator = SequenceGenerator([invalid, proposal()])
    result = perform(corpus, generator_factory=lambda _: generator)
    assert result['status'] == 'draft' and len(generator.dialogues) == 2
    schema = response_schema(generator.dialogues[1])
    assert 'plan' in schema['required']
    assert schema['properties']['claims']['items']['properties']['evidence']['items']['anyOf']


@pytest.mark.parametrize('evidencias', [[], None, {}, [{'source_id': 'S1', 'quote': 'quote_001'}] * 31])
def test_ampliacion_sin_evidencias_se_repara_sin_inventar_citas(corpus, evidencias):
    invalida = proposal()
    invalida['claims'] += [deepcopy(invalida['claims'][0]), {
        'kind': 'summary', 'text': 'Contenido adicional sin respaldo.', 'evidence': evidencias,
    }]
    invalida['plan']['activities'][1]['claim_ids'] = [3]
    generator = SequenceGenerator([invalida, proposal()])
    result = perform(corpus, generator_factory=lambda _: generator)
    assert result['status'] == 'draft'
    assert result['result']['plan'] == proposal()['plan']
    assert len(result['result']['claims']) == 1
    assert [a['error_type'] for a in result['metrics']['attempts']] == ['evidence_count', None]
    instruccion = json.loads(generator.dialogues[1][-1]['content'])['instruction']
    assert 'actualiza todos los claim_ids' in instruccion
    assert 'no le asignes citas de otro bloque por defecto' in instruccion
    assert result['result']['claims'][0]['evidence'][0]['quote'] in TEXT


def test_ampliacion_sin_respaldo_persistente_no_publica_borrador(corpus):
    invalida = proposal()
    invalida['claims'][0]['evidence'] = []
    generator = SequenceGenerator([invalida])
    with pytest.raises(GenerationFailure):
        perform(corpus, generator_factory=lambda _: generator)
    run = get_run(corpus[0], list_runs(corpus[0])[0]['id'])
    assert run['status'] == 'failed' and run['result'] is None
    assert run['metrics']['error_type'] == 'evidence_count'
    assert len(generator.dialogues) == 3


def test_saneado_no_toca_textos_y_se_audita(corpus):
    data = valid()
    data['claims'][0]['evidence'][0]['page'] = 123
    sanitized, removed = sanitize(json.dumps(data))
    assert removed == ['claims[0].evidence[0].page']
    assert json.loads(sanitized)['claims'][0]['text'] == data['claims'][0]['text']
    assert json.loads(sanitized)['claims'][0]['evidence'][0]['quote'] == 'quote_001'
    generator = SequenceGenerator([data])
    db, _, rag, settings = corpus
    remote = replace(settings, provider='deepseek', data_residency='')
    remote = replace(remote, remote_consent=remote.consent_scope)
    result = ask(db, rag, remote, 'Pulso', subject='historia-i',
                 embedder_factory=FakeEmbedder, generator_factory=lambda _: generator)
    assert result['status'] == 'draft'
    assert result['metrics']['attempts'][0]['sanitized_fields'] == removed
    assert len(generator.dialogues) == 1


def test_saneado_solo_evidence_y_visualizations():
    data = valid()
    data['page'] = 1
    data['claims'][0]['page'] = 2
    data['visualizations'] = [{'type': 'table', 'title': 'Tabla', 'caption': 'Relación', 'extra': True,
        'items': [{'label': 'A', 'detail': 'Texto intacto', 'extra': 4}, {'label': 'B', 'detail': 'Otro texto'}],
        'evidence': [{'source_id': 'S1', 'quote': 'quote_001', 'page': 3}]}]
    sanitized, removed = sanitize(json.dumps(data))
    result = json.loads(sanitized)
    assert result['page'] == 1 and result['claims'][0]['page'] == 2
    assert result['visualizations'][0]['items'][0]['detail'] == 'Texto intacto'
    assert len(removed) == 3


def setup_deepseek(monkeypatch, handler):
    set_secret('deepseek_api_key', 'sk-' + 'C' * 32)
    original = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda **kw: original(**kw, transport=httpx.MockTransport(handler)))
    pauses = []
    monkeypatch.setattr('docente_ai.llm.deepseek.time.sleep', pauses.append)
    from docente_ai.generation.settings import GenerationSettings
    settings = GenerationSettings('deepseek-chat', provider='deepseek')
    return DeepSeekGenerator(replace(settings, remote_consent=settings.consent_scope)), pauses


def response(finish='stop'):
    return httpx.Response(200, json={'choices': [{'finish_reason': finish, 'message': {'content': json.dumps(valid())}}],
                                   'usage': {'prompt_tokens': 120, 'completion_tokens': 50}})


@pytest.mark.parametrize('status', [429, 500, 503, 'timeout'])
def test_deepseek_un_reintento_backoff(monkeypatch, status):
    calls = []
    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            if status == 'timeout':
                raise httpx.ReadTimeout('Timeout', request=request)
            return httpx.Response(status)
        return response()
    generator, pauses = setup_deepseek(monkeypatch, handler)
    with generator:
        result = generator.generate([{'role': 'user', 'content': 'Pregunta'}])
    assert len(calls) == 2 and pauses == [0.5]
    assert result['metrics']['transport_retries'] == 1
    payload = json.loads(calls[0].content)
    assert payload['response_format'] == {'type': 'json_object'}
    assert 'JSON' in payload['messages'][0]['content']


@pytest.mark.parametrize('status,cls', [(401, AuthorizationError), (403, AuthorizationError), (400, DeepSeekError), (503, NetworkError)])
def test_deepseek_fallos_acotados(monkeypatch, status, cls):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status)
    generator, pauses = setup_deepseek(monkeypatch, handler)
    with generator, pytest.raises(cls):
        generator.generate([{'role': 'user', 'content': 'Pregunta'}])
    assert len(calls) == (2 if status == 503 else 1)
    assert len(pauses) == (1 if status == 503 else 0)


def test_deepseek_esquema_y_quote_permitidos(monkeypatch):
    calls = []
    def handler(request):
        calls.append(request)
        return response('length')
    generator, _ = setup_deepseek(monkeypatch, handler)
    from docente_ai.generation.prompt import make_messages
    messages = make_messages('Pulso', [{'source_id': 'S1', 'text': TEXT, 'category': 'documental'}])
    with generator, pytest.raises(GenerationLengthError) as error:
        generator.generate(messages)
    payload = json.loads(calls[0].content)
    assert 'quote_001' in payload['messages'][0]['content']
    assert 'additionalProperties' in payload['messages'][0]['content']
    assert error.value.metrics['eval_count'] == 50
    assert error.value.content == json.dumps(valid())
    assert messages[0]['content'] != payload['messages'][0]['content']


def test_stats_cli_y_limite(corpus, capsys):
    generator = SequenceGenerator(['invalido', valid()])
    run_ask(corpus, generator_factory=lambda _: generator)
    with pytest.raises(GenerationFailure):
        run_ask(corpus, generator_factory=lambda _: SequenceGenerator(['invalido']))
    run_ask(corpus, generator_factory=lambda _: SequenceGenerator([{'status': 'insufficient_sources', 'claims': [], 'visualizations': []}]))
    stats = run_stats(corpus[0], 100)
    assert stats['total'] == 3
    assert stats['counts']['draft'] == stats['counts']['failed'] == stats['counts']['abstained'] == 1
    assert stats['rates']['draft'] == 33.33
    assert stats['errors'] == {'json_format': 1}
    assert stats['repaired_drafts'] == 1
    assert run_stats(corpus[0], 1)['total'] == 1
    assert main(['runs', 'stats', '--db', str(corpus[0]), '--limit', '3', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['total'] == 3
    with pytest.raises(ValueError):
        run_stats(corpus[0], 0)


def test_stats_vacio_y_historico_sin_tipo(corpus):
    assert run_stats(corpus[0])['total'] == 0
    assert run_stats(corpus[0])['rates']['draft'] == 0
    with pytest.raises(GenerationFailure):
        run_ask(corpus, generator_factory=lambda _: SequenceGenerator(['invalido']))
    with sqlite3.connect(corpus[0]) as connection:
        connection.execute("UPDATE generation_runs SET metrics_json='{}'")
    assert run_stats(corpus[0])['errors'] == {'legacy_untyped': 1}
