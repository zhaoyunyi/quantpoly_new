"""composition root 存储模式测试。"""

from __future__ import annotations

from apps.backend_app.router_registry import build_context
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.repository_sqlite import SQLiteBacktestRepository
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.repository_sqlite import SQLiteJobRepository
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.repository_sqlite import SQLiteStrategyRepository
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.repository_sqlite import SQLiteTradingAccountRepository


def test_build_context_uses_sqlite_repositories_for_production_mode(tmp_path):
    db_path = tmp_path / "backend.sqlite3"

    context = build_context(storage_backend="sqlite", sqlite_db_path=str(db_path))

    assert isinstance(context.strategy_repo, SQLiteStrategyRepository)
    assert isinstance(context.backtest_repo, SQLiteBacktestRepository)
    assert isinstance(context.trading_repo, SQLiteTradingAccountRepository)
    assert isinstance(context.job_repo, SQLiteJobRepository)


def test_build_context_uses_inmemory_repositories_for_test_mode():
    context = build_context(storage_backend="memory")

    assert isinstance(context.strategy_repo, InMemoryStrategyRepository)
    assert isinstance(context.backtest_repo, InMemoryBacktestRepository)
    assert isinstance(context.trading_repo, InMemoryTradingAccountRepository)
    assert isinstance(context.job_repo, InMemoryJobRepository)
