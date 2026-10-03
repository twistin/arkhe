"""Presets, consentimiento y límites de datos con proveedores simulados."""

from dataclasses import replace
from datetime import date
import json

import httpx
import pytest

from docente_ai.agents.pedagogy import context_for, build_prompt
from docente_ai.generation.settings import GenerationSettings, ConsentRequiredError, load_settings
from docente_ai.generation.service import ask
from docente_ai.llm.openai_compatible import OpenAICompatibleGenerator
from docente_ai.llm.presets import PRESETS
from docente_ai.record.service import add_record, add_feedback
from docente_ai.secrets import set_secret
from test_generation import corpus, FakeEmbedder, candidate
from test_repair import SequenceGenerator, valid
from test_pedagogy import proposal
from test_web import web


@pytest.mark.parametrize('provider,residence,mode', [('deepseek','fuera-ue','json_object'),('mistral','ue','json_schema'),('custom','desconocida','none')])
def test_presets(provider, residence, mode):
    settings = GenerationSettings('modelo', provider=provider, base_url='https://privado.example/v1' if provider == 'custom' else '')
    assert settings.data_residency == residence
    assert settings.response_format == mode
    assert not settings.remote_confirmed
    assert PRESETS[provider]['name'] in settings.indicator
    assert GenerationSettings('local:1').indicator == 'Generación local'
    assert GenerationSettings('deepseek-reasoner', provider='deepseek').response_format == 'none'


def test_residencia_no_puede_disfrazar_otro_endpoint():
    with pytest.raises(ValueError):
        GenerationSettings('modelo', provider='mistral', base_url='https://otro.example/v1')
    with pytest.raises(ValueError):
        GenerationSettings('modelo', provider='custom', base_url='https://otro.example/v1', data_residency='ue')
    for endpoint in ('http://otro.example', 'https://clave@otro.example', 'https://otro.example?api_key=x'):
        with pytest.raises(ValueError):
            GenerationSettings('modelo', provider='custom', base_url=endpoint)


def test_variable_portable_por_proveedor(monkeypatch):
    from docente_ai import secrets
    monkeypatch.setattr(secrets.shutil,'which',lambda _:None)
    with pytest.raises(ValueError,match='DOCENTE_AI_MISTRAL_API_KEY'):
        secrets.get_secret('mistral_api_key')
    monkeypatch.setenv('DOCENTE_AI_MISTRAL_API_KEY','clave-simulada')
    assert secrets.get_secret('mistral_api_key') == 'clave-simulada'


def test_sin_consentimiento_no_abrir_modelos_ni_cliente(corpus, monkeypatch):
    settings = GenerationSettings('deepseek-chat', provider='deepseek')
    def forbidden(*args, **kwargs):
        pytest.fail('No se debe enviar nada sin confirmación.')
    monkeypatch.setattr(httpx, 'Client', forbidden)
    with pytest.raises(ConsentRequiredError):
        OpenAICompatibleGenerator(settings).__enter__()
    with pytest.raises(ConsentRequiredError):
        ask(corpus[0], corpus[2], settings, 'Pulso', subject='historia-i', embedder_factory=forbidden, generator_factory=forbidden)


def test_confirmacion_persistida_y_reconfirmacion_por_cambio(web):
    client, ws = web
    assert client.post('/api/models', json={'provider':'mistral','generation':'mistral-small-latest'}).status_code == 200
    state = client.get('/api/state').json()
    info = state['provider_info']
    assert info['data_residency'] == 'ue' and not info['remote_confirmed']
    assert client.post('/api/generate', json={'mode':'ask','question':'Pulso','subject':'historia-i'}).status_code == 400
    assert client.post('/api/provider/confirm', json={'consent_scope':info['consent_scope'], 'confirmed':False}).status_code == 400
    assert client.post('/api/provider/confirm', json={'consent_scope':'obsoleto', 'confirmed':True}).status_code == 400
    assert client.post('/api/provider/confirm', json={'consent_scope':info['consent_scope'], 'confirmed':True}).status_code == 200
    for name in ('generation','pedagogy'):
        assert load_settings(ws.root / f'config/{name}.yaml').remote_confirmed
    assert client.post('/api/models', json={'provider':'custom','generation':'modelo','base_url':'https://privado.example/v1'}).status_code == 200
    assert not client.get('/api/state').json()['provider_info']['remote_confirmed']
    assert 'generation-indicator' in client.get('/').text
    script = client.get('/assets/js/componentes/consentimiento.js').text
    import re
    fragments = ''.join(re.findall(r'`([^`]+)`', script))
    assert 'Nunca se envían documentos completos, registros del diario ni feedback de sesiones' in fragments
    assert 'ensureRemoteConsent' in script


@pytest.mark.parametrize('provider,format', [('deepseek','json_object'),('mistral','json_schema'),('custom','none')])
def test_adaptador_destinos_y_capacidades(monkeypatch, provider, format):
    settings = GenerationSettings('modelo', provider=provider, base_url='https://privado.example/v1' if provider == 'custom' else '')
    settings = replace(settings, remote_consent=settings.consent_scope)
    set_secret(settings.secret_name, 'sk-' + 'Z' * 32)
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(valid())}}]})
    original = httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kw: original(**kw,transport=httpx.MockTransport(handler)))
    with OpenAICompatibleGenerator(settings) as generator:
        generator.generate([{'role':'user','content':'Pregunta'}])
    assert str(calls[0].url) == settings.base_url + '/chat/completions'
    payload = json.loads(calls[0].content)
    assert 'JSON' in payload['messages'][0]['content']
    if format == 'none':
        assert 'response_format' not in payload
    else:
        assert payload['response_format']['type'] == format
    if format == 'json_schema':
        assert payload['response_format']['json_schema']['strict'] is True


@pytest.mark.parametrize('provider',['deepseek','mistral','custom'])
def test_diario_no_entra_en_prompts_remotos(corpus, provider):
    db, _, rag, _ = corpus
    record = add_record(db,'historia-3gp',date(2026,10,2),30,'TEMA PRIVADO DEL DIARIO',notes='NOTAS PRIVADAS DEL DIARIO')
    add_feedback(db,record['id'],what_worked='FEEDBACK PRIVADO DEL DIARIO')
    context = context_for(db,'historia-3gp',30,criteria='Criterio explícito para esta consulta')
    assert context['prior_experience']
    settings = GenerationSettings('modelo',provider=provider,base_url='https://privado.example/v1' if provider == 'custom' else '',num_ctx=16384,max_output_tokens=1536)
    settings = replace(settings,remote_consent=settings.consent_scope)
    generator = SequenceGenerator([proposal()])
    result = ask(db,rag,settings,'Pulso',subject='historia-i',pedagogy_context=context,
                 embedder_factory=FakeEmbedder,generator_factory=lambda _:generator)
    assert result['status'] == 'draft'
    messages = json.dumps(generator.dialogues,ensure_ascii=False)
    for marker in ('TEMA PRIVADO DEL DIARIO','NOTAS PRIVADAS DEL DIARIO','FEEDBACK PRIVADO DEL DIARIO','prior_experience','session_records','session_feedback'):
        assert marker not in messages
    payload = json.loads(generator.dialogues[0][1]['content'])
    assert set(payload['context']) == {'group','duration_minutes','teacher_criteria','unit'}
    assert 'Criterio explícito' in messages
    local = build_prompt('Pulso',[candidate(corpus)],replace(corpus[3],num_ctx=16384),context)
    assert 'FEEDBACK PRIVADO DEL DIARIO' in json.dumps(local['messages'])
