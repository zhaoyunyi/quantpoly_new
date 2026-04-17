"""本地 Coolify Compose + Playwright 一键验证脚本测试。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PYTHON = sys.executable or "python3"
SCRIPT_PATH = Path("scripts/verify_coolify_local_stack.py")


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
    )


def test_print_only_should_emit_compose_and_playwright_plan():
    result = _run_cli("--print-only")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["action"] == "verify"
    assert payload["plan"]["project_name"] == "quantpoly_local_browser"
    assert payload["plan"]["compose_files"] == [
        "docker-compose.coolify.yml",
        "docker-compose.coolify.local.yml",
    ]
    assert payload["plan"]["env"]["POSTGRES_PASSWORD"] == "quantpoly_local_pw"
    assert payload["plan"]["env"]["VITE_BACKEND_ORIGIN"] == "http://localhost:18000"
    assert (
        payload["plan"]["env"]["BACKEND_CORS_ALLOWED_ORIGINS"]
        == "http://localhost:13000"
    )
    assert payload["plan"]["env"]["USER_AUTH_COOKIE_SECURE"] == "false"
    assert "--config playwright.compose.config.ts" in payload["plan"]["commands"]["e2e"]
    assert "PLAYWRIGHT_BACKEND_PORT=18000" in payload["plan"]["commands"]["e2e"]
    assert "up -d --build" in payload["plan"]["commands"]["up"]
    assert "down -v" in payload["plan"]["commands"]["down"]

