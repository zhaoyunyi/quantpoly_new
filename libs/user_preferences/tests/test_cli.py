"""user-preferences CLI 测试。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PYTHON = sys.executable or "python3.11"
CLI_MODULE = "user_preferences.cli"


def _cli_env() -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[3]
    lib_root = repo_root / "libs" / "user_preferences"
    pythonpath = os.pathsep.join([
        str(lib_root),
        os.environ.get("PYTHONPATH", ""),
    ]).strip(os.pathsep)
    return {
        **os.environ,
        "PATH": "",
        "PYTHONPATH": pythonpath,
    }


def test_default_command_outputs_version():
    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, "default"],
        capture_output=True,
        text=True,
        env=_cli_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["data"]["version"] >= 1


def test_migrate_command_reads_stdin():
    payload = {"version": 0, "theme": {"primaryColor": "#000000", "darkMode": False}}
    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, "migrate"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=_cli_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["data"]["version"] >= 1
