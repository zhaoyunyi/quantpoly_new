"""trading_account UoW 契约测试。"""

from __future__ import annotations

import pytest

from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import LedgerTransactionError, TradingAccountService


class _FailingRepository(InMemoryTradingAccountRepository):
    def __init__(self) -> None:
        super().__init__()
        self.fail_on_cash_flow = False

    def save_cash_flow(self, cash_flow):  # noqa: ANN001
        if self.fail_on_cash_flow:
            raise RuntimeError("boom")
        return super().save_cash_flow(cash_flow)


def test_fill_order_rolls_back_by_uow_when_ledger_write_fails():
    repository = _FailingRepository()
    service = TradingAccountService(repository=repository)

    account = service.create_account(user_id="u-1", account_name="main")
    service.deposit(user_id="u-1", account_id=account.id, amount=10000)
    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )
    repository.fail_on_cash_flow = True

    with pytest.raises(LedgerTransactionError):
        service.fill_order(user_id="u-1", account_id=account.id, order_id=order.id)

    rolled_back_order = service.get_order(user_id="u-1", account_id=account.id, order_id=order.id)
    assert rolled_back_order is not None
    assert rolled_back_order.status == "pending"

    trades = service.list_trades(user_id="u-1", account_id=account.id)
    assert trades == []

    flows = service.list_cash_flows(user_id="u-1", account_id=account.id)
    assert len(flows) == 1
    assert flows[0].flow_type == "deposit"
