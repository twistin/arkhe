"""ENJAMBRE IA DOCENTE LOCAL."""

from importlib.metadata import version
from docente_ai.secrets import install_log_filter

install_log_filter()

__version__ = version("docente-ai")
