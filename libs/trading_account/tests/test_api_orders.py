"""订单与账本 API 测试。"""

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


def test_order_endpoints_cover_create_fill_and_query_views():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")
    client = TestClient(app)

    created = client.post(
        f"/trading/accounts/{account.id}/orders",
        json={"symbol": "AAPL", "side": "BUY", "quantity": 10, "price": 100},
    )
    assert created.status_code == 200
    order_id = created.json()["data"]["id"]

    filled = client.post(f"/trading/accounts/{account.id}/orders/{order_id}/fill")
    assert filled.status_code == 200
    assert filled.json()["data"]["status"] == "filled"

    order_detail = client.get(f"/trading/accounts/{account.id}/orders/{order_id}")
    assert order_detail.status_code == 200
    assert order_detail.json()["data"]["status"] == "filled"

    trades = client.get(f"/trading/accounts/{account.id}/trades")
    assert trades.status_code == 200
    assert len(trades.json()["data"]) == 1

    cash_flows = client.get(f"/trading/accounts/{account.id}/cash-flows")
    assert cash_flows.status_code == 200
    assert len(cash_flows.json()["data"]) == 1
    assert cash_flows.json()["data"][0]["amount"] == -1000


def test_order_not_found_returns_consistent_envelope():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")

    client = TestClient(app)
    resp = client.get(f"/trading/accounts/{account.id}/orders/not-exists")

    assert resp.status_code == 404
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ORDER_NOT_FOUND"


def test_order_read_is_forbidden_for_non_owner():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-2", account_name="other")
    order = service.submit_order(
        user_id="u-2",
        account_id=account.id,
        symbol="MSFT",
        side="SELL",
        quantity=3,
        price=200,
    )

    client = TestClient(app)
    resp = client.get(f"/trading/accounts/{account.id}/orders/{order.id}")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ACCOUNT_ACCESS_DENIED"


def test_deposit_withdraw_and_overview():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")
    client = TestClient(app)

    dep = client.post(f"/trading/accounts/{account.id}/deposit", json={"amount": 1000})
    assert dep.status_code == 200

    wdr = client.post(f"/trading/accounts/{account.id}/withdraw", json={"amount": 200})
    assert wdr.status_code == 200

    overview = client.get(f"/trading/accounts/{account.id}/overview")
    assert overview.status_code == 200
    assert overview.json()["data"]["cashBalance"] == 800
