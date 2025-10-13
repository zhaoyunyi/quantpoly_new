"""monitoring-realtime CLI 测试。

BDD Scenarios:
- heartbeat 输出 JSON 且包含 type/ts
"""

import json
import subprocess
import sys


PYTHON = sys.executable or "python3.11"
CLI_MODULE = "monitoring_realtime.cli"


def test_heartbeat_command_outputs_json():
    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, "heartbeat", "--ts", "1700000000"],
        capture_output=True,
        text=True,
        env={
            "PATH": "",
            "PYTHONPATH": "libs/monitoring_realtime",
        },
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["data"]["type"] == "monitor.heartbeat"
    assert data["data"]["ts"] == 1700000000


def test_summary_command_builds_operational_summary_from_snapshot_json():
    snapshot = {
        "accounts": [
            {"id": "acc-1", "userId": "u-1", "status": "active"},
            {"id": "acc-x", "userId": "u-foreign", "status": "active"},
        ],
        "strategies": [
            {"id": "st-1", "userId": "u-1", "status": "active"},
            {"id": "st-2", "userId": "u-1", "status": "draft"},
        ],
        "backtests": [
            {"id": "bt-1", "userId": "u-1", "status": "running"},
            {"id": "bt-2", "userId": "u-1", "status": "completed"},
        ],
        "tasks": [
            {"taskId": "job-1", "userId": "u-1", "status": "running"},
            {"taskId": "job-2", "userId": "u-1", "status": "failed"},
        ],
        "signals": [
            {"id": "sig-1", "userId": "u-1", "status": "pending"},
            {"id": "sig-2", "userId": "u-1", "status": "expired"},
        ],
        "alerts": [
            {"id": "a-1", "userId": "u-1", "severity": "critical", "status": "open"},
            {"id": "a-2", "userId": "u-1", "severity": "low", "status": "resolved"},
        ],
    }

    result = subprocess.run(
        [PYTHON, "-m", CLI_MODULE, "summary", "--user-id", "u-1"],
        input=json.dumps(snapshot, ensure_ascii=False),
        capture_output=True,
        text=True,
        env={
            "PATH": "",
            "PYTHONPATH": "libs/monitoring_realtime",
        },
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True

    summary = payload["data"]
    assert summary["metadata"]["version"] == "v2"
    assert summary["accounts"]["total"] == 1
    assert summary["strategies"]["total"] == 2
    assert summary["backtests"]["running"] == 1
    assert summary["tasks"]["running"] == 1
    assert summary["tasks"]["failed"] == 1
    assert summary["signals"]["pending"] == 1
    assert summary["signals"]["expired"] == 1
    assert summary["alerts"]["open"] == 1
    assert summary["alerts"]["critical"] == 1
