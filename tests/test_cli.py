import json
from pathlib import Path
import subprocess
import sys

import pytest

from docente_ai import __version__
from docente_ai.cli import main
from docente_ai.doctor import Check


def test_help_without_command(capsys):
    assert main([]) == 0
    assert "doctor" in capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_json_offline(capsys):
    assert main(["doctor", "--offline", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert report["checks"][-1]["status"] == "skipped"


def test_error_exit_and_json(monkeypatch, capsys):
    monkeypatch.setattr("docente_ai.cli.diagnose", lambda **kwargs: [Check("ollama", "error", "offline")])
    assert main(["doctor", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


@pytest.mark.parametrize("args", [
    ["prepare", "class"], ["doctor", "--ollama-host", "http://example.org"],
    ["doctor", "--timeout", "nan"], ["doctor", "--timeout", "0"],
])
def test_invalid_arguments(args):
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2


def test_installed_entry_points():
    for args in ([sys.executable, "-m", "docente_ai", "--version"],
                 [str(Path(sys.executable).parent / "docente-ai"), "--version"]):
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == f"docente-ai {__version__}"
