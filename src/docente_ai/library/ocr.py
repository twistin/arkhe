"""OCR local opcional; nunca instalar herramientas ni reemplazar originales."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

OCR_INSTALL_HELP = (
    'Instala OCRmyPDF y los idiomas de Tesseract: en macOS, '
    '`brew install ocrmypdf tesseract-lang`; en Debian/Ubuntu, '
    '`sudo apt install ocrmypdf tesseract-ocr-spa tesseract-ocr-eng`. '
    'Comprueba después `docente-ai doctor --offline` y vuelve a importar el PDF.'
)
OCR_WARNING = 'Texto OCR: posible error de reconocimiento. Contrasta las citas con la imagen del PDF original.'


def find_ocr() -> str | None:
    return shutil.which('ocrmypdf')


def recognize(content: bytes, pages: list[int]) -> bytes:
    executable = find_ocr()
    if not executable:
        raise ValueError('PDF con páginas sin texto o con texto muy escaso; OCR opcional no disponible. ' + OCR_INSTALL_HELP)
    with tempfile.TemporaryDirectory(prefix='docente-ocr-') as directory:
        source = Path(directory) / 'original.pdf'
        target = Path(directory) / 'texto-ocr.pdf'
        source.write_bytes(content)
        command = [executable, '--force-ocr', '--invalidate-digital-signatures', '--pages', ','.join(map(str, pages)),
                   '--output-type', 'pdf', '--optimize', '0', '--jobs', '2',
                   '-l', os.environ.get('DOCENTE_AI_OCR_LANGUAGES', 'spa+eng'),
                   str(source), str(target)]
        try:
            # No registrar salida de herramientas: puede contener texto del documento.
            result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=900, check=False)
        except subprocess.TimeoutExpired:
            raise ValueError('OCR detenido tras 15 minutos; el original se conserva sin cambios.') from None
        except OSError:
            raise ValueError('No se pudo ejecutar OCRmyPDF. ' + OCR_INSTALL_HELP) from None

        if result.returncode != 0 or not target.is_file():
            retry_command = [executable, '--redo-ocr', '--invalidate-digital-signatures', '--pages', ','.join(map(str, pages)),
                             '--output-type', 'pdf', '--optimize', '0', '--jobs', '2',
                             '-l', os.environ.get('DOCENTE_AI_OCR_LANGUAGES', 'spa+eng'),
                             str(source), str(target)]
            try:
                result = subprocess.run(retry_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        timeout=900, check=False)
            except (subprocess.TimeoutExpired, OSError):
                pass

        if result.returncode != 0 or not target.is_file():
            raise ValueError(f'OCRmyPDF no produjo un PDF utilizable (código {result.returncode}). '
                             'Revisa sus dependencias y los idiomas spa+eng de Tesseract. ' + OCR_INSTALL_HELP)
        return target.read_bytes()
