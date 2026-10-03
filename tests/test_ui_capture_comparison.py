"""La tolerancia exige simultáneamente poca superficie y poca variación de color."""

import pytest

from test_ui_smoke import compare_capture


@pytest.fixture
def images(tmp_path):
    image = pytest.importorskip("PIL.Image")
    baseline = tmp_path / "referencia.png"
    current = tmp_path / "actual.png"
    source = image.new("RGB", (100, 100), (100, 100, 100))
    source.save(baseline)
    return source, current, baseline


def test_identico_pasa_en_ambos_modos(images):
    source, current, baseline = images
    source.save(current)
    for strict in (False, True):
        result = compare_capture(current, baseline, strict=strict)
        assert result["accepted"] and result["changed_pixels"] == 0


def test_un_pixel_dos_niveles_pasa_solo_con_tolerancia(images):
    source, current, baseline = images
    source.putpixel((0, 0), (102, 100, 100))
    source.save(current)
    result = compare_capture(current, baseline)
    assert result["accepted"] and result["changed_percent"] == 0.01
    assert result["max_channel_delta"] == 2
    assert not compare_capture(current, baseline, strict=True)["accepted"]


def test_color_excesivo_falla_aunque_la_superficie_sea_pequena(images):
    source, current, baseline = images
    source.putpixel((0, 0), (103, 100, 100))
    source.save(current)
    assert not compare_capture(current, baseline)["accepted"]


def test_superficie_excesiva_falla_aunque_el_color_cambie_poco(images):
    source, current, baseline = images
    for point in ((0, 0), (1, 0)):
        source.putpixel(point, (101, 100, 100))
    source.save(current)
    assert not compare_capture(current, baseline)["accepted"]


def test_cambio_de_dimensiones_falla(images):
    source, current, baseline = images
    source.crop((0, 0, 99, 100)).save(current)
    assert not compare_capture(current, baseline)["accepted"]
