"""Diagnóstico de solo lectura: SQLite en memoria y metadatos de Ollama."""

from contextlib import closing
from dataclasses import asdict, dataclass
import ipaddress
import math
import platform
import os
import sqlite3
import sys
from typing import Literal
from urllib.parse import urlsplit

import httpx
from docente_ai.library.ocr import find_ocr, OCR_INSTALL_HELP

DEFAULT_HOST = "http://127.0.0.1:11434"


@dataclass(frozen=True)
class Check:
    name: str
    status: Literal["ok", "warning", "error", "skipped"]
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def local_url(value: str) -> str:
    """Aceptar solo loopback literal; localhost se normaliza sin consultar DNS."""
    # Excepción exacta y solo explícita para el servicio privado del despliegue Docker.
    if os.environ.get('ARKHE_SERVER_MODE') == '1' and value == 'http://ollama:11434':
        return value
    try:
        url = urlsplit(value)
        host = url.hostname
        port = url.port
        if (
            url.scheme != "http"
            or not host
            or url.username is not None
            or url.password is not None
            or url.path not in ("", "/")
            or url.query
            or url.fragment
            or "%" in host
        ):
            raise ValueError
        if host == "localhost":
            host = "127.0.0.1"
        address = ipaddress.ip_address(host)
        if not address.is_loopback or port == 0:
            raise ValueError
    except ValueError:
        raise ValueError(
            "Usa una URL HTTP de loopback sin ruta ni credenciales, "
            "por ejemplo http://127.0.0.1:11434."
        ) from None
    authority = f"[{address}]" if address.version == 6 else str(address)
    return f"http://{authority}" + (f":{port}" if port is not None else "")


def positive_timeout(value: str | float) -> float:
    timeout = float(value)
    if not math.isfinite(timeout) or not 0 < timeout <= 30:
        raise ValueError("El timeout debe ser mayor que 0 y como máximo 30 segundos.")
    return timeout


def check_sqlite() -> list[Check]:
    checks = [Check("sqlite", "ok", f"Biblioteca Python: {sqlite3.sqlite_version}")]
    try:
        with closing(sqlite3.connect(":memory:")) as connection:
            try:
                connection.execute("CREATE VIRTUAL TABLE probe USING fts5(text)")
                checks.append(Check("fts5", "ok", "Disponible; prueba en memoria."))
            except sqlite3.Error:
                checks.append(Check("fts5", "warning", "No disponible; mejora futura."))
            supported = hasattr(connection, "enable_load_extension")
            checks.append(Check(
                "sqlite_extensions", "ok" if supported else "warning",
                "Método de carga disponible; sqlite-vec todavía no probado."
                if supported else "Este Python no expone carga de extensiones SQLite.",
            ))
    except sqlite3.Error:
        checks.append(Check("sqlite_memory", "error", "No se pudo abrir SQLite en memoria."))
    return checks


def check_ollama(
    host: str, timeout: float, *, transport: httpx.BaseTransport | None = None,
) -> list[Check]:
    host = local_url(host)
    timeout = positive_timeout(timeout)
    checks = []
    # No proxies del entorno, redirecciones ni reintentos hacia otros destinos.
    with httpx.Client(
        base_url=host, timeout=timeout, trust_env=False,
        follow_redirects=False, transport=transport,
    ) as client:
        for endpoint in ("version", "tags"):
            name = f"ollama_{endpoint}"
            try:
                response = client.get(f"/api/{endpoint}")
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError
                if endpoint == "version":
                    version = payload.get("version")
                    if not isinstance(version, str) or not version.strip():
                        raise ValueError
                    checks.append(Check(name, "ok", f"Servidor: {version}"))
                else:
                    models = payload.get("models")
                    if not isinstance(models, list) or any(
                        not isinstance(model, dict)
                        or not isinstance(model.get("name"), str)
                        or not model["name"].strip()
                        for model in models
                    ):
                        raise ValueError
                    names = sorted({model["name"] for model in models})
                    checks.append(Check(
                        name, "ok" if names else "warning",
                        "Modelos anunciados: " + ", ".join(names) if names
                        else "No hay modelos anunciados; no se descarga ninguno automáticamente.",
                    ))
            except httpx.TimeoutException:
                checks.append(Check(name, "error", "Tiempo de espera agotado. Comprueba Ollama."))
            except httpx.HTTPStatusError as exc:
                checks.append(Check(name, "error", f"Respuesta HTTP {exc.response.status_code}; no se siguen redirecciones."))
            except httpx.RequestError:
                checks.append(Check(name, "error", "No se pudo conectar. Abre Ollama y revisa host/puerto."))
            except (ValueError, UnicodeError):
                checks.append(Check(name, "error", "Respuesta JSON inválida o formato inesperado."))
    checks.append(Check(
        "ollama_scope", "warning",
        "Solo metadatos: no se han probado inferencia, embeddings, cliente CLI ni modo sin cloud.",
    ))
    return checks


def diagnose(
    *, host: str = DEFAULT_HOST, timeout: float = 3, offline: bool = False,
    transport: httpx.BaseTransport | None = None,
) -> list[Check]:
    checks = [
        Check("python", "ok" if sys.version_info[:2] == (3, 12) else "error",
              f"{platform.python_version()} · {sys.executable}; proyecto validado en Python 3.12."),
        Check("system", "ok", f"{platform.system()} {platform.release()} · {platform.machine()}"),
        *check_sqlite(),
        Check('ocrmypdf', 'ok' if find_ocr() else 'warning',
              'OCR opcional disponible en PATH; no se ejecuta ni se validan sus idiomas durante el diagnóstico.'
              if find_ocr() else 'OCR opcional no disponible. ' + OCR_INSTALL_HELP),
    ]
    if offline:
        checks.append(Check("ollama", "skipped", "Modo offline: no se realizan peticiones HTTP."))
    else:
        checks.extend(check_ollama(host, timeout, transport=transport))
    return checks
