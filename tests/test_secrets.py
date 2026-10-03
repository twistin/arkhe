"""Credenciales y logging con Llavero simulado y archivos temporales."""

from dataclasses import asdict, replace
import io
import logging
import subprocess

import pytest
import yaml

from docente_ai import secrets
from docente_ai.generation.settings import load_settings


KEY = 'sk-' + 'A' * 32


def test_entorno_tiene_prioridad(monkeypatch, simulated_keychain):
    secrets.set_secret('deepseek_api_key', KEY)
    monkeypatch.setenv('DOCENTE_AI_DEEPSEEK_API_KEY', 'desde-entorno')
    monkeypatch.setattr(secrets.subprocess, 'run', lambda *a, **k: pytest.fail('No consultar Llavero'))
    assert secrets.get_secret('deepseek_api_key') == 'desde-entorno'


def test_llavero_y_borrado(simulated_keychain):
    assert secrets.get_secret('deepseek_api_key') is None
    secrets.set_secret('deepseek_api_key', KEY)
    assert secrets.get_secret('deepseek_api_key') == KEY
    secrets.delete_secret('deepseek_api_key')
    secrets.delete_secret('deepseek_api_key')
    assert secrets.get_secret('deepseek_api_key') is None


def test_sin_security(monkeypatch):
    monkeypatch.setattr(secrets.shutil, 'which', lambda _: None)
    with pytest.raises(ValueError, match='DOCENTE_AI_DEEPSEEK_API_KEY'):
        secrets.get_secret('deepseek_api_key')
    monkeypatch.setenv('DOCENTE_AI_DEEPSEEK_API_KEY', KEY)
    assert secrets.get_secret('deepseek_api_key') == KEY


def test_migracion_yaml_una_vez(tmp_path, simulated_keychain, caplog):
    path = tmp_path / 'antiguo.yaml'
    path.write_text(yaml.safe_dump({'schema_version': 1, 'generation': {
        'model': 'deepseek-chat', 'provider': 'deepseek', 'api_key': KEY}}))
    settings = load_settings(path)
    assert 'api_key' not in asdict(settings)
    assert 'api_key' not in yaml.safe_load(path.read_text())['generation']
    assert KEY not in path.read_text() and KEY not in caplog.text
    assert secrets.get_secret('deepseek_api_key') == KEY
    assert len(caplog.records) == 1
    load_settings(path)
    assert len(caplog.records) == 1


def test_migracion_fallida_preserva_original(tmp_path, monkeypatch):
    path = tmp_path / 'antiguo.yaml'
    original = yaml.safe_dump({'schema_version': 1, 'generation': {'model': 'gen:1', 'api_key': KEY}})
    path.write_text(original)
    monkeypatch.setattr(secrets.subprocess, 'run', lambda command, **kwargs: subprocess.CompletedProcess(command, 1, '', KEY))
    with pytest.raises(ValueError) as error:
        load_settings(path)
    assert KEY not in str(error.value)
    assert path.read_text() == original


def test_logs_enmascaran_mensajes_argumentos_y_excepciones():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger('prueba.credenciales')
    logger.addHandler(handler)
    try:
        logger.warning('Credencial %s', KEY)
        try:
            raise ValueError(KEY)
        except ValueError:
            logger.exception('Fallo con %s', KEY)
        assert KEY not in stream.getvalue()
        assert '[CLAVE OCULTA]' in stream.getvalue()
        assert any(isinstance(f, secrets.SecretFilter) for f in handler.filters)
    finally:
        logger.removeHandler(handler)


def test_error_de_proveedor_no_reenvia_credencial(monkeypatch):
    import httpx
    from docente_ai.generation.settings import GenerationSettings
    from docente_ai.llm.deepseek import DeepSeekGenerator, DeepSeekError
    secrets.set_secret('deepseek_api_key', KEY)
    original_client = httpx.Client

    def transport(request):
        assert request.headers['Authorization'] == 'Bearer ' + KEY
        return httpx.Response(401, json={'error': {'message': KEY}})

    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original_client(**kwargs, transport=httpx.MockTransport(transport)))
    settings = GenerationSettings('deepseek-chat', provider='deepseek')
    with DeepSeekGenerator(replace(settings, remote_consent=settings.consent_scope)) as generator:
        with pytest.raises(DeepSeekError) as error:
            generator._request('POST', '/chat/completions', {})
        assert KEY not in str(error.value)


def test_yaml_invalido_no_filtra_clave(tmp_path):
    path = tmp_path / 'invalido.yaml'
    path.write_text('generation: [' + KEY)
    with pytest.raises(ValueError) as error:
        load_settings(path)
    assert KEY not in str(error.value)


def test_redaccion_clave_entorno_sin_prefijo(monkeypatch):
    from docente_ai.secrets import redact
    monkeypatch.setenv('DOCENTE_AI_MISTRAL_API_KEY', 'credencial-sintetica-sin-prefijo')
    assert redact('Bearer credencial-sintetica-sin-prefijo') == 'Bearer [CLAVE OCULTA]'
