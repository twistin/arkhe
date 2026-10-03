"""Registro de acciones: duplicados, formularios y referencias HTML sin manejador."""

from pathlib import Path
import re

import pytest

from test_frontend_modules import ROOT
from ui_templates import mascara


def objeto_exportado(text, name):
    match = re.search(r'export\s+const\s+' + name + r'\s*=\s*[\{\[]', mascara(text))
    if not match:
        return None
    start = match.end()
    mask = mascara(text)
    opening = mask[start - 1]
    closing = '}' if opening == '{' else ']'
    depth = 1
    for end in range(start, len(mask)):
        depth += (mask[end] == opening) - (mask[end] == closing)
        if depth == 0:
            return text[start:end]
    raise AssertionError(f'Objeto {name} sin cierre')


def registro(root):
    maps = {'actions': {}, 'forms': {}}
    for path in sorted([*(root / 'vistas').glob('*.js'), *(root / 'componentes').glob('*.js')]):
        text = path.read_text()
        for name, entries in maps.items():
            body = objeto_exportado(text, name)
            if name == 'actions':
                assert body is not None, f'{path}: debe exportar actions, aunque esté vacío'
            if body is None:
                continue
            pattern = r'''\s*['"]([\w-]+)['"]\s*:\s*([A-Za-z_$][\w$]*)\s*,?'''
            matches = list(re.finditer(pattern, body))
            assert not re.sub(pattern, '', body).strip(), f'{path}: registro no analizable de {name}'
            for match in matches:
                key, handler = match.groups()
                assert key not in entries, f'{name} duplicado: {key}, {entries.get(key)} y {path}'
                assert re.search(r'\b(?:function|const)\s+' + handler + r'\b', text), f'Manejador ausente: {handler}'
                entries[key] = path
    return maps


def comprobar_html(root, maps):
    paths = [*root.rglob('*.js')]
    if (root.parent / 'index.html').exists():
        paths.append(root.parent / 'index.html')
    for path in paths:
        text = path.read_text()
        for attribute, name in [('data-action', 'actions'), ('data-form', 'forms')]:
            for value in re.findall(attribute + r'''\s*=\s*["']([^"']+)["']''', text):
                if value == '${e(action)}' and path == root / 'ui.js':
                    # Único constructor dinámico: primary; revisar sus llamadas abajo.
                    continue
                assert '${' not in value, f'{path}: referencia dinámica no revisada: {value}'
                assert value in maps[name], f'{path}: {attribute} sin manejador: {value}'
        literal = r'''(?:'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")'''
        calls = list(re.finditer(r'\bprimary\(\s*' + literal + r'\s*,\s*(' + literal + ')', text))
        known = {match.start() for match in calls}
        for call in re.finditer(r'\bprimary\(', text):
            if text[:call.start()].rstrip().endswith('function'):
                continue
            assert call.start() in known, f'{path}: acción dinámica de primary no revisada'
        for match in calls:
            key = match[1][1:-1]
            assert key in maps['actions'], f'{path}: primary sin manejador: {key}'
        for action in re.findall(r'''\baction:\s*['"]([\w-]+)['"]''', objeto_exportado(text, 'clickBindings') or ''):
            assert action in maps['actions'], f'{path}: binding sin manejador: {action}'


def test_acciones_y_formularios_registrados_sin_duplicados():
    maps = registro(ROOT)
    assert maps['actions'] and maps['forms']
    comprobar_html(ROOT, maps)
    main = (ROOT / 'main.js').read_text()
    assert len(main.splitlines()) < 250
    # Cada módulo exportador se importa y figura en el registro del coordinador.
    aliases = {url: alias for alias, url in re.findall(r"import \* as (\w+) from '([^']+)'", main)}
    registered = re.search(r'const modules = \[([^]]+)\]', main)[1].split(',')
    for path in [*(ROOT / 'vistas').glob('*.js'), *(ROOT / 'componentes').glob('*.js')]:
        alias = aliases.get('./' + str(path.relative_to(ROOT)))
        assert alias and alias in [part.strip() for part in registered], f'Módulo sin registrar: {path}'


def fixture_module(root, filename, text):
    folder = root / 'vistas'
    folder.mkdir(exist_ok=True)
    (folder / filename).write_text(text)


def test_detector_rechaza_acciones_duplicadas(tmp_path):
    for name in ['a.js', 'b.js']:
        fixture_module(tmp_path, name, "function guardar() {}\nexport const actions={'guardar': guardar};")
    with pytest.raises(AssertionError, match='duplicado'):
        registro(tmp_path)


@pytest.mark.parametrize('html', [
    '<button data-action="sin-handler">', '<form data-form="sin-handler">',
    "primary('Guardar', 'sin-handler')",
])
def test_detector_rechaza_html_sin_manejador(tmp_path, html):
    fixture_module(tmp_path, 'a.js', "export const actions={};\nconst html=`" + html + '`;')
    with pytest.raises(AssertionError, match='sin manejador'):
        comprobar_html(tmp_path, registro(tmp_path))


def test_detector_rechaza_referencia_dinamica_no_revisada(tmp_path):
    fixture_module(tmp_path, 'a.js', 'export const actions={};\nconst html=`<button data-action="${foo}">`;')
    with pytest.raises(AssertionError, match='dinámica'):
        comprobar_html(tmp_path, registro(tmp_path))


def test_detector_rechaza_binding_sin_manejador(tmp_path):
    fixture_module(tmp_path, 'a.js', "export const actions={};\n"
        "export const clickBindings=[{action:'perdida', matches: target=>true}];")
    with pytest.raises(AssertionError, match='binding sin manejador'):
        comprobar_html(tmp_path, registro(tmp_path))


def test_detector_rechaza_accion_dinamica_en_constructor(tmp_path):
    fixture_module(tmp_path, 'a.js', "export const actions={};\nprimary('Guardar', variable);")
    with pytest.raises(AssertionError, match='dinámica'):
        comprobar_html(tmp_path, registro(tmp_path))
