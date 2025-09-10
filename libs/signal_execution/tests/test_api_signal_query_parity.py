"""signal_execution 手动过期与账户统计 API 对齐测试。"""

from __future__ import annotations

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


def test_api_should_support_manual_expire_and_account_statistics():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    pending = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    executed = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=executed.id)

    resp = client.post(f"/signals/{pending.id}/expire")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "expired"

    stats = client.get("/signals/statistics/u-1-account")
    assert stats.status_code == 200
    data = stats.json()["data"]
    assert data["accountId"] == "u-1-account"
    assert data["total"] == 2
    assert data["expired"] == 1
    assert data["executed"] == 1


def test_api_should_reject_foreign_signal_or_account_statistics():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    foreign = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy",
        account_id="u-2-account",
        symbol="TSLA",
        side="BUY",
    )

    denied = client.post(f"/signals/{foreign.id}/expire")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "SIGNAL_ACCESS_DENIED"

    denied_stats = client.get("/signals/statistics/u-2-account")
    assert denied_stats.status_code == 403
    assert denied_stats.json()["error"]["code"] == "SIGNAL_ACCESS_DENIED"
