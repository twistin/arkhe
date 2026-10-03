"""Extraer texto sin inventar numeración impresa ni ejecutar contenido."""

from dataclasses import dataclass, field
from io import BytesIO

import pypdf
from pypdf import PdfReader


@dataclass
class Extraction:
    extractor: str
    segments: list[dict] = field(default_factory=list)
    page_count: int | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def status(self) -> str:
        if self.error:
            return 'failed'
        return 'needs_review' if self.warnings else 'ready'


def extract(content: bytes, suffix: str) -> Extraction:
    if suffix in {'.txt', '.md'}:
        result = Extraction('utf8-text:1')
        try:
            text = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            result.error = 'El archivo no es texto UTF-8 válido.'
            return result
        if not text.strip():
            result.error = 'El archivo no contiene texto.'
        elif any(ord(char) < 32 and char not in '\n\r\t' for char in text):
            result.error = 'El archivo contiene caracteres de control; no parece texto válido.'
        else:
            result.segments.append({'text': text, 'locator': {
                'kind': 'lines', 'line_start': 1, 'line_end': len(text.splitlines()),
                'char_start': 0, 'char_end': len(text), 'section': None,
                'pdf_page_index': None, 'page_label': None, 'printed_page': None,
            }})
        return result
    if suffix != '.pdf':
        raise ValueError('Formato no admitido. Utiliza .pdf, .txt o .md.')
    result = Extraction(f'pypdf:{pypdf.__version__};text:1')
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            result.error = 'PDF cifrado: proporciona una copia local sin cifrar que puedas utilizar.'
            return result
        result.page_count = len(reader.pages)
        labels = reader.page_labels
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ''
            if not text.strip():
                result.warnings.append(f'Página {number} del archivo PDF sin texto extraíble; puede ser blanca o una imagen.')
                continue
            result.segments.append({'text': text, 'locator': {
                'kind': 'pdf_page', 'pdf_page_index': number,
                'page_label': labels[number - 1], 'printed_page': None,
                'char_start': 0, 'char_end': len(text),
            }})
        if not result.segments:
            result.error = 'PDF sin texto extraíble; vacío, escaneado o ilegible. OCR no disponible en esta fase.'
    except Exception as exc:
        # Los parsers PDF pueden lanzar errores de varias familias ante daños.
        # No registrar el contenido del archivo ni mensajes arbitrarios del PDF.
        result.error = f'No se pudo extraer el PDF ({type(exc).__name__}).'
    return result
