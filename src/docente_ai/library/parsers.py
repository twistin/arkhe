"""Extraer texto sin inventar numeración impresa ni ejecutar contenido."""

from dataclasses import dataclass, field
from io import BytesIO
import re

import pypdf
from pypdf import PdfReader
import docx
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from docente_ai.library import ocr


@dataclass
class Extraction:
    extractor: str
    segments: list[dict] = field(default_factory=list)
    page_count: int | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    derived_content: bytes | None = None
    original: 'Extraction | None' = None

    @property
    def status(self) -> str:
        if self.error:
            return 'failed'
        return 'needs_review' if self.warnings else 'ready'


def paragraph_markdown(paragraph, document):
    """Encabezados y numeración directa o heredada del estilo Word."""
    text = paragraph.text
    style = paragraph.style
    properties = [paragraph._p.pPr]
    seen = set()
    while style is not None and style.style_id not in seen:
        seen.add(style.style_id)
        properties.append(style.element.pPr)
        heading = re.fullmatch(r'(?:Heading|Título)\s*(\d+)', style.name or '', re.I)
        if heading:
            return '#' * min(6, int(heading[1])) + ' ' + text, text
        style = style.base_style
    for props in properties:
        if props is None:
            continue
        outline = props.find(qn('w:outlineLvl'))
        if outline is not None and int(outline.get(qn('w:val'))) < 9:
            return '#' * min(6, int(outline.get(qn('w:val'))) + 1) + ' ' + text, text
        numbering = props.numPr
        if numbering is None or numbering.numId is None or numbering.numId.val == 0:
            continue
        level = numbering.ilvl.val if numbering.ilvl is not None else 0
        root = document.part.numbering_part.element
        nums = root.xpath(f'./w:num[@w:numId="{numbering.numId.val}"]/w:abstractNumId')
        formats = root.xpath(f'./w:abstractNum[@w:abstractNumId="{nums[0].val}"]/w:lvl[@w:ilvl="{level}"]/w:numFmt') if nums else []
        bullet = bool(formats and formats[0].get(qn('w:val')) == 'bullet')
        return '  ' * level + ('- ' if bullet else '1. ') + text, None
    return text, None


def table_markdown(table, document):
    rows = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            pieces = []
            for block in cell.iter_inner_content():
                value = paragraph_markdown(block, document)[0] if isinstance(block, Paragraph) else table_markdown(block, document)
                if value.strip():
                    pieces.append(value)
            cells.append('<br>'.join(pieces).replace('|', '\\|').replace('\n', '<br>'))
        rows.append(cells)
    if not rows:
        return ''
    width = max(map(len, rows))
    # Markdown necesita una fila de encabezado; una fila vacía evita inventar
    # que la primera fila de datos del DOCX era un encabezado.
    first_is_header = bool(table.rows[0]._tr.xpath('./w:trPr/w:tblHeader'))
    header = rows.pop(0) if first_is_header else [''] * width
    lines = [header, ['---'] * width, *rows]
    return '\n'.join('| ' + ' | '.join(row + [''] * (width - len(row))) + ' |' for row in lines)


def extract_docx(content: bytes) -> Extraction:
    result = Extraction(f'python-docx:{docx.__version__};markdown:1')
    try:
        document = docx.Document(BytesIO(content))
        paragraph_index = table_index = 0
        section = None
        for block in document.iter_inner_content():
            if isinstance(block, Paragraph):
                paragraph_index += 1  # Incluye párrafos vacíos del cuerpo principal.
                text, heading = paragraph_markdown(block, document)
                section = heading or section
                locator = {'kind': 'docx_paragraph', 'paragraph_index': paragraph_index, 'section': section}
            else:
                table_index += 1
                text = table_markdown(block, document)
                locator = {'kind': 'docx_table', 'table_index': table_index, 'section': section}
            if text.strip():
                locator.update(char_start=0, char_end=len(text))
                result.segments.append({'text': text, 'locator': locator})
        if not result.segments:
            result.error = 'DOCX sin texto utilizable; las imágenes y cuadros de texto no se extraen.'
    except Exception as exc:
        result.error = f'No se pudo extraer el DOCX ({type(exc).__name__}).'
    return result


def extract(content: bytes, suffix: str) -> Extraction:
    if suffix == '.docx':
        return extract_docx(content)
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
        raise ValueError('Formato no admitido. Utiliza .pdf, .docx, .txt o .md.')
    result, sparse_pages = extract_pdf(content)
    if not sparse_pages or (result.error and result.segments == [] and result.page_count is None):
        return result
    try:
        derived = ocr.recognize(content, sparse_pages)
    except ValueError as exc:
        result.error = str(exc)
        return result
    recognized, _ = extract_pdf(derived)
    if recognized.error or recognized.page_count != result.page_count:
        result.error = 'El resultado OCR es ilegible, no contiene texto o ha cambiado el número de páginas.'
        return result
    recognized.extractor += ';ocrmypdf:1'
    recognized.warnings.insert(0, ocr.OCR_WARNING)
    recognized.derived_content = derived
    recognized.original = result
    for segment in recognized.segments:
        segment['locator']['ocr_document'] = True
        if segment['locator']['pdf_page_index'] in sparse_pages:
            segment['locator']['text_origin'] = 'texto OCR'
    return recognized


def extract_pdf(content: bytes) -> tuple[Extraction, list[int]]:
    result = Extraction(f'pypdf:{pypdf.__version__};text:1')
    sparse_pages = []
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            result.error = 'PDF cifrado: proporciona una copia local sin cifrar que puedas utilizar.'
            return result, sparse_pages
        result.page_count = len(reader.pages)
        labels = reader.page_labels
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ''
            if sum(char.isalnum() for char in text) < 20:
                sparse_pages.append(number)
                result.warnings.append(f'Página {number} del archivo PDF sin texto o con texto muy escaso (menos de 20 caracteres alfanuméricos).')
            if not text.strip():
                continue
            result.segments.append({'text': text, 'locator': {
                'kind': 'pdf_page', 'pdf_page_index': number,
                'page_label': labels[number - 1], 'printed_page': None,
                'char_start': 0, 'char_end': len(text),
            }})
        if not result.segments:
            result.error = 'PDF sin texto extraíble; vacío, escaneado o ilegible.'
    except Exception as exc:
        # Los parsers PDF pueden lanzar errores de varias familias ante daños.
        # No registrar el contenido del archivo ni mensajes arbitrarios del PDF.
        result.error = f'No se pudo extraer el PDF ({type(exc).__name__}).'
    return result, sparse_pages
