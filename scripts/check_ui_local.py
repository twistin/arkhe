"""Ejecutar el smoke y la comparación visual contra un espacio ASGI sintético."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/ui-smoke"),
        help="Directorio de capturas e informes.",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Actualizar explícitamente las referencias visuales.",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exigir cero píxeles distintos."
    )
    parser.add_argument(
        "--update-views",
        nargs="+",
        choices=[
            "biblioteca",
            "asistente",
            "propuestas",
            "diario",
            "ajustes",
            "impresion",
        ],
        help="Actualizar solo las referencias indicadas.",
    )
    args = parser.parse_args()
    if args.update_views and not args.update_baseline:
        parser.error("--update-views requiere --update-baseline")
    root = Path(__file__).resolve().parents[1]
    environment = {**os.environ, "DOCENTE_UI_CAPTURE_DIR": str(args.output.resolve())}
    if args.strict:
        environment["DOCENTE_UI_STRICT"] = "1"
    if args.update_views:
        environment["DOCENTE_UI_UPDATE_VIEWS"] = ",".join(args.update_views)
    if args.update_baseline:
        environment["DOCENTE_UI_UPDATE_BASELINE"] = "1"
    return subprocess.call(
        [sys.executable, "-m", "pytest", "tests/test_ui_smoke.py", "-q"],
        cwd=root,
        env=environment,
    )


if __name__ == "__main__":
    raise SystemExit(main())
