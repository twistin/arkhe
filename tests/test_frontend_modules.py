"""Contratos del grafo ES nativo: URLs únicas, ausencia de ciclos y vistas aisladas."""

from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'src/docente_ai/web/static/js'
IMPORT = re.compile(r'''(?:^\s*(?:import|export)\s+(?:[^;]*?\s+from\s+)?["']([^"']+)["']|\bimport\(\s*["']([^"']+)["']\s*\))''', re.M)


def module_graph(root):
    graph = {}
    for path in root.rglob('*.js'):
        text = re.sub(r'/\*.*?\*/', '', path.read_text(), flags=re.S)
        dependencies = []
        for match in IMPORT.finditer(text):
            url = match[1] or match[2]
            assert url.startswith('.'), f'Import externo o bare en {path}: {url}'
            assert '?' not in url and '#' not in url, f'Import con dos identidades posibles: {url}'
            target = (path.parent / url).resolve()
            assert target.is_relative_to(root.resolve()) and target.is_file(), f'Import inexistente o fuera del grafo: {url}'
            if path.parent.name == 'vistas':
                allowed = {root / 'api.js', root / 'state.js', root / 'ui.js'}
                assert target in {p.resolve() for p in allowed} or target.is_relative_to((root / 'componentes').resolve()), f'La vista {path.name} importa {target.name}'
            dependencies.append(target)
        graph[path.resolve()] = dependencies
    return graph


def assert_acyclic(graph):
    complete = set()
    def visit(node, stack):
        assert node not in stack, 'Ciclo ES: ' + ' -> '.join(p.name for p in [*stack, node])
        if node in complete:
            return
        for target in graph[node]:
            visit(target, [*stack, node])
        complete.add(node)
    for node in graph:
        visit(node, [])


def test_modulos_locales_sin_ciclos_ni_imports_entre_vistas():
    graph = module_graph(ROOT)
    assert graph and (ROOT / 'main.js').resolve() in graph
    assert_acyclic(graph)


def test_detector_rechaza_ciclo(tmp_path):
    (tmp_path / 'a.js').write_text("import {b} from './b.js';\nexport const a=1;")
    (tmp_path / 'b.js').write_text("import {a} from './a.js';\nexport const b=1;")
    with pytest.raises(AssertionError, match='Ciclo ES'):
        assert_acyclic(module_graph(tmp_path))


@pytest.mark.parametrize('target', ['../vistas/otra.js', '../infografias/egipto.js', '../main.js'])
def test_detector_rechaza_imports_prohibidos_de_vistas(tmp_path, target):
    (tmp_path / 'vistas').mkdir()
    destination = (tmp_path / 'vistas' / target).resolve()
    destination.parent.mkdir(exist_ok=True)
    destination.write_text('export const ejemplo=1;')
    (tmp_path / 'vistas/biblioteca.js').write_text(f"import {{ejemplo}} from '{target}';")
    with pytest.raises(AssertionError, match='La vista'):
        module_graph(tmp_path)


def test_detector_rechaza_import_versionado(tmp_path):
    (tmp_path / 'a.js').write_text("import {b} from './b.js?v=1';")
    with pytest.raises(AssertionError, match='dos identidades'):
        module_graph(tmp_path)


def test_css_imports_locales_sin_parametros():
    static = ROOT.parent
    for path in [static / 'style.css', *(static / 'css').glob('*.css')]:
        for url in re.findall(r'@import\s+url\(["\']?([^"\')]+)', path.read_text()):
            assert '?' not in url and '#' not in url and url.startswith('.')
            assert (path.parent / url).is_file()


def test_sin_scripts_inline_ni_atributos_de_eventos():
    from html.parser import HTMLParser
    class Scripts(HTMLParser):
        def __init__(self):
            super().__init__()
            self.scripts = []
        def handle_starttag(self, tag, attrs):
            assert not any(name.startswith('on') for name, _ in attrs)
            if tag == 'script':
                attributes = dict(attrs)
                assert attributes.get('src'), 'Script inline en index.html'
                self.scripts.append(attributes)
    parser = Scripts()
    parser.feed((ROOT.parent / 'index.html').read_text())
    assert any(s.get('type') == 'module' and '/js/main.js' in s['src'] for s in parser.scripts)
    assert any(s.get('type') != 'module' and s['src'] == '/assets/mermaid.min.js' for s in parser.scripts)
    for path in ROOT.rglob('*.js'):
        assert not re.search(r'<[^>]*\son[a-z]+\s*=', path.read_text(), re.I), path


def test_mermaid_fuera_del_grafo_y_egipto_sin_global():
    assert not any(p.name == 'mermaid.min.js' for p in module_graph(ROOT))
    assert 'window.switchEgyptTab' not in (ROOT / 'infografias/egipto.js').read_text()


def test_modulos_legibles_sin_lineas_monoliticas():
    largas = [(str(path.relative_to(ROOT)), numero, len(linea))
              for path in ROOT.rglob('*.js')
              for numero, linea in enumerate(path.read_text().splitlines(), 1)
              if len(linea) > 120]
    assert not largas, largas
