"""backend docker 开发脚本测试。"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


SCRIPT_PATH = Path("scripts/backend_docker_dev.sh")


def _run_script(*args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_up_print_only_should_emit_default_compose_plan():
    result = _run_script("up", "--print-only")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["action"] == "up"
    assert payload["env"]["BACKEND_PORT"] == "8000"
    assert payload["env"]["BACKEND_CORS_ALLOWED_ORIGINS"] == "http://localhost:3300"
    assert payload["env"]["BACKEND_STORAGE_BACKEND"] == "postgres"
    assert "docker-compose.backend-dev.yml" in payload["compose_file"]
    assert "up -d --build" in payload["commands"]["up"]


def test_invalid_action_should_fail_with_json_error():
    result = _run_script("unknown-action", "--print-only")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_ARGUMENT"

