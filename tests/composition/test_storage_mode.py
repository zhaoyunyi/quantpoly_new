"""composition root 存储模式测试。"""

from __future__ import annotations

import pytest

from apps.backend_app.router_registry import build_context
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.repository_sqlite import SQLiteBacktestRepository
from backtest_runner.result_store import InMemoryBacktestResultStore
from backtest_runner.result_store_sqlite import SQLiteBacktestResultStore
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.repository_sqlite import SQLiteJobRepository
from job_orchestration.scheduler import InMemoryScheduler, SQLiteScheduler
from risk_control.repository import InMemoryRiskRepository
from risk_control.repository_sqlite import SQLiteRiskRepository
from signal_execution.repository import InMemorySignalRepository
from signal_execution.repository_sqlite import SQLiteSignalRepository
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.repository_sqlite import SQLiteStrategyRepository
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.repository_sqlite import SQLiteTradingAccountRepository
from user_preferences.store import InMemoryPreferencesStore
from user_preferences.store_sqlite import SQLitePreferencesStore


def test_build_context_uses_sqlite_repositories_for_production_mode(tmp_path):
    db_path = tmp_path / "backend.sqlite3"

    context = build_context(storage_backend="sqlite", sqlite_db_path=str(db_path))

    assert isinstance(context.strategy_repo, SQLiteStrategyRepository)
    assert isinstance(context.backtest_repo, SQLiteBacktestRepository)
    assert isinstance(context.trading_repo, SQLiteTradingAccountRepository)
    assert isinstance(context.job_repo, SQLiteJobRepository)
    assert isinstance(context.job_scheduler, SQLiteScheduler)
    assert isinstance(context.backtest_result_store, SQLiteBacktestResultStore)
    assert isinstance(context.risk_repo, SQLiteRiskRepository)
    assert isinstance(context.signal_repo, SQLiteSignalRepository)
    assert isinstance(context.preferences_store, SQLitePreferencesStore)


def test_build_context_uses_inmemory_repositories_for_test_mode():
    context = build_context(storage_backend="memory")

    assert isinstance(context.strategy_repo, InMemoryStrategyRepository)
    assert isinstance(context.backtest_repo, InMemoryBacktestRepository)
    assert isinstance(context.trading_repo, InMemoryTradingAccountRepository)
    assert isinstance(context.job_repo, InMemoryJobRepository)
    assert isinstance(context.job_scheduler, InMemoryScheduler)
    assert isinstance(context.backtest_result_store, InMemoryBacktestResultStore)
    assert isinstance(context.risk_repo, InMemoryRiskRepository)
    assert isinstance(context.signal_repo, InMemorySignalRepository)
    assert isinstance(context.preferences_store, InMemoryPreferencesStore)


def test_build_context_supports_market_data_alpaca_provider(monkeypatch):
    monkeypatch.setenv("BACKEND_ALPACA_API_KEY", "key")
    monkeypatch.setenv("BACKEND_ALPACA_API_SECRET", "secret")
    monkeypatch.delenv("BACKEND_ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv("BACKEND_ALPACA_TIMEOUT_SECONDS", raising=False)

    context = build_context(storage_backend="memory", market_data_provider="alpaca")

    health = context.market_service.provider_health(user_id="u-1")
    assert health["provider"] == "alpaca"
    assert health["status"] in {"ok", "degraded"}


def test_build_context_alpaca_provider_fail_fast_without_required_config(monkeypatch):
    monkeypatch.delenv("BACKEND_ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("BACKEND_ALPACA_API_SECRET", raising=False)

    with pytest.raises(ValueError, match="ALPACA_CONFIG_MISSING"):
        build_context(storage_backend="memory", market_data_provider="alpaca")


def test_build_context_rejects_unknown_market_data_provider():
    with pytest.raises(ValueError, match="market_data_provider"):
        build_context(storage_backend="memory", market_data_provider="unknown")
