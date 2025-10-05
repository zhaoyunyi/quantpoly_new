"""交易分析与运维能力 API 测试。"""

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
    from trading_account.api import create_router
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    class _User:
        def __init__(
            self,
            user_id: str,
            admin: bool | None,
            user_role: str | None,
            user_level: int | None,
        ):
            self.id = user_id
            if admin is not None:
                self.is_admin = admin
            if user_role is not None:
                self.role = user_role
            if user_level is not None:
                self.level = user_level

    def _get_current_user():
        return _User(current_user_id, is_admin, role, level)

    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_account_analytics_endpoints_return_data_for_owner():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="primary")
    service.deposit(user_id="u-1", account_id=account.id, amount=2000)
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )

    client = TestClient(app)

    risk = client.get(f"/trading/accounts/{account.id}/risk-metrics")
    assert risk.status_code == 200
    assert risk.json()["data"]["accountId"] == account.id

    curve = client.get(f"/trading/accounts/{account.id}/equity-curve")
    assert curve.status_code == 200
    assert len(curve.json()["data"]) >= 1

    analysis = client.get(f"/trading/accounts/{account.id}/position-analysis")
    assert analysis.status_code == 200
    assert len(analysis.json()["data"]) == 1


def test_aggregate_endpoint_is_user_scoped():
    app, service = _build_app(current_user_id="u-1")
    service.create_account(user_id="u-1", account_name="a1")
    service.create_account(user_id="u-2", account_name="a2")

    client = TestClient(app)
    aggregate = client.get("/trading/accounts/aggregate")

    assert aggregate.status_code == 200
    payload = aggregate.json()
    assert payload["success"] is True
    assert payload["data"]["accountCount"] == 1


def test_pending_orders_and_refresh_prices_require_admin():
    app, service = _build_app(current_user_id="u-1", is_admin=False)
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

    pending = client.get("/trading/ops/pending-orders")
    assert pending.status_code == 403
    assert pending.json()["error"]["code"] == "ADMIN_REQUIRED"

    refresh = client.post(
        "/trading/ops/refresh-prices",
        json={"priceUpdates": {"AAPL": 130}},
    )
    assert refresh.status_code == 403
    assert refresh.json()["error"]["code"] == "ADMIN_REQUIRED"


def test_refresh_prices_idempotency_conflict_returns_409_for_admin():
    app, service = _build_app(current_user_id="admin-1", is_admin=None, role="admin")
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.upsert_position(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )

    client = TestClient(app)

    first = client.post(
        "/trading/ops/refresh-prices",
        json={"priceUpdates": {"AAPL": 130}, "idempotencyKey": "refresh-1"},
    )
    assert first.status_code == 200
    assert first.json()["data"]["idempotent"] is False

    conflict = client.post(
        "/trading/ops/refresh-prices",
        json={"priceUpdates": {"AAPL": 131}, "idempotencyKey": "refresh-1"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_ops_endpoints_accept_role_admin_without_is_admin_flag():
    app, service = _build_app(current_user_id="admin-1", is_admin=None, role="admin")
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="MSFT",
        side="BUY",
        quantity=1,
        price=100,
    )

    client = TestClient(app)

    pending = client.get("/trading/ops/pending-orders")
    assert pending.status_code == 200
    assert pending.json()["success"] is True

    refresh = client.post(
        "/trading/ops/refresh-prices",
        json={"priceUpdates": {"MSFT": 130}},
    )
    assert refresh.status_code == 200
    assert refresh.json()["success"] is True


def test_ops_endpoints_reject_legacy_is_admin_flag_without_role():
    app, service = _build_app(current_user_id="admin-legacy", is_admin=True, role=None)
    account = service.create_account(user_id="admin-legacy", account_name="primary")
    service.submit_order(
        user_id="admin-legacy",
        account_id=account.id,
        symbol="NVDA",
        side="BUY",
        quantity=1,
        price=100,
    )

    client = TestClient(app)

    pending = client.get("/trading/ops/pending-orders")
    assert pending.status_code == 403
    assert pending.json()["error"]["code"] == "ADMIN_REQUIRED"


def test_ops_endpoints_reject_role_user_without_is_admin_flag():
    app, service = _build_app(current_user_id="u-1", is_admin=None, role="user")
    account = service.create_account(user_id="u-1", account_name="primary")
    service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AMD",
        side="BUY",
        quantity=1,
        price=100,
    )

    client = TestClient(app)

    pending = client.get("/trading/ops/pending-orders")
    assert pending.status_code == 403
    assert pending.json()["error"]["code"] == "ADMIN_REQUIRED"

    refresh = client.post(
        "/trading/ops/refresh-prices",
        json={"priceUpdates": {"AMD": 120}},
    )
    assert refresh.status_code == 403
    assert refresh.json()["error"]["code"] == "ADMIN_REQUIRED"
