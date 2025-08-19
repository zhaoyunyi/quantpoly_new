"""signal_execution 批处理任务化 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService
    from signal_execution.api import create_router
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id
            self.is_admin = False

    def _get_current_user():
        return _User(current_user_id)

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    job_service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user, job_service=job_service))
    return app, service, job_service


def test_batch_execute_task_endpoint_returns_task_handle_and_result():
    app, service, job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    s2 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )

    resp = client.post(
        "/signals/batch/execute-task",
        json={"signalIds": [s1.id, s2.id], "idempotencyKey": "sig-task-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "signal_batch_execute"
    assert payload["data"]["result"]["executed"] == 2

    job = job_service.get_job(user_id="u-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.status == "succeeded"


def test_batch_cancel_task_endpoint_supports_idempotency_conflict():
    app, service, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    signal = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )

    first = client.post(
        "/signals/batch/cancel-task",
        json={"signalIds": [signal.id], "idempotencyKey": "sig-cancel-task-1"},
    )
    assert first.status_code == 200

    second = client.post(
        "/signals/batch/cancel-task",
        json={"signalIds": [signal.id, "x-2"], "idempotencyKey": "sig-cancel-task-1"},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
