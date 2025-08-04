"""trading_account SQLite 仓储测试。"""

from __future__ import annotations

from pathlib import Path

from trading_account.repository_sqlite import SQLiteTradingAccountRepository
from trading_account.service import TradingAccountService


def _sqlite_repo(db_path: Path) -> SQLiteTradingAccountRepository:
    return SQLiteTradingAccountRepository(db_path=str(db_path))


def test_sqlite_repository_persists_order_trade_and_cash_flow(tmp_path):
    db_path = tmp_path / "trading_account.sqlite3"

    repo1 = _sqlite_repo(db_path)
    service1 = TradingAccountService(repository=repo1)

    account = service1.create_account(user_id="u-1", account_name="primary")
    service1.deposit(user_id="u-1", account_id=account.id, amount=5000)
    order = service1.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )
    service1.fill_order(user_id="u-1", account_id=account.id, order_id=order.id)

    repo2 = _sqlite_repo(db_path)
    service2 = TradingAccountService(repository=repo2)

    persisted_order = service2.get_order(user_id="u-1", account_id=account.id, order_id=order.id)
    assert persisted_order is not None
    assert persisted_order.status == "filled"

    trades = service2.list_trades(user_id="u-1", account_id=account.id)
    assert len(trades) == 1
    assert trades[0].order_id == order.id

    flows = service2.list_cash_flows(user_id="u-1", account_id=account.id)
    assert len(flows) == 2
    assert sum(item.amount for item in flows) == 4000
