"""storage-contract-gate CLI 测试。"""

from __future__ import annotations

import json
import subprocess
import sys


PYTHON = sys.executable or "python3.11"
CLI_MODULE = "platform_core.cli"


def _run_gate(payload: dict | None = None):
    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, "storage-contract-gate"],
        input=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
        capture_output=True,
        text=True,
    )
    return result.returncode, json.loads(result.stdout)


def test_storage_contract_gate_default_modules_should_pass():
    code, body = _run_gate()

    assert code == 0
    assert body["success"] is True
    assert body["data"]["allowed"] is True
    assert body["data"]["summary"]["checkedModules"] >= 8


def test_storage_contract_gate_should_block_when_forbidden_export_detected():
    code, body = _run_gate(
        {
            "modules": [
                {"name": "fake.module", "exports": ["InMemoryRepo", "SQLiteRepo"]},
            ],
            "forbiddenTokens": ["SQLite", "sqlite"],
        }
    )

    assert code == 0
    assert body["success"] is True
    assert body["data"]["allowed"] is False
    assert body["data"]["summary"]["violations"] == 1
    assert body["data"]["violations"][0]["module"] == "fake.module"


def test_storage_contract_gate_should_reject_invalid_payload():
    code, body = _run_gate({"forbiddenTokens": "SQLite"})

    assert code == 0
    assert body["success"] is False
    assert body["error"]["code"] == "STORAGE_CONTRACT_GATE_INVALID_INPUT"
