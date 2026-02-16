"""composition root 存储模式测试。"""

from __future__ import annotations

import pytest

from apps.backend_app.router_registry import build_context
from apps.backend_app.settings import CompositionSettings, normalize_job_executor_mode
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.repository_postgres import PostgresBacktestRepository
from backtest_runner.result_store import InMemoryBacktestResultStore
from backtest_runner.result_store_postgres import PostgresBacktestResultStore
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.repository_postgres import PostgresJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from risk_control.repository import InMemoryRiskRepository
from risk_control.repository_postgres import PostgresRiskRepository
from signal_execution.repository import InMemorySignalRepository
from signal_execution.repository_postgres import PostgresSignalRepository
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.repository_postgres import PostgresStrategyRepository
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.repository_postgres import PostgresTradingAccountRepository
from user_auth.repository_postgres import PostgresUserRepository
from user_auth.session_postgres import PostgresSessionStore
from user_preferences.store import InMemoryPreferencesStore, PostgresPreferencesStore


class _FakeConn:
    def exec_driver_sql(self, _sql, _params=None):
        class _R:
            rowcount = 1

            @staticmethod
            def fetchone():
                return None

            @staticmethod
            def fetchall():
                return []

        return _R()


class _FakeBegin:
    def __enter__(self):
        return _FakeConn()

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeEngine:
    def begin(self):
        return _FakeBegin()


def test_build_context_uses_postgres_repositories_for_production_mode(monkeypatch):
    fake_engine = _FakeEngine()
    monkeypatch.setattr("apps.backend_app.router_registry._build_postgres_engine", lambda dsn: fake_engine)

    context = build_context(
        storage_backend="postgres",
        postgres_dsn="postgresql+psycopg://quantpoly:quantpoly@localhost:54329/quantpoly_test",
    )

    assert isinstance(context.user_repo, PostgresUserRepository)
    assert isinstance(context.session_store, PostgresSessionStore)
    assert isinstance(context.strategy_repo, PostgresStrategyRepository)
    assert isinstance(context.backtest_repo, PostgresBacktestRepository)
    assert isinstance(context.trading_repo, PostgresTradingAccountRepository)
    assert isinstance(context.job_repo, PostgresJobRepository)
    assert isinstance(context.job_scheduler, InMemoryScheduler)
    assert isinstance(context.backtest_result_store, PostgresBacktestResultStore)
    assert isinstance(context.risk_repo, PostgresRiskRepository)
    assert isinstance(context.signal_repo, PostgresSignalRepository)
    assert isinstance(context.preferences_store, PostgresPreferencesStore)


def test_build_context_rejects_postgres_mode_without_dsn():
    with pytest.raises(ValueError, match="postgres_dsn"):
        build_context(storage_backend="postgres", postgres_dsn=None)


def test_build_context_uses_inmemory_repositories_for_test_mode():
    context = build_context(storage_backend="memory")

    assert context.user_repo.__class__.__name__ == "UserRepository"
    assert context.session_store.__class__.__name__ == "SessionStore"
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


def test_normalize_job_executor_mode_supports_inprocess_and_celery_adapter():
    assert normalize_job_executor_mode("inprocess") == "inprocess"
    assert normalize_job_executor_mode("celery-adapter") == "celery-adapter"


def test_composition_settings_reads_job_executor_mode_from_env(monkeypatch):
    monkeypatch.setenv("BACKEND_JOB_EXECUTOR_MODE", "celery-adapter")

    settings = CompositionSettings.from_env()

    assert settings.job_executor_mode == "celery-adapter"
