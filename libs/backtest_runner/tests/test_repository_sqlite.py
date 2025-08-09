"""backtest_runner SQLite 仓储测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from backtest_runner.repository_sqlite import SQLiteBacktestRepository
from backtest_runner.service import BacktestIdempotencyConflictError, BacktestService


def _sqlite_repo(db_path: Path) -> SQLiteBacktestRepository:
    return SQLiteBacktestRepository(db_path=str(db_path))


def test_sqlite_repository_persists_task_and_idempotency_across_restart(tmp_path):
    db_path = tmp_path / "backtest_runner.sqlite3"

    repo1 = _sqlite_repo(db_path)
    service1 = BacktestService(repository=repo1)

    task = service1.create_task(
        user_id="u-1",
        strategy_id="s-1",
        config={"benchmark": "SPY"},
        idempotency_key="k-1",
    )
    service1.transition(user_id="u-1", task_id=task.id, to_status="running")
    service1.transition(
        user_id="u-1",
        task_id=task.id,
        to_status="completed",
        metrics={"returnRate": 0.12},
    )

    repo2 = _sqlite_repo(db_path)
    service2 = BacktestService(repository=repo2)

    persisted = service2.get_task(user_id="u-1", task_id=task.id)
    assert persisted is not None
    assert persisted.status == "completed"
    assert persisted.metrics == {"returnRate": 0.12}

    with pytest.raises(BacktestIdempotencyConflictError):
        service2.create_task(
            user_id="u-1",
            strategy_id="s-1",
            config={"benchmark": "SPY"},
            idempotency_key="k-1",
        )
