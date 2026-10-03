"""Contrato estático del despliegue y excepción mínima para Ollama interno."""
from pathlib import Path
import pytest
import yaml
from docente_ai.doctor import local_url

ROOT = Path(__file__).parents[1]


def test_compose_no_publica_backend_ni_ollama():
    data = yaml.safe_load((ROOT / 'docker-compose.yml').read_text())
    assert 'ports' not in data['services']['arkhe']
    assert 'ports' not in data['services']['ollama']
    assert data['networks']['privada']['internal'] is True
    assert data['services']['arkhe']['read_only'] is True
    assert 'arkhe_data:/datos/docente' in data['services']['arkhe']['volumes']
    assert 'ollama_models:/root/.ollama' in data['services']['ollama']['volumes']
    services = data['services']
    for left, right in [('arkhe', 'ollama'), ('caddy', 'arkhe'), ('caddy', 'ollama')]:
        assert set(services[left]['networks']) & set(services[right]['networks']) == {'privada'}
    dockerfile = (ROOT / 'Dockerfile').read_text()
    assert '--locked --no-dev' in dockerfile and 'USER 10001:10001' in dockerfile
    assert 'config/' not in dockerfile and 'Conocimiento/' not in dockerfile


def test_ollama_interno_no_relaja_validacion_local(monkeypatch):
    monkeypatch.delenv('ARKHE_SERVER_MODE', raising=False)
    with pytest.raises(ValueError): local_url('http://ollama:11434')
    monkeypatch.setenv('ARKHE_SERVER_MODE', '1')
    assert local_url('http://ollama:11434') == 'http://ollama:11434'
    for value in ('http://ollama:11434/api', 'http://otro:11434', 'http://169.254.169.254'):
        with pytest.raises(ValueError): local_url(value)
