"""signal_execution 策略驱动自动化能力测试（Wave3）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str, risk_passed: bool = True, is_admin: bool = False):
    from signal_execution.api import create_router
    from signal_execution.domain import ExecutionRecord
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    class _User:
        def __init__(self, user_id: str, admin: bool):
            self.id = user_id
            self.is_admin = admin

    def _get_current_user():
        return _User(current_user_id, is_admin)

    def _risk_checker(*, user_id: str, account_id: str, strategy_id: str):
        del user_id, account_id, strategy_id
        if risk_passed:
            return {"passed": True, "riskScore": 10.0, "riskLevel": "low"}
        return {"passed": False, "riskScore": 90.0, "riskLevel": "high"}

    repo = InMemorySignalRepository()
    service = SignalExecutionService(
        repository=repo,
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
        risk_checker=_risk_checker,
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service, repo, ExecutionRecord


def test_generate_signals_endpoint_creates_pending_signals():
    app, _service, _repo, _ExecutionRecord = _build_app(current_user_id="u-1")
    client = TestClient(app)

    resp = client.post(
        "/signals/generate",
        json={
            "strategyId": "u-1-strategy-1",
            "accountId": "u-1-account-1",
            "symbols": ["AAPL", "MSFT"],
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    items = payload["data"]["signals"]
    assert len(items) == 2
    assert {item["symbol"] for item in items} == {"AAPL", "MSFT"}
    assert all(item["status"] == "pending" for item in items)


def test_process_signal_risk_failure_cancels_signal():
    app, service, _repo, _ExecutionRecord = _build_app(current_user_id="u-1", risk_passed=False)
    client = TestClient(app)

    signal = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy-1",
        account_id="u-1-account-1",
        symbol="AAPL",
        side="BUY",
    )

    resp = client.post(f"/signals/{signal.id}/process")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "cancelled"
    assert payload["data"]["risk"]["riskLevel"] == "high"

    updated = service.get_signal(user_id="u-1", signal_id=signal.id)
    assert updated is not None
    assert updated.status == "cancelled"


def test_daily_trend_endpoint_groups_executions_by_day():
    app, service, repo, ExecutionRecord = _build_app(current_user_id="u-1")
    client = TestClient(app)

    now = datetime.now(timezone.utc)

    repo.save_execution(
        ExecutionRecord(
            id="e-1",
            user_id="u-1",
            signal_id="s-1",
            strategy_id="u-1-strategy-1",
            symbol="AAPL",
            status="executed",
            metrics={"pnl": 1.0},
            created_at=now - timedelta(days=1),
        )
    )
    repo.save_execution(
        ExecutionRecord(
            id="e-2",
            user_id="u-1",
            signal_id="s-2",
            strategy_id="u-1-strategy-1",
            symbol="MSFT",
            status="cancelled",
            metrics={},
            created_at=now - timedelta(days=2),
        )
    )

    resp = client.get("/signals/trends/daily", params={"days": 3})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    series = payload["data"]
    assert len(series) == 2
    assert sum(item["total"] for item in series) == 2


def test_signal_performance_endpoint_returns_summary():
    app, service, _repo, _ExecutionRecord = _build_app(current_user_id="u-1")
    client = TestClient(app)

    signal = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy-1",
        account_id="u-1-account-1",
        symbol="AAPL",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=signal.id, execution_metrics={"pnl": 2.5})

    resp = client.get(f"/signals/performance/{signal.id}")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["signalId"] == signal.id
    assert payload["data"]["totalExecutions"] == 1
    assert payload["data"]["averagePnl"] == 2.5
