"""backtest_runner 领域测试。"""

from __future__ import annotations

import pytest


def test_create_backtest_task_with_pending_status():
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestService

    repo = InMemoryBacktestRepository()
    service = BacktestService(repository=repo)

    task = service.create_task(
        user_id="u-1",
        strategy_id="s-1",
        config={"symbol": "AAPL"},
    )

    assert task.status == "pending"


def test_backtest_task_state_machine_happy_path():
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestService

    repo = InMemoryBacktestRepository()
    service = BacktestService(repository=repo)

    task = service.create_task(user_id="u-1", strategy_id="s-1", config={})

    running = service.transition(user_id="u-1", task_id=task.id, to_status="running")
    assert running is not None
    assert running.status == "running"

    completed = service.transition(user_id="u-1", task_id=task.id, to_status="completed")
    assert completed is not None
    assert completed.status == "completed"


def test_invalid_transition_raises_error():
    from backtest_runner.domain import InvalidBacktestTransitionError
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestService

    repo = InMemoryBacktestRepository()
    service = BacktestService(repository=repo)

    task = service.create_task(user_id="u-1", strategy_id="s-1", config={})

    with pytest.raises(InvalidBacktestTransitionError):
        service.transition(user_id="u-1", task_id=task.id, to_status="completed")


def test_get_task_returns_none_for_non_owner():
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestService

    repo = InMemoryBacktestRepository()
    service = BacktestService(repository=repo)

    task = service.create_task(user_id="u-1", strategy_id="s-1", config={})

    assert service.get_task(user_id="u-2", task_id=task.id) is None
