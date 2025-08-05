"""signal_execution 筛选与搜索测试。"""

from __future__ import annotations


def test_list_signals_filters_and_user_scope():
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-growth",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    s2 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-value",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=s2.id)

    service.create_signal(
        user_id="u-2",
        strategy_id="u-2-growth",
        account_id="u-2-account",
        symbol="AAPL",
        side="BUY",
    )

    by_strategy = service.list_signals(user_id="u-1", strategy_id="u-1-growth")
    assert [item.id for item in by_strategy] == [s1.id]

    by_symbol = service.list_signals(user_id="u-1", symbol="MSFT")
    assert [item.id for item in by_symbol] == [s2.id]

    by_status = service.list_signals(user_id="u-1", status="executed")
    assert [item.id for item in by_status] == [s2.id]

    by_keyword = service.list_signals(user_id="u-1", keyword="value")
    assert [item.id for item in by_keyword] == [s2.id]
