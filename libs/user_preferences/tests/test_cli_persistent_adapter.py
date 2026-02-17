"""user-preferences 持久化适配器 CLI 测试（Postgres）。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


sqlalchemy = pytest.importorskip("sqlalchemy")
create_engine = sqlalchemy.create_engine
text = sqlalchemy.text

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


def _postgres_dsn() -> str:
    return os.getenv(
        "POSTGRES_DSN",
        "postgresql+psycopg://quantpoly:quantpoly@localhost:54329/quantpoly_test",
    )


def _reset_user_preferences(*, user_id: str) -> None:
    from user_preferences.store import PostgresPreferencesStore

    engine = create_engine(_postgres_dsn())
    store = PostgresPreferencesStore(engine=engine)
    store.ensure_schema()
    with engine.begin() as conn:
        conn.execute(text("delete from user_preferences where user_id=:user_id"), {"user_id": user_id})


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


@pytest.mark.integration
def test_cli_should_support_get_update_export_import_with_postgres_store():
    user_id = "cli-pg-u1"
    _reset_user_preferences(user_id=user_id)

    updated = _run_cli(
        [
            "update",
            "--user-id",
            user_id,
            "--user-level",
            "2",
            "--postgres-dsn",
            _postgres_dsn(),
            "--patch",
            '{"theme": {"darkMode": true}}',
        ]
    )
    assert updated["success"] is True
    assert updated["data"]["theme"]["darkMode"] is True

    got = _run_cli([
        "get",
        "--user-id",
        user_id,
        "--user-level",
        "2",
        "--postgres-dsn",
        _postgres_dsn(),
    ])
    assert got["success"] is True
    assert got["data"]["theme"]["darkMode"] is True

    exported = _run_cli([
        "export",
        "--user-id",
        user_id,
        "--user-level",
        "2",
        "--postgres-dsn",
        _postgres_dsn(),
    ])
    assert exported["success"] is True
    assert exported["data"]["theme"]["darkMode"] is True

    imported = _run_cli(
        [
            "import",
            "--user-id",
            user_id,
            "--user-level",
            "2",
            "--postgres-dsn",
            _postgres_dsn(),
        ],
        stdin_payload={"theme": {"primaryColor": "#00FF00", "darkMode": True}},
    )
    assert imported["success"] is True
    assert imported["data"]["theme"]["primaryColor"] == "#00FF00"


@pytest.mark.integration
def test_cli_update_should_reject_advanced_for_level1():
    user_id = "cli-pg-u2"
    _reset_user_preferences(user_id=user_id)

    payload = _run_cli(
        [
            "update",
            "--user-id",
            user_id,
            "--user-level",
            "1",
            "--postgres-dsn",
            _postgres_dsn(),
            "--patch",
            '{"advanced": {"betaFeatures": true}}',
        ]
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "ADVANCED_PERMISSION_DENIED"
