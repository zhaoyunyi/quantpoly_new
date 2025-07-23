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

