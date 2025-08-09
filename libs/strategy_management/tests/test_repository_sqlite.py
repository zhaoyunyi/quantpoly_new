"""strategy_management SQLite 仓储测试。"""

from __future__ import annotations

from pathlib import Path

from strategy_management.repository_sqlite import SQLiteStrategyRepository
from strategy_management.service import StrategyService


def _sqlite_repo(db_path: Path) -> SQLiteStrategyRepository:
    return SQLiteStrategyRepository(db_path=str(db_path))


def test_sqlite_repository_persists_strategy_state_across_restart(tmp_path):
    db_path = tmp_path / "strategy_management.sqlite3"

    repo1 = _sqlite_repo(db_path)
    service1 = StrategyService(repository=repo1, count_active_backtests=lambda _strategy_id: 0)

    strategy = service1.create_strategy(
        user_id="u-1",
        name="alpha",
        template="mean_reversion",
        parameters={"window": 10},
    )
    service1.activate_strategy(user_id="u-1", strategy_id=strategy.id)

    repo2 = _sqlite_repo(db_path)
    service2 = StrategyService(repository=repo2, count_active_backtests=lambda _strategy_id: 0)

    persisted = service2.get_strategy(user_id="u-1", strategy_id=strategy.id)
    assert persisted is not None
    assert persisted.status == "active"

    deleted = service2.delete_strategy(user_id="u-1", strategy_id=strategy.id)
    assert deleted is True
