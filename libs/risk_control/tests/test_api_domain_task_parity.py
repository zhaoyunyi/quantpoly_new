"""risk_control 任务化评估 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService
    from risk_control.api import create_router
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import RiskControlService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    job_service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user, job_service=job_service))
    return app, service, job_service


def test_evaluate_task_endpoint_returns_task_handle_and_snapshot_result():
    app, _service, job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    resp = client.post(
        "/risk/accounts/u-1-account/evaluate-task",
        json={"idempotencyKey": "risk-task-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "risk_account_evaluate"
    assert payload["data"]["result"]["accountId"] == "u-1-account"

    job = job_service.get_job(user_id="u-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.status == "succeeded"


def test_evaluate_task_endpoint_rejects_foreign_account():
    app, _service, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    resp = client.post(
        "/risk/accounts/u-2-account/evaluate-task",
        json={"idempotencyKey": "risk-task-foreign"},
    )

    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "RULE_ACCESS_DENIED"
