"""Tests para la eliminación de pentagramas decorativos, incorporación del catálogo

de ejemplos musicales reales y corrección de contraste en infografías.
"""

from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parents[1]
MUSICA_JS = ROOT / 'src/docente_ai/web/static/js/infografias/musica.js'
INFOGRAFIAS_CSS = ROOT / 'src/docente_ai/web/static/css/infografias.css'
CONFIG_EJEMPLOS = ROOT / 'config/ejemplos'


def test_prohibicion_de_notas_a_mano_y_eliminacion_de_pentagramas_decorativos():
    """Comprueba que no se dibujen notas ni pentagramas a mano en HTML/CSS/JS."""
    codigo = MUSICA_JS.read_text(encoding='utf-8')
    assert 'renderStaffSvg' not in codigo
    assert '<ellipse cx=' not in codigo
    assert '<line x1=' not in codigo
    assert 'stroke-dasharray' not in codigo
    # Debe contener el texto de sustitución exacto cuando no hay ejemplo verificado
    assert 'Ejemplo musical pendiente de añadir al catálogo' in codigo


def test_aviso_pendiente_cuando_no_hay_ejemplo_verificado():
    """Comprueba que el esquema muestre 'Ejemplo musical pendiente...' si no hay verificado."""
    codigo = MUSICA_JS.read_text(encoding='utf-8')
    assert 'renderEjemploPendiente' in codigo
    assert 'Ejemplo musical pendiente de añadir al catálogo' in codigo
    assert 'renderDufayEjemploReal' not in codigo
    assert 'dufay_se_la_face_ay_pale_gloria.musicxml' not in codigo


def test_contraste_titulo_caja_azul():
    """Comprueba que el título de la caja azul tenga alto contraste."""
    css = INFOGRAFIAS_CSS.read_text(encoding='utf-8')
    bloque_h3 = re.search(r'\.panel-header-bar\s+h3\s*\{([^}]+)\}', css)
    assert bloque_h3 is not None
    contenido_h3 = bloque_h3.group(1)
    assert 'color: #ffffff' in contenido_h3 or 'color: rgb(255, 255, 255)' in contenido_h3

    bloque_sub = re.search(r'\.panel-sub\s*\{([^}]+)\}', css)
    assert bloque_sub is not None
    contenido_sub = bloque_sub.group(1)
    assert 'color:' in contenido_sub
