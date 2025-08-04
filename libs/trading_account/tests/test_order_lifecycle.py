"""订单状态机领域测试。"""

from __future__ import annotations

import pytest

from trading_account.domain import InvalidTradeOrderTransitionError, TradeOrder


def test_order_create_defaults_to_pending():
    order = TradeOrder.create(
        user_id="u-1",
        account_id="a-1",
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )

    assert order.status == "pending"


def test_order_mark_filled_from_pending():
    order = TradeOrder.create(
        user_id="u-1",
        account_id="a-1",
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )

    order.mark_filled()

    assert order.status == "filled"


def test_order_rejects_invalid_transition():
    order = TradeOrder.create(
        user_id="u-1",
        account_id="a-1",
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )
    order.mark_cancelled()

    with pytest.raises(InvalidTradeOrderTransitionError):
        order.mark_filled()
