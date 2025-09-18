"""user-preferences 持久化适配器 CLI 测试。"""

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


def _run_cli(args: list[str], *, stdin_payload: dict | None = None) -> dict:
    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, *args],
        input=json.dumps(stdin_payload) if stdin_payload is not None else None,
        capture_output=True,
        text=True,
        env=_cli_env(),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_cli_should_support_get_update_export_import_with_sqlite_store(tmp_path):
    db_path = str(tmp_path / "prefs.sqlite3")

    updated = _run_cli(
        [
            "update",
            "--user-id",
            "u-1",
            "--user-level",
            "2",
            "--db-path",
            db_path,
            "--patch",
            '{"theme": {"darkMode": true}}',
        ]
    )
    assert updated["success"] is True
    assert updated["data"]["theme"]["darkMode"] is True

    got = _run_cli([
        "get",
        "--user-id",
        "u-1",
        "--user-level",
        "2",
        "--db-path",
        db_path,
    ])
    assert got["success"] is True
    assert got["data"]["theme"]["darkMode"] is True

    exported = _run_cli([
        "export",
        "--user-id",
        "u-1",
        "--user-level",
        "2",
        "--db-path",
        db_path,
    ])
    assert exported["success"] is True
    assert exported["data"]["theme"]["darkMode"] is True

    imported = _run_cli(
        [
            "import",
            "--user-id",
            "u-1",
            "--user-level",
            "2",
            "--db-path",
            db_path,
        ],
        stdin_payload={"theme": {"primaryColor": "#00FF00", "darkMode": True}},
    )
    assert imported["success"] is True
    assert imported["data"]["theme"]["primaryColor"] == "#00FF00"


def test_cli_update_should_reject_advanced_for_level1(tmp_path):
    db_path = str(tmp_path / "prefs.sqlite3")

    payload = _run_cli(
        [
            "update",
            "--user-id",
            "u-1",
            "--user-level",
            "1",
            "--db-path",
            db_path,
            "--patch",
            '{"advanced": {"betaFeatures": true}}',
        ]
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "ADVANCED_PERMISSION_DENIED"
