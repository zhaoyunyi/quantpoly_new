"""trading_account 领域测试。"""

from __future__ import annotations

import pytest


def test_account_list_is_user_scoped():
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)

    a1 = service.create_account(user_id="u-1", account_name="primary")
    service.create_account(user_id="u-2", account_name="other")

    mine = service.list_accounts(user_id="u-1")
    other = service.list_accounts(user_id="u-2")

    assert len(mine) == 1
    assert mine[0].id == a1.id
    assert len(other) == 1
    assert other[0].user_id == "u-2"


def test_position_summary_is_user_scoped():
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)

    account = service.create_account(user_id="u-1", account_name="primary")
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="MSFT",
        quantity=5,
        avg_price=200,
        last_price=190,
    )

    summary = service.position_summary(user_id="u-1", account_id=account.id)
    assert summary["positionCount"] == 2
    assert summary["totalMarketValue"] == pytest.approx(10 * 110 + 5 * 190)

    with pytest.raises(PermissionError):
        service.position_summary(user_id="u-2", account_id=account.id)


def test_trade_stats_is_user_scoped():
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)

    account = service.create_account(user_id="u-1", account_name="primary")
    service.record_trade(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )
    service.record_trade(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="SELL",
        quantity=4,
        price=120,
    )

    stats = service.trade_stats(user_id="u-1", account_id=account.id)
    assert stats["tradeCount"] == 2
    assert stats["turnover"] == pytest.approx(10 * 100 + 4 * 120)

    with pytest.raises(PermissionError):
        service.trade_stats(user_id="u-2", account_id=account.id)


def test_service_public_methods_require_explicit_user_id():
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)

    with pytest.raises(TypeError):
        service.list_accounts()  # type: ignore[misc]
