"""job_orchestration CLI 测试。"""

from __future__ import annotations

import argparse
import json

from job_orchestration import cli
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import JobOrchestrationService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_submit_and_status(capsys, monkeypatch):
    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )
    monkeypatch.setattr(cli, "_service", service)

    submitted = _run(
        cli._cmd_submit,
        capsys=capsys,
        user_id="u-1",
        task_type="backtest_run",
        payload='{"strategyId":"s-1"}',
        idempotency_key="k-1",
    )
    job_id = submitted["data"]["id"]

    status = _run(cli._cmd_status, capsys=capsys, user_id="u-1", job_id=job_id)
    assert submitted["success"] is True
    assert status["success"] is True
    assert status["data"]["status"] == "queued"


def test_cli_cancel_foreign_job_returns_access_denied(capsys, monkeypatch):
    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )
    monkeypatch.setattr(cli, "_service", service)

    job = service.submit_job(
        user_id="u-2",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-foreign",
    )

    payload = _run(cli._cmd_cancel, capsys=capsys, user_id="u-1", job_id=job.id)
    assert payload["success"] is False
    assert payload["error"]["code"] == "JOB_ACCESS_DENIED"

