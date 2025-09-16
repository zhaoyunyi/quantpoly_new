"""交易命令（buy/sell）API 测试。"""

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


def test_buy_endpoint_should_return_order_trade_cashflow_position():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")
    service.deposit(user_id="u-1", account_id=account.id, amount=2000)

    client = TestClient(app)
    resp = client.post(
        f"/trading/accounts/{account.id}/buy",
        json={"symbol": "AAPL", "quantity": 10, "price": 100},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["order"]["status"] == "filled"
    assert payload["data"]["trade"]["side"] == "BUY"
    assert payload["data"]["position"]["quantity"] == 10


def test_buy_endpoint_should_return_insufficient_funds_error():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")

    client = TestClient(app)
    resp = client.post(
        f"/trading/accounts/{account.id}/buy",
        json={"symbol": "AAPL", "quantity": 10, "price": 100},
    )

    assert resp.status_code == 409
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INSUFFICIENT_FUNDS"


def test_sell_endpoint_should_return_insufficient_position_error():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")

    client = TestClient(app)
    resp = client.post(
        f"/trading/accounts/{account.id}/sell",
        json={"symbol": "TSLA", "quantity": 1, "price": 200},
    )

    assert resp.status_code == 409
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INSUFFICIENT_POSITION"
