"""订单与账本服务测试。"""

from __future__ import annotations

import pytest

from trading_account.domain import CashFlow
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import (
    InsufficientFundsError,
    LedgerTransactionError,
    OrderNotFoundError,
    TradingAccountService,
)


def _setup_service(*, user_id: str = "u-1"):
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    account = service.create_account(user_id=user_id, account_name="primary")
    return repo, service, account


def test_submit_and_fill_order_records_trade_and_cash_flow():
    _, service, account = _setup_service()

    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )
    filled = service.fill_order(user_id="u-1", account_id=account.id, order_id=order.id)

    assert filled.status == "filled"

    trades = service.list_trades(user_id="u-1", account_id=account.id)
    assert len(trades) == 1
    assert trades[0].symbol == "AAPL"

    cash_flows = service.list_cash_flows(user_id="u-1", account_id=account.id)
    assert len(cash_flows) == 1
    assert cash_flows[0].flow_type == "trade_buy"
    assert cash_flows[0].amount == pytest.approx(-1000)


def test_fill_missing_order_raises_not_found():
    _, service, account = _setup_service()

    with pytest.raises(OrderNotFoundError):
        service.fill_order(user_id="u-1", account_id=account.id, order_id="not-exists")


def test_withdraw_requires_sufficient_cash_balance():
    _, service, account = _setup_service()

    service.deposit(user_id="u-1", account_id=account.id, amount=1000)
    service.withdraw(user_id="u-1", account_id=account.id, amount=400)

    with pytest.raises(InsufficientFundsError):
        service.withdraw(user_id="u-1", account_id=account.id, amount=700)


class _FailingCashFlowRepo(InMemoryTradingAccountRepository):
    def save_cash_flow(self, cash_flow: CashFlow) -> None:
        raise RuntimeError("cashflow write failed")


def test_fill_order_rolls_back_when_cash_flow_write_fails():
    repo = _FailingCashFlowRepo()
    service = TradingAccountService(repository=repo)
    account = service.create_account(user_id="u-1", account_name="primary")
    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )

    with pytest.raises(LedgerTransactionError):
        service.fill_order(user_id="u-1", account_id=account.id, order_id=order.id)

    stored = service.get_order(user_id="u-1", account_id=account.id, order_id=order.id)
    assert stored is not None
    assert stored.status == "pending"
    assert service.list_trades(user_id="u-1", account_id=account.id) == []


def test_account_overview_includes_order_trade_and_cash_metrics():
    _, service, account = _setup_service()

    service.deposit(user_id="u-1", account_id=account.id, amount=5000)
    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )
    service.fill_order(user_id="u-1", account_id=account.id, order_id=order.id)

    overview = service.account_overview(user_id="u-1", account_id=account.id)

    assert overview["orderCount"] == 1
    assert overview["filledOrderCount"] == 1
    assert overview["tradeCount"] == 1
    assert overview["turnover"] == pytest.approx(1000)
    assert overview["cashBalance"] == pytest.approx(4000)
