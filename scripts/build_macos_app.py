"""Crear Arkhe.app junto al proyecto; conservar cualquier lanzador anterior."""

import argparse
import math
from pathlib import Path
import plistlib
import tomllib


def write_icon(path):
    """Rasterizar el símbolo vectorial local para el icono de Finder, sin red."""
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError('Instala el grupo opcional ui: uv sync --locked --group ui.') from exc
    size, scale = 1024, 1024 / 40
    image = Image.new('RGBA', (size, size))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=11 * scale, fill='#244b3e')

    def stroke(points):
        points = [(round(x * scale), round(y * scale)) for x, y in points]
        width = round(1.8 * scale)
        draw.line(points, fill='#f5f3e8', width=width, joint='curve')
        for x, y in [points[0], points[-1]]:
            radius = width / 2
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill='#f5f3e8')

    def arch(radius, bottom):
        return [(20-radius, bottom), (20-radius, 18)] + [
            (20 + radius * math.cos(math.pi + i * math.pi / 96),
             18 + radius * math.sin(math.pi + i * math.pi / 96)) for i in range(97)
        ] + [(20+radius, bottom)]

    def curve(a, b, c, d):
        return [tuple((1-t)**3*a[j] + 3*(1-t)**2*t*b[j] + 3*(1-t)*t*t*c[j] + t**3*d[j]
                      for j in range(2)) for t in [i/64 for i in range(65)]]

    stroke(arch(9, 25))
    stroke(arch(4, 22))
    book = curve((8, 28), (13, 27), (16, 28), (20, 31))
    book += curve((20, 31), (24, 28), (27, 27), (32, 28))
    book += [(32, 32)] + curve((32, 32), (27, 31), (24, 32), (20, 35))
    book += curve((20, 35), (16, 32), (13, 31), (8, 32)) + [(8, 28)]
    stroke(book)
    stroke([(20, 31), (20, 35)])
    stroke([(25, 7), (28, 4)])
    image.save(path, format='ICNS')


def build_bundle(root, version):
    bundle = root / 'Arkhe.app'
    contents = bundle / 'Contents'
    executable = contents / 'MacOS' / 'Arkhe'
    resources = contents / 'Resources'
    executable.parent.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)
    write_icon(resources / 'Arkhe.icns')
    with (contents / 'Info.plist').open('wb') as output:
        plistlib.dump({
            'CFBundleName': 'Arkhé', 'CFBundleDisplayName': 'Arkhé',
            'CFBundleExecutable': 'Arkhe', 'CFBundleIconFile': 'Arkhe.icns',
            'CFBundleIdentifier': 'local.arkhe.docente', 'CFBundlePackageType': 'APPL',
            'CFBundleShortVersionString': version, 'CFBundleVersion': version,
            'LSUIElement': True, 'NSHighResolutionCapable': True,
        }, output)
    executable.write_text('''#!/bin/zsh
ARKHE_ROOT="$(cd -- "$(dirname -- "$0")/../../.." && pwd)"
mkdir -p "$ARKHE_ROOT/data"
nohup "$ARKHE_ROOT/.venv/bin/docente-ai" ui --workspace "$ARKHE_ROOT" >> "$ARKHE_ROOT/data/interface.log" 2>&1 < /dev/null &
exit 0
''')
    executable.chmod(0o755)
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / 'pyproject.toml').read_text())['project']['version']
    print(f'Lanzador Arkhé creado: {build_bundle(root, version)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
