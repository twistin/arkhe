"""Guardas de interpolación HTML, incluidas plantillas anidadas y fragmentos."""

from pathlib import Path

import pytest

from ui_templates import HTML_SEGURO, INTERNOS_SEGUROS, interpolaciones_inseguras

ROOT = Path(__file__).resolve().parents[1] / "src/docente_ai/web/static/js"


def test_interpolaciones_html_de_todos_los_modulos():
    errores = []
    for path in ROOT.rglob("*.js"):
        source = path.read_text()
        errores.extend(
            (str(path.relative_to(ROOT)), source.count("\n", 0, pos) + 1, expression)
            for pos, expression in interpolaciones_inseguras(source)
        )
    assert not errores, errores
    assert set(INTERNOS_SEGUROS) <= HTML_SEGURO


@pytest.mark.parametrize(
    "source",
    [
        "const h = `<p>${dato}</p>`;",
        "const h = `<p>${e(titulo) + dato}</p>`;",
        "const h = `<p>${condicion ? e(titulo) : dato}</p>`;",
        "const h = [`<p>`, `${dato}`, `</p>`].join('');",
        "const h = `<p>${filas.map(x => `<b>${x.nombre}</b>`).join('')}</p>`;",
        "const h = `<p>${filas.map(x => x.nombre).join('')}</p>`;",
        "const h = `<p>${filas.map(x => `<b>${e(x.nombre)}</b>` + x.otro).join('')}</p>`;",
        "const h = `<p>${renderDesconocido(dato)}</p>`;",
        "const h = `<p>${window.e(dato)}</p>`;",
    ],
)
def test_guard_rechaza_datos_sin_escape(source):
    assert interpolaciones_inseguras(source)


@pytest.mark.parametrize(
    "source",
    [
        "const h = `<p>${e(dato)}</p>`;",
        "const h = `<p>${icon('folder')}</p>`;",
        "const h = `<p>${condicion ? e(titulo) : icon('folder')}</p>`;",
        "const h = `<p>${filas.map(x => `<b>${e(x.nombre)}</b>`).join('')}</p>`;",
        "const h = [`<p>`, `${e(dato)}`, `</p>`].join('');",
        "const h = `<p>${option('a', `${dato}`, seleccionado)}</p>`;",
        "const texto = `Consulta: ${dato}`; const regex = /`[<>\"']/;",
        "// `<p>${dato}</p>`\nconst h = `<p>${e(dato)}</p>`;",
        "const h = `<p>${filas.map(x => { const y = e(x.nombre); return `<b>${y}</b>`; }).join('')}</p>`;",
    ],
)
def test_guard_acepta_escape_y_constructores_revisados(source):
    assert not interpolaciones_inseguras(source)
