"""risk_control CLI 自动化任务对齐测试。"""

from __future__ import annotations

import json
import subprocess
import sys


PYTHON = sys.executable or "python3"
CLI_MODULE = "risk_control.cli"


def _run(args: list[str]) -> dict:
    proc = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        env={"PATH": "", "PYTHONPATH": "libs/risk_control"},
    )
    assert proc.returncode == 0
    return json.loads(proc.stdout)


def test_cli_risk_report_generate_outputs_summary():
    payload = _run([PYTHON, "-m", CLI_MODULE, "report-generate", "--user-id", "u-1", "--report-type", "daily"])

    assert payload["success"] is True
    assert payload["data"]["summary"]


def test_cli_alert_cleanup_outputs_audit_id_and_deleted_count():
    payload = _run([PYTHON, "-m", CLI_MODULE, "alert-cleanup", "--user-id", "u-1", "--retention-days", "3"])

    assert payload["success"] is True
    assert "auditId" in payload["data"]
    assert "deleted" in payload["data"]
