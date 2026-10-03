"""Fragmentación por caracteres y límites de párrafo, con offsets verificables."""

import re
from bisect import bisect_right

from docente_ai.rag.settings import RagSettings


def split_segment(segment: dict, settings: RagSettings) -> list[dict]:
    text = segment['text']
    result = []
    newline_ends = [match.end() for match in re.finditer(r'\r\n|\r|\n', text)] if segment['locator']['kind'] == 'lines' else []
    start = 0
    while start < len(text):
        end = min(start + settings.chunk_chars, len(text))
        if end < len(text):
            # Preferir párrafo, después un espacio. No eliminar ni reformatear texto.
            lower = start + settings.chunk_chars // 2
            boundary = text.rfind('\n\n', lower, end)
            if boundary >= lower:
                end = boundary + 2
            else:
                boundary = text.rfind(' ', lower, end)
                if boundary >= lower:
                    end = boundary + 1
        piece = text[start:end]
        if piece.strip():
            locator = dict(segment['locator'])
            locator.update(char_start=start, char_end=end)
            if locator['kind'] == 'lines':
                locator['line_start'] = 1 + bisect_right(newline_ends, start)
                # Si el fragmento termina con salto, pertenece a la línea anterior.
                effective_end = end
                while effective_end > start and text[effective_end - 1] in '\r\n':
                    effective_end -= 1
                locator['line_end'] = 1 + bisect_right(newline_ends, max(start, effective_end - 1))
            result.append({'segment_id': segment['id'], 'text': piece, 'locator': locator})
        if end == len(text):
            break
        start = max(start + 1, end - settings.overlap_chars)
    return result
