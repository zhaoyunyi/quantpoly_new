"""signal_execution 执行统计测试。"""

from __future__ import annotations


def test_execution_history_trend_and_performance_stats():
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    executed = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-growth",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    cancelled = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-growth",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )

    service.execute_signal(
        user_id="u-1",
        signal_id=executed.id,
        execution_metrics={"pnl": 18.5, "latencyMs": 120},
    )
    service.cancel_signal(user_id="u-1", signal_id=cancelled.id)

    history = service.list_executions(user_id="u-1")
    assert len(history) == 2

    trend = service.execution_trend(user_id="u-1")
    assert trend["total"] == 2
    assert trend["executed"] == 1
    assert trend["cancelled"] == 1

    perf = service.performance_statistics(user_id="u-1")
    assert perf["totalExecutions"] == 1
    assert perf["averagePnl"] == 18.5
    assert perf["averageLatencyMs"] == 120
