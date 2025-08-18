"""signal_execution 信号中心读模型补齐测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
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

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_signal_detail_endpoint_returns_current_user_signal():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    signal = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-growth",
        account_id="u-1-account-1",
        symbol="AAPL",
        side="BUY",
    )

    resp = client.get(f"/signals/{signal.id}")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == signal.id
    assert payload["data"]["status"] == "pending"


def test_signal_detail_endpoint_rejects_foreign_signal():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    foreign_signal = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-growth",
        account_id="u-2-account-1",
        symbol="MSFT",
        side="BUY",
    )

    resp = client.get(f"/signals/{foreign_signal.id}")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_ACCESS_DENIED"


def test_pending_and_expired_shortcuts_follow_status_semantics():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    pending = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-growth",
        account_id="u-1-account-1",
        symbol="AAPL",
        side="BUY",
    )
    executed = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-growth",
        account_id="u-1-account-1",
        symbol="MSFT",
        side="BUY",
    )
    expired = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-mean-revert",
        account_id="u-1-account-1",
        symbol="TSLA",
        side="SELL",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    service.execute_signal(user_id="u-1", signal_id=executed.id)
    service.update_expired_signals(user_id="u-1")

    pending_resp = client.get("/signals/pending")
    assert pending_resp.status_code == 200
    pending_ids = [item["id"] for item in pending_resp.json()["data"]]
    assert pending_ids == [pending.id]

    expired_resp = client.get("/signals/expired")
    assert expired_resp.status_code == 200
    expired_ids = [item["id"] for item in expired_resp.json()["data"]]
    assert expired_ids == [expired.id]


def test_signal_search_and_dashboard_are_user_scoped_and_account_scoped():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    account_a = "u-1-account-a"
    account_b = "u-1-account-b"

    pending_a = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-mean-revert",
        account_id=account_a,
        symbol="AAPL",
        side="BUY",
    )
    expired_a = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-mean-revert",
        account_id=account_a,
        symbol="TSLA",
        side="SELL",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    executed_b = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-breakout",
        account_id=account_b,
        symbol="NVDA",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=executed_b.id)
    service.update_expired_signals(user_id="u-1")

    service.create_signal(
        user_id="u-2",
        strategy_id="u-2-mean-revert",
        account_id="u-2-account-a",
        symbol="AAPL",
        side="BUY",
    )

    search_resp = client.get(
        "/signals/search",
        params={"keyword": "mean", "accountId": account_a},
    )
    assert search_resp.status_code == 200
    search_ids = [item["id"] for item in search_resp.json()["data"]]
    assert search_ids == [pending_a.id, expired_a.id]

    dashboard_resp = client.get("/signals/dashboard", params={"accountId": account_a})
    assert dashboard_resp.status_code == 200
    dashboard = dashboard_resp.json()["data"]

    assert dashboard["total"] == 2
    assert dashboard["pending"] == 1
    assert dashboard["expired"] == 1
    assert dashboard["executed"] == 0

    assert len(dashboard["byAccount"]) == 1
    assert dashboard["byAccount"][0]["accountId"] == account_a
    assert dashboard["byAccount"][0]["total"] == 2
    assert dashboard["byAccount"][0]["pending"] == 1
    assert dashboard["byAccount"][0]["expired"] == 1
