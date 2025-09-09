"""订单改撤与快捷查询 API 合同测试。"""

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


def test_api_should_support_order_patch_delete_and_pending_query():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")
    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )

    client = TestClient(app)

    updated = client.patch(
        f"/trading/accounts/{account.id}/orders/{order.id}",
        json={"quantity": 2, "price": 120},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["quantity"] == 2
    assert updated.json()["data"]["price"] == 120

    pending = client.get(f"/trading/accounts/{account.id}/trades/pending")
    assert pending.status_code == 200
    assert [item["id"] for item in pending.json()["data"]] == [order.id]

    deleted = client.delete(f"/trading/accounts/{account.id}/orders/{order.id}")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["status"] == "cancelled"

    pending_after = client.get(f"/trading/accounts/{account.id}/trades/pending")
    assert pending_after.status_code == 200
    assert pending_after.json()["data"] == []


def test_api_should_support_symbol_position_query_and_enforce_order_editable_state():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="TSLA",
        quantity=3,
        avg_price=200,
        last_price=210,
    )
    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="TSLA",
        side="BUY",
        quantity=1,
        price=210,
    )
    service.fill_order(user_id="u-1", account_id=account.id, order_id=order.id)

    client = TestClient(app)

    position = client.get(f"/trading/accounts/{account.id}/positions/TSLA")
    assert position.status_code == 200
    assert position.json()["data"]["symbol"] == "TSLA"

    denied = client.patch(
        f"/trading/accounts/{account.id}/orders/{order.id}",
        json={"quantity": 2},
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "ORDER_INVALID_TRANSITION"
