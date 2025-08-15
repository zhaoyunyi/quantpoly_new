"""交易分析与运维能力服务测试。"""

from __future__ import annotations

import pytest

from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import (
    AccountAccessDeniedError,
    PriceRefreshConflictError,
    TradingAccountService,
    TradingAdminRequiredError,
)


def _build_service() -> TradingAccountService:
    repo = InMemoryTradingAccountRepository()
    return TradingAccountService(repository=repo)


def test_account_risk_metrics_equity_curve_and_position_analysis_are_user_scoped():
    service = _build_service()
    account = service.create_account(user_id="u-1", account_name="primary")

    service.deposit(user_id="u-1", account_id=account.id, amount=5000)
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=120,
    )

    metrics = service.account_risk_metrics(user_id="u-1", account_id=account.id)
    assert metrics["accountId"] == account.id
    assert "riskScore" in metrics
    assert "riskLevel" in metrics

    curve = service.account_equity_curve(user_id="u-1", account_id=account.id)
    assert len(curve) >= 1
    assert curve[0]["timestamp"] <= curve[-1]["timestamp"]

    analysis = service.account_position_analysis(user_id="u-1", account_id=account.id)
    assert len(analysis) == 1
    assert analysis[0]["symbol"] == "AAPL"
    assert "weight" in analysis[0]

    with pytest.raises(AccountAccessDeniedError):
        service.account_risk_metrics(user_id="u-2", account_id=account.id)


def test_user_account_aggregate_stats_are_user_scoped():
    service = _build_service()

    a1 = service.create_account(user_id="u-1", account_name="a1")
    a2 = service.create_account(user_id="u-1", account_name="a2")
    service.create_account(user_id="u-2", account_name="other")

    service.deposit(user_id="u-1", account_id=a1.id, amount=2000)
    service.deposit(user_id="u-1", account_id=a2.id, amount=3000)
    service.upsert_position(
        user_id="u-1",
        account_id=a2.id,
        symbol="MSFT",
        quantity=5,
        avg_price=200,
        last_price=210,
    )

    aggregate = service.user_account_aggregate(user_id="u-1")

    assert aggregate["accountCount"] == 2
    assert aggregate["totalCashBalance"] == pytest.approx(5000)
    assert aggregate["totalMarketValue"] == pytest.approx(1050)
    assert aggregate["totalEquity"] == pytest.approx(6050)


def test_pending_orders_and_price_refresh_require_admin_and_support_idempotency():
    service = _build_service()
    account = service.create_account(user_id="u-1", account_name="primary")

    service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )

    with pytest.raises(TradingAdminRequiredError):
        service.list_pending_orders(user_id="u-1", is_admin=False)

    pending = service.list_pending_orders(user_id="admin-1", is_admin=True)
    assert len(pending) == 1
    assert pending[0].status == "pending"

    first = service.refresh_market_prices(
        user_id="admin-1",
        is_admin=True,
        price_updates={"AAPL": 130},
        idempotency_key="refresh-1",
    )
    assert first["updatedPositions"] == 1
    assert first["idempotent"] is False

    second = service.refresh_market_prices(
        user_id="admin-1",
        is_admin=True,
        price_updates={"AAPL": 130},
        idempotency_key="refresh-1",
    )
    assert second["updatedPositions"] == 1
    assert second["idempotent"] is True

    with pytest.raises(PriceRefreshConflictError):
        service.refresh_market_prices(
            user_id="admin-1",
            is_admin=True,
            price_updates={"AAPL": 131},
            idempotency_key="refresh-1",
        )
