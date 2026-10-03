"""Recorrido léxico de plantillas, incluidas interpolaciones y plantillas anidadas."""

from dataclasses import dataclass


@dataclass
class Plantilla:
    inicio: int
    fin: int
    expresiones: list
    segmentos: list
    contenedores: tuple = ()


def plantillas(texto, opacos=None):
    salida = []
    n = len(texto)
    pila = []
    rangos = {}
    opacos = [] if opacos is None else opacos

    def codigo(i, cierre=False):
        profundidad = 0
        previo = ""
        while i < n:
            c = texto[i]
            if texto.startswith("//", i):
                inicio = i
                j = texto.find("\n", i)
                i = n if j < 0 else j
                opacos.append((inicio, i))
                continue
            if texto.startswith("/*", i):
                inicio = i
                i = texto.index("*/", i) + 2
                opacos.append((inicio, i))
                continue
            if c in ('"', "'"):
                inicio = i
                q = c
                i += 1
                while i < n:
                    if texto[i] == "\\":
                        i += 2
                        continue
                    if texto[i] == q:
                        i += 1
                        break
                    i += 1
                opacos.append((inicio, i))
                previo = "literal"
                continue
            if c == "`":
                inicio = i
                contenedores = tuple(pila)
                i += 1
                segmento = i
                expresiones = []
                segmentos = []
                while i < n:
                    if texto[i] == "\\":
                        i += 2
                        continue
                    if texto[i] == "`":
                        segmentos.append((segmento, i))
                        i += 1
                        break
                    if texto.startswith("${", i):
                        segmentos.append((segmento, i))
                        a = i + 2
                        i = codigo(a, True)
                        expresiones.append((a, i - 1))
                        segmento = i
                        continue
                    i += 1
                salida.append(
                    Plantilla(inicio, i, expresiones, segmentos, contenedores)
                )
                previo = "literal"
                continue
            if c == "/" and previo in (
                "",
                "=",
                "(",
                "[",
                ",",
                ":",
                "return",
                "=>",
                "!",
                "&",
                "|",
                "?",
            ):
                inicio = i
                i += 1
                corchete = False
                while i < n:
                    if texto[i] == "\\":
                        i += 2
                        continue
                    if texto[i] == "[":
                        corchete = True
                    if texto[i] == "]":
                        corchete = False
                    if texto[i] == "/" and not corchete:
                        i += 1
                        while i < n and texto[i].isalpha():
                            i += 1
                        break
                    i += 1
                opacos.append((inicio, i))
                previo = "literal"
                continue
            if c.isalpha() or c in "_$":
                a = i
                i += 1
                while i < n and (texto[i].isalnum() or texto[i] in "_$"):
                    i += 1
                previo = texto[a:i]
                continue
            if c in "[(":
                pila.append(i)
            if c in "])" and pila:
                rangos[pila.pop()] = i + 1
            if c == "{":
                profundidad += 1
            if c == "}":
                if cierre and profundidad == 0:
                    return i + 1
                profundidad -= 1
            if not c.isspace():
                if texto.startswith("=>", i):
                    previo = "=>"
                    i += 2
                    continue
                previo = c
            i += 1
        return i

    codigo(0)
    return sorted(salida, key=lambda p: p.inicio), rangos


# Contratos revisados: devuelven HTML compuesto con e() o literales del código.
# No se permiten comodines por módulo ni cualquier función que empiece por render.
HTML_SEGURO = frozenset(
    {
        "e",
        "icon",
        "option",
        "subjectOptions",
        "statusBadge",
        "header",
        "primary",
        "formatMarkdown",
        "resultHTML",
        "bibliographyHTML",
        "evidenceHTML",
        "visualHTML",
        "studentDocumentHTML",
        "renderStudentInfographic",
        "renderEgyptInfographic",
        "renderStaffSvg",
        "renderListeningCardItem",
        "renderEgyptListeningsHTML",
        "renderStudentDiscographySection",
        "libraryResults",
        "filaFuente",
        "botonPeriodo",
        "entradaDiario",
        "tarjetaPropuesta",
        "runStatsPanel",
        "providerSettingsPanel",
        "schedulePanel",
        "horarioRegla",
        "excepcionHorario",
        "grupoHorario",
        "panelMaterias",
        "panelGrupos",
        "panelConocimiento",
        "unitOptions",
        "dialogHTML",
    }
)

# Dos constructores de base tienen valores locales ya seguros: formatMarkdown
# escapa el texto al entrar; icon y renderStaffSvg usan SVG literal del código.
# modal recibe exclusivamente HTML compuesto por los constructores anteriores.
INTERNOS_SEGUROS = {
    "formatMarkdown": {
        "code.trim()",
        "c",
        "l.trim().replace(/^-\\s+/, '')",
        "items",
        "trimmed.replace(/\\n/g, '<br>')",
    },
    "icon": {"paths[name] || paths.document"},
    "renderStaffSvg": {"lines", "content"},
    "header": {"actions"},
    "dialogHTML": {"content"},
}


def mascara(texto):
    """Ocultar literales/comentarios sin cambiar sus posiciones."""
    salida = list(texto)
    opacos = []
    plant, _ = plantillas(texto, opacos)
    for a, b in [*opacos, *[(p.inicio, p.fin) for p in plant]]:
        salida[a:b] = ["\n" if c == "\n" else " " for c in texto[a:b]]
    return "".join(salida)


def partes_superiores(texto, delimitador):
    mask = mascara(texto)
    profundidad = 0
    inicio = 0
    salida = []
    for i, c in enumerate(mask):
        if c in "([{":
            profundidad += 1
        elif c in ")]}":
            profundidad -= 1
        elif c == delimitador and profundidad == 0:
            salida.append(texto[inicio:i])
            inicio = i + 1
    return [*salida, texto[inicio:]]


def interpolaciones_inseguras(texto):
    """Señalar expresiones no escapadas; sintaxis nueva desconocida falla cerrada."""
    import re

    plant, rangos = plantillas(texto)
    html = set(
        p.inicio
        for p in plant
        if any(re.search(r"<[a-zA-Z!/]", texto[a:b]) for a, b in p.segmentos)
    )
    contenedores_html = {
        inicio for p in plant if p.inicio in html for inicio in p.contenedores
    }
    contexto = [
        p
        for p in plant
        if p.inicio in html
        or any(i in contenedores_html for i in p.contenedores)
        or any(q.inicio < p.inicio < q.fin and q.inicio in html for q in plant)
    ]
    mask = mascara(texto)
    funciones = []
    for m in re.finditer(r"function\s+(\w+)\s*\(", mask):
        inicio = mask.find("{", m.end())
        d = 0
        for i in range(inicio, len(mask)):
            if mask[i] == "{":
                d += 1
            elif mask[i] == "}":
                d -= 1
                if d == 0:
                    funciones.append((m.start(), i + 1, m[1]))
                    break
    bindings = list(re.finditer(r"\b(?:const|let)\s+(\w+)\s*=\s*", texto))

    def scope(pos):
        matches = [item for item in funciones if item[0] < pos < item[1]]
        if matches:
            return min(matches, key=lambda item: item[1] - item[0])[2]
        return (
            "icon"
            if "export const icon" in texto[:pos]
            and pos < texto.find("export const formatPeriod")
            else ""
        )

    def seguro(exp, pos, visitados=frozenset()):
        exp = exp.strip()
        if exp in INTERNOS_SEGUROS.get(scope(pos), set()):
            return True
        while exp.startswith("(") and exp.endswith(")"):
            mask = mascara(exp)
            d = 0
            final = None
            for i, c in enumerate(mask):
                if c == "(":
                    d += 1
                if c == ")":
                    d -= 1
                    if d == 0:
                        final = i
                        break
            if final != len(exp) - 1:
                break
            exp = exp[1:-1].strip()
        if re.fullmatch(
            r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|\d+|true|false|null|undefined", exp
        ):
            return True
        call = re.match(r"^(\w+)\s*\(", exp)
        if call and call[1] in HTML_SEGURO:
            mask = mascara(exp)
            a = mask.index("(")
            d = 0
            fin = None
            for i in range(a, len(mask)):
                if mask[i] == "(":
                    d += 1
                elif mask[i] == ")":
                    d -= 1
                    if d == 0:
                        fin = i
                        break
            if fin == len(exp) - 1:
                return True
        ps, _ = plantillas(exp)
        if ps and ps[0].inicio == 0 and ps[0].fin == len(exp):
            return all(seguro(exp[a:b], pos, visitados) for a, b in ps[0].expresiones)
        # Unión de fragmentos explícitos; cada fragmento debe ser seguro.
        match = re.fullmatch(r"\[([\s\S]*)\]\.join\(\s*(['\"])\2\s*\)", exp)
        if match:
            return all(
                seguro(x, pos, visitados) for x in partes_superiores(match[1], ",")
            )
        mask = mascara(exp)
        d = 0
        question = None
        ternary = 0
        for i, c in enumerate(mask):
            if c in "([{":
                d += 1
            elif c in ")]}":
                d -= 1
            elif (
                d == 0
                and c == "?"
                and (i + 1 == len(mask) or mask[i + 1] not in ".?")
                and (i == 0 or mask[i - 1] != "?")
            ):
                if question is None:
                    question = i
                else:
                    ternary += 1
            elif d == 0 and c == ":" and question is not None:
                if ternary:
                    ternary -= 1
                else:
                    return seguro(exp[question + 1 : i], pos, visitados) and seguro(
                        exp[i + 1 :], pos, visitados
                    )
        # || y + pueden unir HTML seguro y literales. Nunca basta con contener e().
        for separator in ("|", "+"):
            parts = partes_superiores(exp, separator)
            if len(parts) > 1:
                parts = [p for p in parts if p.strip()]
                return all(seguro(x, pos, visitados) for x in parts)
        # Los callbacks se validan también por sus plantillas anidadas.
        match = re.search(r"\.map\(([\s\S]+)\)\.join\(\s*(['\"])(?:| )\2\s*\)$", exp)
        if match:
            callback = match[1].strip()
            if callback in HTML_SEGURO:
                return True
            if "=>" in callback:
                body = callback.split("=>", 1)[1].strip()
                if body.startswith("{") and body.endswith("}"):
                    body_mask = mascara(body)
                    returned = list(re.finditer(r"\breturn\b", body_mask))
                    if not returned:
                        return False
                    body = (
                        body[returned[-1].end() :]
                        .strip()
                        .removesuffix("}")
                        .strip()
                        .removesuffix(";")
                        .strip()
                    )
                return seguro(body, pos + len(exp), visitados)
        if re.fullmatch(r"\w+", exp) and exp not in visitados:
            candidates = [
                m
                for m in bindings
                if m[1] == exp and m.start() < pos and scope(m.start()) == scope(pos)
            ]
            if candidates:
                m = candidates[-1]
                tail = texto[m.end() :]
                mask = mascara(tail)
                d = 0
                end = len(mask)
                for i, c in enumerate(mask):
                    if c in "([{":
                        d += 1
                    elif c in ")]}":
                        d -= 1
                    elif c in ";," and d == 0:
                        end = i
                        break
                return seguro(tail[:end], m.start(), visitados | {exp})
        return False

    errores = []
    for p in contexto:
        # option escapa valor/texto y e escapa toda la cadena; sus argumentos
        # pueden contener plantillas de texto, que no son HTML sin sanear.
        if any(
            re.search(r"\b(?:e|option)\s*$", texto[max(0, i - 60) : i])
            for i in p.contenedores
        ):
            continue
        for a, b in p.expresiones:
            if not seguro(texto[a:b], a):
                errores.append((a, texto[a:b].strip()))
    return errores
