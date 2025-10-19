"""strategy_management 领域测试。"""

from __future__ import annotations

import pytest


def test_create_and_list_strategies_are_user_scoped():
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda user_id, strategy_id: 0)

    created = service.create_strategy(
        user_id="u-1",
        name="mean-reversion-1",
        template="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    mine = service.list_strategies(user_id="u-1")
    others = service.list_strategies(user_id="u-2")

    assert len(mine) == 1
    assert mine[0].id == created.id
    assert others == []


def test_get_strategy_returns_none_for_non_owner():
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda user_id, strategy_id: 0)

    created = service.create_strategy(
        user_id="u-1",
        name="mean-reversion-1",
        template="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    assert service.get_strategy(user_id="u-2", strategy_id=created.id) is None


def test_delete_strategy_blocked_when_backtest_in_use():
    from strategy_management.domain import StrategyInUseError
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda user_id, strategy_id: 2)

    created = service.create_strategy(
        user_id="u-1",
        name="mean-reversion-1",
        template="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    with pytest.raises(StrategyInUseError):
        service.delete_strategy(user_id="u-1", strategy_id=created.id)


def test_delete_strategy_success_when_no_active_backtests():
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda user_id, strategy_id: 0)

    created = service.create_strategy(
        user_id="u-1",
        name="mean-reversion-1",
        template="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    service.delete_strategy(user_id="u-1", strategy_id=created.id)
    assert service.get_strategy(user_id="u-1", strategy_id=created.id) is None
