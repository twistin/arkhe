"""Extracción automática de metadatos musicales desde archivos de partitura.

Soporta formatos estándar de notación:
- MusicXML (.xml, .musicxml) y comprimido (.mxl)
- Humdrum (**kern, .krn)
- MEI (.mei)
- ABC (.abc)

Extrae de la cabecera: título, compositor, voces, compases, claves y mensuración.
"""

from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


def parse_musicxml_content(content_str: str) -> dict[str, Any]:
    """Extrae metadatos de un documento MusicXML en cadena XML."""
    try:
        root = ET.fromstring(content_str)
    except Exception as exc:
        raise ValueError(f"Error parseando MusicXML: {exc}") from exc

    title = ""
    work_title = root.find(".//work/work-title")
    if work_title is not None and work_title.text:
        title = work_title.text.strip()
    if not title:
        mov_title = root.find(".//movement-title")
        if mov_title is not None and mov_title.text:
            title = mov_title.text.strip()

    composer = ""
    for creator in root.findall(".//identification/creator"):
        creator_type = creator.get("type", "").lower()
        if creator_type in ("composer", "autor", "") and creator.text:
            composer = creator.text.strip()
            break
    if not composer:
        creator_any = root.find(".//identification/creator")
        if creator_any is not None and creator_any.text:
            composer = creator_any.text.strip()

    # Voces / Partes
    voces = []
    for part in root.findall(".//part-list/score-part"):
        part_id = part.get("id", "")
        part_name_el = part.find("part-name")
        part_name = part_name_el.text.strip() if part_name_el is not None and part_name_el.text else part_id
        voces.append({"id": part_id, "nombre": part_name})

    # Claves y Mensuración del primer compás de cada parte
    claves = []
    time_sig = ""
    for clef in root.findall(".//measure/attributes/clef"):
        sign = clef.find("sign")
        line = clef.find("line")
        sign_str = sign.text.strip() if sign is not None and sign.text else "?"
        line_str = line.text.strip() if line is not None and line.text else ""
        octave = clef.find("clef-octave-change")
        oct_str = f"({octave.text})" if octave is not None and octave.text else ""
        claves.append(f"{sign_str}{line_str}{oct_str}")

    time_el = root.find(".//measure/attributes/time")
    if time_el is not None:
        beats = time_el.find("beats")
        beat_type = time_el.find("beat-type")
        if beats is not None and beat_type is not None and beats.text and beat_type.text:
            time_sig = f"{beats.text.strip()}/{beat_type.text.strip()}"
        else:
            senza = time_el.find("senza-misura")
            if senza is not None:
                time_sig = "senza misura"

    # Conteo de compases de la primera parte
    first_part = root.find(".//part")
    compases_count = len(first_part.findall("measure")) if first_part is not None else 0

    return {
        "titulo": title or "Sin título",
        "compositor": composer or "Anónimo",
        "voces": voces,
        "compases": compases_count,
        "claves": list(dict.fromkeys(claves)),
        "mensuracion": time_sig or "No especificada",
        "formato": "musicxml",
    }


def parse_mxl_file(path: Path) -> dict[str, Any]:
    """Extrae metadatos de un archivo MusicXML comprimido (.mxl)."""
    with zipfile.ZipFile(path, "r") as zf:
        container_xml = zf.read("META-INF/container.xml").decode("utf-8")
        cont_root = ET.fromstring(container_xml)
        rootfile = cont_root.find(".//rootfile")
        if rootfile is None or not rootfile.get("full-path"):
            raise ValueError("Archivo .mxl no contiene ruta de partitura en container.xml")
        xml_path = rootfile.get("full-path")
        xml_content = zf.read(xml_path).decode("utf-8")
        data = parse_musicxml_content(xml_content)
        data["formato"] = "mxl"
        data["archivo"] = path.name
        return data


def parse_humdrum_content(content_str: str) -> dict[str, Any]:
    """Extrae metadatos de un archivo Humdrum (**kern)."""
    title = ""
    composer = ""
    voices = []
    claves = []
    time_sig = ""
    measure_count = 0

    for line in content_str.splitlines():
        line_str = line.strip()
        if line_str.startswith("!!!OTL:"):
            title = line_str[7:].strip()
        elif line_str.startswith("!!!COM:"):
            composer = line_str[7:].strip()
            # Formatos como "Josquin des Prez" o "Desprez, Josquin"
            if "," in composer:
                parts = [p.strip() for p in composer.split(",", 1)]
                composer = f"{parts[1]} {parts[0]}"
        elif line_str.startswith("**kern"):
            parts = line_str.split("\t")
            voices = [{"id": f"V{idx + 1}", "nombre": f"Voz {idx + 1}"} for idx in range(len(parts))]
        elif "*clef" in line_str:
            tokens = line_str.split("\t")
            for tok in tokens:
                if tok.startswith("*clef"):
                    clef_val = tok.replace("*clef", "")
                    if clef_val and clef_val not in claves:
                        claves.append(clef_val)
        elif line_str.startswith("*M") and "/" in line_str:
            m_match = re.search(r'\*M(\d+/\d+)', line_str)
            if m_match and not time_sig:
                time_sig = m_match.group(1)
        elif line_str.startswith("="):
            measure_count += 1

    return {
        "titulo": title or "Sin título",
        "compositor": composer or "Anónimo",
        "voces": voices,
        "compases": measure_count,
        "claves": claves,
        "mensuracion": time_sig or "No especificada",
        "formato": "humdrum",
    }


def parse_mei_content(content_str: str) -> dict[str, Any]:
    """Extrae metadatos de un documento MEI (Music Encoding Initiative)."""
    try:
        root = ET.fromstring(content_str)
    except Exception as exc:
        raise ValueError(f"Error parseando MEI: {exc}") from exc

    # En MEI suele haber namespace
    ns = {"mei": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    prefix = f"{{{ns['mei']}}}" if ns else ""

    title = ""
    title_el = root.find(f".//{prefix}title")
    if title_el is not None and title_el.text:
        title = title_el.text.strip()

    composer = ""
    composer_el = root.find(f".//{prefix}persName[@role='composer']")
    if composer_el is None:
        composer_el = root.find(f".//{prefix}composer")
    if composer_el is not None and composer_el.text:
        composer = composer_el.text.strip()

    voces = []
    claves = []
    time_sig = ""
    for staff_def in root.findall(f".//{prefix}staffDef"):
        staff_n = staff_def.get("n", "")
        label_el = staff_def.find(f"{prefix}label")
        v_name = label_el.text.strip() if label_el is not None and label_el.text else f"Voz {staff_n}"
        voces.append({"id": f"P{staff_n}", "nombre": v_name})

        clef_shape = staff_def.get("clef.shape", "")
        clef_line = staff_def.get("clef.line", "")
        if clef_shape:
            claves.append(f"{clef_shape}{clef_line}")

        meter_count = staff_def.get("meter.count", "")
        meter_unit = staff_def.get("meter.unit", "")
        if meter_count and meter_unit and not time_sig:
            time_sig = f"{meter_count}/{meter_unit}"

    measures = root.findall(f".//{prefix}measure")
    measure_count = len(measures)

    return {
        "titulo": title or "Sin título",
        "compositor": composer or "Anónimo",
        "voces": voces,
        "compases": measure_count,
        "claves": list(dict.fromkeys(claves)),
        "mensuracion": time_sig or "No especificada",
        "formato": "mei",
    }


def parse_abc_content(content_str: str) -> dict[str, Any]:
    """Extrae metadatos de una partitura en notación ABC."""
    title = ""
    composer = ""
    voces = []
    claves = []
    time_sig = ""

    lines = content_str.splitlines()
    for line in lines:
        line_str = line.strip()
        if line_str.startswith("T:"):
            title = line_str[2:].strip()
        elif line_str.startswith("C:"):
            composer = line_str[2:].strip()
        elif line_str.startswith("M:"):
            time_sig = line_str[2:].strip()
        elif line_str.startswith("V:"):
            v_spec = line_str[2:].strip()
            v_id = v_spec.split()[0] if v_spec else f"V{len(voces) + 1}"
            v_name = v_id
            name_match = re.search(r'name=["\']?([^"\']+)["\']?', v_spec)
            if name_match:
                v_name = name_match.group(1)
            clef_match = re.search(r'clef=(\w+)', v_spec, re.I)
            if clef_match:
                claves.append(clef_match.group(1))
            voces.append({"id": v_id, "nombre": v_name})

    # Aproximación de compases por barras de compás '|'
    pipe_count = sum(l.count("|") for l in lines if not l.startswith("%") and not (len(l) > 2 and l[1] == ":"))
    num_voices = max(1, len(voces))
    measures_est = max(1, pipe_count // num_voices)

    return {
        "titulo": title or "Sin título",
        "compositor": composer or "Anónimo",
        "voces": voces,
        "compases": measures_est,
        "claves": list(dict.fromkeys(claves)),
        "mensuracion": time_sig or "No especificada",
        "formato": "abc",
    }


def parse_score_file(path: Path) -> dict[str, Any]:
    """Parsea un archivo de partitura reconociendo automáticamente su formato."""
    if not path.is_file():
        raise FileNotFoundError(f"Archivo de partitura no encontrado: {path}")

    suffix = path.suffix.lower()
    if suffix == ".mxl":
        data = parse_mxl_file(path)
        data["path"] = str(path)
        data["archivo"] = path.name
        return data

    raw_text = path.read_text(encoding="utf-8", errors="replace")
    if suffix in (".xml", ".musicxml") or "<score-partwise" in raw_text or "<score-timewise" in raw_text:
        data = parse_musicxml_content(raw_text)
    elif suffix == ".krn" or "**kern" in raw_text:
        data = parse_humdrum_content(raw_text)
    elif suffix == ".mei" or "<mei" in raw_text:
        data = parse_mei_content(raw_text)
    elif suffix == ".abc" or re.search(r'^[XTMKV]:', raw_text, re.M):
        data = parse_abc_content(raw_text)
    else:
        raise ValueError(f"Formato de partitura no soportado o irreconocible para: {path.name}")

    data["path"] = str(path)
    data["archivo"] = path.name
    return data
