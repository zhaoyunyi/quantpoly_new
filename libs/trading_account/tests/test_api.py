"""trading_account API 路由测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from trading_account.api import create_router
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_list_accounts_returns_only_current_user():
    app, service = _build_app(current_user_id="u-1")
    mine = service.create_account(user_id="u-1", account_name="primary")
    service.create_account(user_id="u-2", account_name="other")

    client = TestClient(app)
    resp = client.get("/trading/accounts")

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == mine.id
    assert data["data"][0]["userId"] == "u-1"
    assert data["data"][0]["accountName"] == "primary"


def test_get_positions_forbidden_for_non_owner_account():
    app, service = _build_app(current_user_id="u-1")
    other_account = service.create_account(user_id="u-2", account_name="other")
    service.upsert_position(
        user_id="u-2",
        account_id=other_account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )

    client = TestClient(app)
    resp = client.get(f"/trading/accounts/{other_account.id}/positions")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ACCOUNT_ACCESS_DENIED"


def test_trade_stats_forbidden_for_non_owner_account():
    app, service = _build_app(current_user_id="u-1")
    other_account = service.create_account(user_id="u-2", account_name="other")
    service.record_trade(
        user_id="u-2",
        account_id=other_account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )

    client = TestClient(app)
    resp = client.get(f"/trading/accounts/{other_account.id}/trade-stats")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ACCOUNT_ACCESS_DENIED"


def test_trade_stats_returns_envelope_with_camel_case_fields():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")
    service.record_trade(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )

    client = TestClient(app)
    resp = client.get(f"/trading/accounts/{account.id}/trade-stats")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["tradeCount"] == 1
    assert payload["data"]["turnover"] == 1000

