"""trading_account 运维任务化 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(
    *,
    current_user_id: str,
    is_admin: bool | None = False,
    role: str | None = None,
    level: int | None = None,
):
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService
    from trading_account.api import create_router
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    class _User:
        def __init__(self, user_id: str, admin: bool | None, user_role: str | None, user_level: int | None):
            self.id = user_id
            if admin is not None:
                self.is_admin = admin
            if user_role is not None:
                self.role = user_role
            if user_level is not None:
                self.level = user_level

    def _get_current_user():
        return _User(current_user_id, is_admin, role, level)

    service = TradingAccountService(repository=InMemoryTradingAccountRepository())
    job_service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user, job_service=job_service))
    return app, service, job_service


def test_refresh_prices_task_endpoint_returns_task_result_for_admin():
    app, service, job_service = _build_app(current_user_id="admin-1", is_admin=None, role="admin")
    client = TestClient(app)

    account = service.create_account(user_id="admin-1", account_name="primary")
    service.upsert_position(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )

    resp = client.post(
        "/trading/ops/refresh-prices/task",
        json={"priceUpdates": {"AAPL": 130}, "idempotencyKey": "trading-task-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "trading_refresh_prices"
    assert payload["data"]["result"]["updatedSymbols"] == ["AAPL"]

    job = job_service.get_job(user_id="admin-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.status == "succeeded"


def test_refresh_prices_task_endpoint_requires_admin():
    app, _service, _job_service = _build_app(current_user_id="u-1", is_admin=False)
    client = TestClient(app)

    resp = client.post(
        "/trading/ops/refresh-prices/task",
        json={"priceUpdates": {"AAPL": 130}, "idempotencyKey": "trading-task-no-admin"},
    )

    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ADMIN_REQUIRED"
