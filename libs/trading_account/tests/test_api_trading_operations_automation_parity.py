"""trading_account 交易运营自动化任务 API 测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str, is_admin: bool):
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService
    from trading_account.api import create_router
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    class _User:
        def __init__(self, user_id: str, admin: bool):
            self.id = user_id
            self.is_admin = admin

    def _get_current_user():
        return _User(current_user_id, is_admin)

    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    job_service = JobOrchestrationService(repository=InMemoryJobRepository(), scheduler=InMemoryScheduler())

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user, job_service=job_service))
    return app, service, repo, job_service


def test_submit_pending_process_task_requires_admin():
    app, service, _repo, _job_service = _build_app(current_user_id="u-1", is_admin=False)
    account = service.create_account(user_id="u-1", account_name="primary")
    service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )

    client = TestClient(app)
    resp = client.post("/trading/ops/pending/process-task", json={"maxTrades": 10, "idempotencyKey": "pp-1"})

    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ADMIN_REQUIRED"


def test_pending_process_task_returns_job_and_fills_orders_for_admin():
    app, service, _repo, job_service = _build_app(current_user_id="admin-1", is_admin=True)
    account = service.create_account(user_id="admin-1", account_name="primary")

    order1 = service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )
    order2 = service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="MSFT",
        side="SELL",
        quantity=2,
        price=50,
    )

    client = TestClient(app)
    resp = client.post(
        "/trading/ops/pending/process-task",
        json={"maxTrades": 100, "idempotencyKey": "pp-2"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "trading_pending_process"
    assert payload["data"]["status"] == "succeeded"
    assert payload["data"]["error"] is None
    assert payload["data"]["result"]["processed"] == 2
    assert payload["data"]["result"]["auditId"]

    assert service.get_order(user_id="admin-1", account_id=account.id, order_id=order1.id).status == "filled"
    assert service.get_order(user_id="admin-1", account_id=account.id, order_id=order2.id).status == "filled"
    assert len(service.list_trades(user_id="admin-1", account_id=account.id)) == 2

    job = job_service.get_job(user_id="admin-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.status == "succeeded"


def test_pending_process_task_idempotency_conflict_returns_409():
    app, service, _repo, _job_service = _build_app(current_user_id="admin-1", is_admin=True)
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )

    client = TestClient(app)
    first = client.post(
        "/trading/ops/pending/process-task",
        json={"maxTrades": 10, "idempotencyKey": "pp-idem"},
    )
    assert first.status_code == 200

    conflict = client.post(
        "/trading/ops/pending/process-task",
        json={"maxTrades": 10, "idempotencyKey": "pp-idem"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_daily_stats_task_generates_snapshot_and_can_be_read_back():
    app, service, _repo, _job_service = _build_app(current_user_id="admin-1", is_admin=True)
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.deposit(user_id="admin-1", account_id=account.id, amount=1000)
    order = service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )
    service.fill_order(user_id="admin-1", account_id=account.id, order_id=order.id)

    target_date = "2026-02-10"

    client = TestClient(app)
    resp = client.post(
        "/trading/ops/daily-stats/calculate-task",
        json={"accountIds": [account.id], "targetDate": target_date, "idempotencyKey": "ds-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "trading_daily_stats_calculate"
    assert payload["data"]["status"] == "succeeded"
    assert payload["data"]["error"] is None
    assert payload["data"]["result"]["date"] == target_date
    assert payload["data"]["result"]["auditId"]

    stats = client.get("/trading/stats/daily", params={"date": target_date, "accountId": account.id})
    assert stats.status_code == 200
    stats_payload = stats.json()
    assert stats_payload["success"] is True
    assert stats_payload["data"]["date"] == target_date
    assert stats_payload["data"]["items"][0]["accountId"] == account.id


def test_account_cleanup_task_deletes_old_cancelled_orders_and_tracks_job_status():
    app, service, repo, job_service = _build_app(current_user_id="admin-1", is_admin=True)
    account = service.create_account(user_id="admin-1", account_name="primary")
    order = service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )
    service.cancel_order(user_id="admin-1", account_id=account.id, order_id=order.id)

    stored = repo.get_order(account_id=account.id, user_id="admin-1", order_id=order.id)
    assert stored is not None
    stored.updated_at = datetime.now(timezone.utc) - timedelta(days=120)
    repo.save_order(stored)

    client = TestClient(app)
    resp = client.post(
        "/trading/ops/accounts/cleanup-task",
        json={"accountIds": [account.id], "daysThreshold": 90, "idempotencyKey": "cleanup-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "trading_account_cleanup"
    assert payload["data"]["error"] is None
    assert payload["data"]["result"]["auditId"]

    status = client.get(f"/trading/ops/tasks/{payload['data']['taskId']}")
    assert status.status_code == 200
    assert status.json()["data"]["status"] == "succeeded"

    assert repo.get_order(account_id=account.id, user_id="admin-1", order_id=order.id) is None

    job = job_service.get_job(user_id="admin-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.status == "succeeded"


def test_batch_execute_task_creates_and_fills_orders_for_admin():
    app, service, _repo, _job_service = _build_app(current_user_id="admin-1", is_admin=True)
    account = service.create_account(user_id="admin-1", account_name="primary")

    client = TestClient(app)
    resp = client.post(
        "/trading/ops/batch/execute-task",
        json={
            "tradeRequests": [
                {
                    "accountId": account.id,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "quantity": 1,
                    "price": 100,
                }
            ],
            "idempotencyKey": "batch-1",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "trading_batch_execute"
    assert payload["data"]["status"] == "succeeded"
    assert payload["data"]["error"] is None
    assert payload["data"]["result"]["total"] == 1
    assert payload["data"]["result"]["success"] == 1
    assert payload["data"]["result"]["auditId"]

    orders = service.list_orders(user_id="admin-1", account_id=account.id)
    assert len(orders) == 1
    assert orders[0].status == "filled"


def test_risk_monitor_task_returns_risk_metrics_for_account():
    app, service, _repo, _job_service = _build_app(current_user_id="admin-1", is_admin=True)
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.deposit(user_id="admin-1", account_id=account.id, amount=1000)
    service.upsert_position(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=1,
        avg_price=100,
        last_price=120,
    )

    client = TestClient(app)
    resp = client.post(
        "/trading/ops/risk/monitor-task",
        json={"accountIds": [account.id], "idempotencyKey": "rm-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "trading_risk_monitor"
    assert payload["data"]["error"] is None
    assert payload["data"]["result"]["totalAccounts"] == 1
    assert payload["data"]["result"]["items"][0]["accountId"] == account.id
    assert payload["data"]["result"]["auditId"]


def test_batch_execute_task_marks_job_failed_and_returns_error_when_request_fails():
    app, service, _repo, _job_service = _build_app(current_user_id="admin-1", is_admin=True)
    account = service.create_account(user_id="admin-1", account_name="primary")

    client = TestClient(app)
    resp = client.post(
        "/trading/ops/batch/execute-task",
        json={
            "tradeRequests": [
                {
                    "accountId": account.id,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "quantity": 1,
                    "price": 100,
                },
                {
                    "accountId": "not-owned",
                    "symbol": "MSFT",
                    "side": "BUY",
                    "quantity": 1,
                    "price": 50,
                },
            ],
            "idempotencyKey": "batch-fail-1",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "trading_batch_execute"
    assert payload["data"]["status"] == "failed"
    assert payload["data"]["error"]["code"] == "TRADING_BATCH_EXECUTE_FAILED"
    assert payload["data"]["result"]["failed"] == 1
    assert payload["data"]["result"]["auditId"]
