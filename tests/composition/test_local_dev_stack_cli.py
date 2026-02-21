"""本地前后端联调一键脚本 CLI 测试。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PYTHON = sys.executable or "python3"
SCRIPT_PATH = Path("scripts/local_dev_stack.py")


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
    )


def test_cli_up_print_only_should_emit_start_plan_with_default_ports():
    result = _run_cli("up", "--print-only")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["action"] == "up"
    assert payload["plan"]["backend_origin"] == "http://localhost:8000"
    assert payload["plan"]["frontend_origin"] == "http://localhost:3300"
    assert payload["plan"]["backend_env"]["BACKEND_CORS_ALLOWED_ORIGINS"] == "http://localhost:3300"
    assert payload["plan"]["frontend_env"]["VITE_BACKEND_ORIGIN"] == "http://localhost:8000"


def test_cli_up_postgres_without_dsn_should_fail():
    result = _run_cli("up", "--print-only", "--backend-storage", "postgres")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_ARGUMENT"
    assert "BACKEND_POSTGRES_DSN" in payload["error"]["message"]


def test_cli_up_with_non_default_frontend_port_should_fail():
    result = _run_cli("up", "--print-only", "--frontend-port", "3310")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_ARGUMENT"
    assert "3300" in payload["error"]["message"]


def test_cli_status_without_state_should_report_not_running(tmp_path: Path):
    result = _run_cli("status", "--state-dir", str(tmp_path))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["action"] == "status"
    assert payload["running"] is False
