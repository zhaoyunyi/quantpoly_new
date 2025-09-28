"""backtest_runner 任务化提交 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from backtest_runner.api import create_router
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestService
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    job_service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )
    service = BacktestService(repository=InMemoryBacktestRepository())

    app = FastAPI()
    app.include_router(
        create_router(
            service=service,
            get_current_user=_get_current_user,
            job_service=job_service,
        )
    )
    return app, service, job_service


def test_submit_backtest_task_returns_orchestration_task_handle():
    app, service, job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    resp = client.post(
        "/backtests/tasks",
        json={
            "strategyId": "s-1",
            "config": {
                "symbol": "AAPL",
                "prices": [100, 100, 100, 100, 100, 101, 102, 103, 102, 101, 100, 99],
                "parameters": {"shortWindow": 3, "longWindow": 5},
            },
            "idempotencyKey": "bk-task-1",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "backtest_run"
    assert payload["data"]["status"] in {"running", "succeeded"}

    backtests = service.list_tasks(user_id="u-1")
    assert backtests["total"] == 1

    job_id = payload["data"]["taskId"]
    job = job_service.get_job(user_id="u-1", job_id=job_id)
    assert job is not None
    assert job.executor_name is not None
    assert job.dispatch_id is not None


def test_submit_backtest_task_conflict_returns_409():
    app, _service, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    first = client.post(
        "/backtests/tasks",
        json={
            "strategyId": "s-1",
            "config": {"symbol": "AAPL"},
            "idempotencyKey": "bk-task-dup",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/backtests/tasks",
        json={
            "strategyId": "s-2",
            "config": {"symbol": "MSFT"},
            "idempotencyKey": "bk-task-dup",
        },
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] in {"BACKTEST_IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_CONFLICT"}
