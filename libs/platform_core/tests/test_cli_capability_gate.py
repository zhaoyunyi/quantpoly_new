"""capability gate CLI 测试。"""

from __future__ import annotations

import json
import subprocess
import sys


PYTHON = sys.executable or "python3.11"
CLI_MODULE = "platform_core.cli"


def _run_gate(payload: dict):
    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, "capability-gate"],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
    )
    return result.returncode, json.loads(result.stdout)


def test_capability_gate_blocks_when_critical_capability_missing():
    payload = {
        "wave": "wave-1",
        "capabilities": [
            {"id": "auth_login", "passed": False, "critical": True},
            {"id": "strategy_list", "passed": True, "critical": True},
        ],
        "postCutoverMetrics": {
            "errorRate": 0.01,
            "p95LatencyMs": 180,
            "queueBacklog": 2,
            "dataLeakage": False,
        },
    }

    code, body = _run_gate(payload)

    assert code == 0
    assert body["success"] is True
    assert body["data"]["allowed"] is False
    assert body["data"]["rollbackRequired"] is True
    assert "critical_capability_missing:auth_login" in body["data"]["blockers"]


def test_capability_gate_passes_when_all_conditions_meet_thresholds():
    payload = {
        "wave": "wave-2",
        "capabilities": [
            {"id": "auth_login", "passed": True, "critical": True},
            {"id": "market_quote", "passed": True, "critical": True},
            {"id": "monitor_summary", "passed": True, "critical": False},
        ],
        "postCutoverMetrics": {
            "errorRate": 0.02,
            "p95LatencyMs": 250,
            "queueBacklog": 5,
            "dataLeakage": False,
        },
    }

    code, body = _run_gate(payload)

    assert code == 0
    assert body["success"] is True
    assert body["data"]["allowed"] is True
    assert body["data"]["rollbackRequired"] is False
    assert body["data"]["summary"]["criticalFailed"] == 0
