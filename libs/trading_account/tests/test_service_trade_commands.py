"""交易命令（buy/sell）服务测试。"""

from __future__ import annotations

import pytest

from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import (
    InsufficientFundsError,
    InsufficientPositionError,
    TradingAccountService,
)


def _setup_service(*, user_id: str = "u-1"):
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    account = service.create_account(user_id=user_id, account_name="primary")
    return service, account


def test_buy_command_should_create_order_trade_cashflow_and_position():
    service, account = _setup_service()
    service.deposit(user_id="u-1", account_id=account.id, amount=2000)

    result = service.execute_buy_command(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        price=100,
    )

    assert result["order"].status == "filled"
    assert result["trade"].side == "BUY"
    assert result["cashFlow"].flow_type == "trade_buy"
    assert result["cashFlow"].amount == pytest.approx(-1000)
    assert result["position"].symbol == "AAPL"
    assert result["position"].quantity == pytest.approx(10)
    assert service.cash_balance(user_id="u-1", account_id=account.id) == pytest.approx(1000)


def test_sell_command_should_reduce_position_and_increase_cash():
    service, account = _setup_service()
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="MSFT",
        quantity=10,
        avg_price=100,
        last_price=100,
    )

    result = service.execute_sell_command(
        user_id="u-1",
        account_id=account.id,
        symbol="MSFT",
        quantity=4,
        price=120,
    )

    assert result["order"].status == "filled"
    assert result["trade"].side == "SELL"
    assert result["cashFlow"].flow_type == "trade_sell"
    assert result["cashFlow"].amount == pytest.approx(480)
    assert result["position"].quantity == pytest.approx(6)
    assert service.cash_balance(user_id="u-1", account_id=account.id) == pytest.approx(480)


def test_buy_command_should_fail_when_insufficient_funds():
    service, account = _setup_service()

    with pytest.raises(InsufficientFundsError):
        service.execute_buy_command(
            user_id="u-1",
            account_id=account.id,
            symbol="AAPL",
            quantity=10,
            price=100,
        )

    assert service.list_orders(user_id="u-1", account_id=account.id) == []
    assert service.list_trades(user_id="u-1", account_id=account.id) == []


def test_sell_command_should_fail_when_insufficient_position():
    service, account = _setup_service()

    with pytest.raises(InsufficientPositionError):
        service.execute_sell_command(
            user_id="u-1",
            account_id=account.id,
            symbol="TSLA",
            quantity=1,
            price=200,
        )

    assert service.list_orders(user_id="u-1", account_id=account.id) == []
    assert service.list_trades(user_id="u-1", account_id=account.id) == []
