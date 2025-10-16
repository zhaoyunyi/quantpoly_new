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


def test_cli_types_lists_task_registry(capsys, monkeypatch):
    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )
    monkeypatch.setattr(cli, "_service", service)

    payload = _run(cli._cmd_types, capsys=capsys)

    assert payload["success"] is True
    rows = payload["data"]
    item = next(row for row in rows if row["taskType"] == "risk_report_generate")
    assert item["domain"] == "risk"
    assert item["priority"] >= 0
    assert item["timeoutSeconds"] > 0
    assert item["maxRetries"] >= 0
    assert item["concurrencyLimit"] >= 1


def test_cli_schedule_list_and_stop_scoped_by_user(capsys, monkeypatch):
    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )
    monkeypatch.setattr(cli, "_service", service)

    created = _run(
        cli._cmd_schedule_interval,
        capsys=capsys,
        user_id="u-1",
        task_type="market_data_sync",
        every_seconds=60,
    )
    schedule_id = created["data"]["id"]

    listed = _run(cli._cmd_schedules, capsys=capsys, user_id="u-1")
    assert any(item["id"] == schedule_id for item in listed["data"])

    denied = _run(cli._cmd_schedule_stop, capsys=capsys, user_id="u-2", schedule_id=schedule_id)
    assert denied["success"] is False
    assert denied["error"]["code"] == "SCHEDULE_ACCESS_DENIED"

    stopped = _run(cli._cmd_schedule_stop, capsys=capsys, user_id="u-1", schedule_id=schedule_id)
    assert stopped["success"] is True
    assert stopped["data"]["status"] == "stopped"


def test_cli_status_includes_runtime_and_execution_observability(capsys, monkeypatch):
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
        idempotency_key="k-runtime-status-1",
    )
    job_id = submitted["data"]["id"]

    _run(cli._cmd_transition, capsys=capsys, user_id="u-1", job_id=job_id, to_status="running")

    status = _run(cli._cmd_status, capsys=capsys, user_id="u-1", job_id=job_id)

    assert status["success"] is True
    assert status["data"]["startedAt"] is not None
    assert status["data"]["finishedAt"] is None
    assert "runtime" in status
    assert "executor" in status["runtime"]



def test_cli_templates_recover_and_list_include_runtime(capsys, monkeypatch):
    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )
    monkeypatch.setattr(cli, "_service", service)

    recovered = _run(cli._cmd_templates_recover, capsys=capsys)
    listed = _run(cli._cmd_templates, capsys=capsys)

    assert recovered["success"] is True
    assert recovered["data"]["total"] >= 4
    assert "runtime" in recovered

    assert listed["success"] is True
    assert len(listed["data"]) >= 4
    assert "runtime" in listed
