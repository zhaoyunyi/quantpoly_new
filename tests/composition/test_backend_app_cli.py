"""backend_app CLI 测试。"""

from __future__ import annotations

import json
import subprocess
import sys


PYTHON = sys.executable or "python3"
CLI_MODULE = "apps.backend_app.cli"


def test_cli_resolve_settings_from_stdin_json():
    payload = {
        "storageBackend": "memory",
        "marketDataProvider": "alpaca",
        "enabledContexts": ["market-data"],
    }

    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, "resolve-settings"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["data"]["storageBackend"] == "memory"
    assert data["data"]["marketDataProvider"] == "alpaca"
    assert "user-auth" in data["data"]["enabledContexts"]


def test_cli_rejects_invalid_market_data_provider():
    payload = {
        "storageBackend": "sqlite",
        "marketDataProvider": "unknown",
    }

    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, "resolve-settings"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_ARGUMENT"
