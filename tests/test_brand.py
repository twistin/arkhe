"""Marca visible y compatibilidad con los lanzadores anteriores, sin sockets reales."""

import hashlib
import importlib.util
from pathlib import Path
import plistlib
from types import SimpleNamespace

import httpx
import pytest

from docente_ai.web.launch import launch

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('header', ['X-Arkhe-Workspace', 'X-Enjambre-Workspace'])
def test_lanzador_reutiliza_servidor_con_ambas_cabeceras(tmp_path, monkeypatch, capsys, header):
    class SocketOcupado:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def setsockopt(self, *args): pass
        def bind(self, *args): raise OSError('Puerto ocupado')

    workspace_id = hashlib.sha256(str(tmp_path.resolve()).encode()).hexdigest()
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url):
            assert url == 'http://127.0.0.1:8765'
            return httpx.Response(200, headers={header: workspace_id})

    opened = []
    monkeypatch.setattr('docente_ai.web.launch.socket.socket', lambda: SocketOcupado())
    monkeypatch.setattr('docente_ai.web.launch.httpx.Client', Client)
    monkeypatch.setattr('docente_ai.web.launch.webbrowser.open', opened.append)
    monkeypatch.setattr('docente_ai.web.launch.create_app', lambda *args, **kwargs: pytest.fail('Segundo servidor'))
    args = SimpleNamespace(port=8765, workspace=tmp_path, no_browser=False)
    assert launch(args) == 0
    assert opened == ['http://127.0.0.1:8765']
    assert 'Arkhé ya está abierto' in capsys.readouterr().out


def test_bundle_arkhe_conserva_lanzador_anterior(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('build_macos_app', ROOT / 'scripts/build_macos_app.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    old = tmp_path / 'Enjambre.app'
    old.mkdir()
    (old / 'testigo').write_text('Conservar')
    monkeypatch.setattr(builder, 'write_icon', lambda path: path.write_bytes(b'icns-sintetico'))
    bundle = builder.build_bundle(tmp_path, '0.8.0')
    assert bundle.name == 'Arkhe.app'
    assert (old / 'testigo').read_text() == 'Conservar'
    info = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())
    assert info['CFBundleName'] == info['CFBundleDisplayName'] == 'Arkhé'
    assert info['CFBundleExecutable'] == 'Arkhe'
    assert (bundle / 'Contents/Resources/Arkhe.icns').is_file()
    executable = bundle / 'Contents/MacOS/Arkhe'
    text = executable.read_text()
    assert '.venv/bin/docente-ai' in text and '/data/interface.log' in text
    assert executable.stat().st_mode & 0o111


def test_marca_y_familias_tipograficas():
    static = ROOT / 'src/docente_ai/web/static'
    html = (static / 'index.html').read_text()
    assert '<title>Arkhé · Espacio docente</title>' in html
    assert 'aria-label="Arkhé, biblioteca"' in html and '<span>ARKHÉ</span>' in html
    assert 'Enjambre' not in html and 'enjambre' not in html
    for file in ['base.css', 'tokens.css']:
        css = (static / 'css' / file).read_text()
        assert 'Arkhé Sans' in css and 'Arkhé Serif' in css
        assert 'Enjambre' not in css
    for file in ['README.md', 'ARCHITECTURE.md']:
        text = (ROOT / file).read_text()
        assert text.startswith('# ARKHÉ') and 'Antes llamado Enjambre.' in text
    ignored = (ROOT / '.gitignore').read_text()
    assert '/Enjambre.app/' in ignored and '/Arkhe.app/' in ignored
