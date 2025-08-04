"""trading_account 并发冲突语义测试。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading

from trading_account.domain import InvalidTradeOrderTransitionError
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import TradingAccountService


class _RaceFillRepository(InMemoryTradingAccountRepository):
    def __init__(self) -> None:
        super().__init__()
        self._barrier = threading.Barrier(2)

    def transition_order_status(self, *, account_id: str, user_id: str, order_id: str, from_status: str, to_status: str):
        self._barrier.wait(timeout=1)
        return super().transition_order_status(
            account_id=account_id,
            user_id=user_id,
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
        )


def test_concurrent_fill_same_order_only_one_success():
    service = TradingAccountService(repository=_RaceFillRepository())
    account = service.create_account(user_id="u-1", account_name="primary")
    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )

    def _fill_one() -> str:
        try:
            service.fill_order(user_id="u-1", account_id=account.id, order_id=order.id)
            return "ok"
        except InvalidTradeOrderTransitionError:
            return "invalid_transition"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_fill_one) for _ in range(2)]
        results = [future.result() for future in futures]

    assert results.count("ok") == 1
    assert results.count("invalid_transition") == 1

    trades = service.list_trades(user_id="u-1", account_id=account.id)
    flows = service.list_cash_flows(user_id="u-1", account_id=account.id)
    final_order = service.get_order(user_id="u-1", account_id=account.id, order_id=order.id)

    assert len(trades) == 1
    assert len(flows) == 1
    assert final_order is not None
    assert final_order.status == "filled"
