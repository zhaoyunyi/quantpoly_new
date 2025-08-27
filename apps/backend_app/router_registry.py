"""统一路由注册。"""

from __future__ import annotations

import logging
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backtest_runner.api import create_router as create_backtest_router
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.repository_sqlite import SQLiteBacktestRepository
from backtest_runner.service import BacktestService
from job_orchestration.api import create_router as create_job_router
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.repository_sqlite import SQLiteJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import JobOrchestrationService
from market_data.api import create_router as create_market_router
from market_data.domain import MarketAsset, MarketCandle, MarketQuote
from market_data.service import MarketDataService
from monitoring_realtime.app import create_app as create_monitoring_app
from platform_core.logging import mask_sensitive
from platform_core.response import error_response
from risk_control.api import create_router as create_risk_router
from risk_control.repository import InMemoryRiskRepository
from risk_control.service import RiskControlService
from signal_execution.api import create_router as create_signal_router
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService
from strategy_management.api import create_router as create_strategy_router
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.repository_sqlite import SQLiteStrategyRepository
from strategy_management.service import StrategyService
from trading_account.api import create_router as create_trading_router
from trading_account.domain import TradingAccount
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.repository_sqlite import SQLiteTradingAccountRepository
from trading_account.service import TradingAccountService
from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.repository_sqlite import SQLiteUserRepository
from user_auth.session import SessionStore
from user_auth.session_sqlite import SQLiteSessionStore
from user_auth.token import extract_session_token
from user_preferences.api import create_router as create_preferences_router
from user_preferences.store import InMemoryPreferencesStore


AuthUserFn = Callable[[Request], User]


class _InMemoryMarketProvider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        normalized = symbol.upper()
        return MarketQuote(symbol=normalized, name=normalized, price=0.0)

    def history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ):
        del symbol, start_date, end_date, timeframe, limit
        return []

    def list_assets(self, *, limit: int):
        del limit
        return []

    def batch_quote(self, *, symbols: list[str]):
        return {symbol.upper(): MarketQuote(symbol=symbol.upper(), name=symbol.upper(), price=0.0) for symbol in symbols}

    def health(self):
        return {
            "provider": "in-memory",
            "healthy": True,
            "status": "ok",
            "message": "",
        }


@dataclass
class CompositionContext:
    user_repo: UserRepository
    session_store: SessionStore
    strategy_repo: InMemoryStrategyRepository
    backtest_repo: InMemoryBacktestRepository
    trading_repo: InMemoryTradingAccountRepository
    job_repo: InMemoryJobRepository
    risk_repo: InMemoryRiskRepository
    signal_repo: InMemorySignalRepository
    preferences_store: InMemoryPreferencesStore
    market_service: MarketDataService


class MetricsCollector:
    def __init__(self) -> None:
        self._http_requests_total = 0
        self._http_errors_total = 0

    def record(self, *, status_code: int) -> None:
        self._http_requests_total += 1
        if status_code >= 400:
            self._http_errors_total += 1

    def snapshot(self) -> dict[str, Any]:
        error_rate = 0.0
        if self._http_requests_total > 0:
            error_rate = round(self._http_errors_total / self._http_requests_total, 6)

        return {
            "httpRequestsTotal": self._http_requests_total,
            "httpErrorsTotal": self._http_errors_total,
            "httpErrorRate": error_rate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def build_context(
    *,
    storage_backend: str = "sqlite",
    sqlite_db_path: str | None = None,
) -> CompositionContext:
    normalized_backend = storage_backend.strip().lower()
    if normalized_backend not in {"sqlite", "memory"}:
        raise ValueError("storage_backend must be one of: sqlite, memory")

    if normalized_backend == "sqlite":
        if not sqlite_db_path:
            sqlite_db_path = "data/backend.sqlite3"
        if sqlite_db_path != ":memory:":
            db_path = Path(sqlite_db_path)
            if db_path.parent != Path("."):
                db_path.parent.mkdir(parents=True, exist_ok=True)
        user_repo = SQLiteUserRepository(db_path=sqlite_db_path)
        session_store = SQLiteSessionStore(db_path=sqlite_db_path)
        strategy_repo = SQLiteStrategyRepository(db_path=sqlite_db_path)
        backtest_repo = SQLiteBacktestRepository(db_path=sqlite_db_path)
        trading_repo = SQLiteTradingAccountRepository(db_path=sqlite_db_path)
        job_repo = SQLiteJobRepository(db_path=sqlite_db_path)
    else:
        user_repo = UserRepository()
        session_store = SessionStore()
        strategy_repo = InMemoryStrategyRepository()
        backtest_repo = InMemoryBacktestRepository()
        trading_repo = InMemoryTradingAccountRepository()
        job_repo = InMemoryJobRepository()

    risk_repo = InMemoryRiskRepository()
    signal_repo = InMemorySignalRepository()
    preferences_store = InMemoryPreferencesStore()

    market_service = MarketDataService(provider=_InMemoryMarketProvider())

    return CompositionContext(
        user_repo=user_repo,
        session_store=session_store,
        strategy_repo=strategy_repo,
        backtest_repo=backtest_repo,
        trading_repo=trading_repo,
        job_repo=job_repo,
        risk_repo=risk_repo,
        signal_repo=signal_repo,
        preferences_store=preferences_store,
        market_service=market_service,
    )


def build_current_user_dependency(*, context: CompositionContext) -> AuthUserFn:
    auth_logger = logging.getLogger("backend_app.auth")

    def get_current_user(request: Request) -> User:
        token = extract_session_token(headers=request.headers, cookies=request.cookies)

        if not token:
            auth_logger.warning(
                "auth_failed reason=missing_token context=%s",
                mask_sensitive(
                    str(
                        {
                            "headers": dict(request.headers),
                            "cookies": dict(request.cookies),
                            "query": str(request.query_params),
                        }
                    )
                ),
            )
            raise PermissionError("UNAUTHORIZED")

        session = context.session_store.get_by_token(token)
        if session is None:
            auth_logger.warning(
                "auth_failed reason=invalid_token context=%s",
                mask_sensitive(
                    str(
                        {
                            "headers": dict(request.headers),
                            "cookies": dict(request.cookies),
                            "query": str(request.query_params),
                        }
                    )
                ),
            )
            raise PermissionError("UNAUTHORIZED")

        user = context.user_repo.get_by_id(session.user_id)
        if user is None:
            auth_logger.warning(
                "auth_failed reason=user_not_found context=%s",
                mask_sensitive(
                    str(
                        {
                            "headers": dict(request.headers),
                            "cookies": dict(request.cookies),
                            "query": str(request.query_params),
                        }
                    )
                ),
            )
            raise PermissionError("UNAUTHORIZED")

        return user

    return get_current_user


def register_all_routes(
    *,
    app: FastAPI,
    context: CompositionContext,
    enabled_contexts: set[str],
    get_current_user: AuthUserFn,
) -> None:
    job_service = JobOrchestrationService(
        repository=context.job_repo,
        scheduler=InMemoryScheduler(),
    )
    backtest_service = BacktestService(
        repository=context.backtest_repo,
        strategy_owner_acl=lambda user_id, strategy_id: context.strategy_repo.get_by_id(
            strategy_id,
            user_id=user_id,
        )
        is not None,
    )
    strategy_service = StrategyService(
        repository=context.strategy_repo,
        count_active_backtests=lambda user_id, strategy_id: backtest_service.count_active_backtests(
            user_id=user_id,
            strategy_id=strategy_id,
        ),
        create_backtest_for_strategy=lambda user_id, strategy_id, config, idempotency_key: backtest_service.create_task(
            user_id=user_id,
            strategy_id=strategy_id,
            config=config,
            idempotency_key=idempotency_key,
        ),
        list_backtests_for_strategy=lambda user_id, strategy_id, status, page, page_size: backtest_service.list_tasks(
            user_id=user_id,
            strategy_id=strategy_id,
            status=status,
            page=page,
            page_size=page_size,
        ),
        stats_backtests_for_strategy=lambda user_id, strategy_id: backtest_service.statistics(
            user_id=user_id,
            strategy_id=strategy_id,
        ),
    )
    risk_service = RiskControlService(
        repository=context.risk_repo,
        account_owner_acl=lambda user_id, account_id: context.trading_repo.get_account(
            account_id=account_id,
            user_id=user_id,
        )
        is not None,
    )
    trading_service = TradingAccountService(
        repository=context.trading_repo,
        risk_snapshot_reader=lambda user_id, account_id: risk_service.get_account_assessment_snapshot(
            user_id=user_id,
            account_id=account_id,
        ),
        risk_evaluator=lambda user_id, account_id: risk_service.evaluate_account_risk(
            user_id=user_id,
            account_id=account_id,
        ),
    )
    signal_service = SignalExecutionService(
        repository=context.signal_repo,
        strategy_owner_acl=lambda user_id, strategy_id: context.strategy_repo.get_by_id(
            strategy_id,
            user_id=user_id,
        )
        is not None,
        account_owner_acl=lambda user_id, account_id: context.trading_repo.get_account(
            account_id=account_id,
            user_id=user_id,
        )
        is not None,
        strategy_parameter_validator=lambda user_id, strategy_id, parameters: strategy_service.validate_execution_parameters(
            user_id=user_id,
            strategy_id=strategy_id,
            parameters=parameters,
        ),
    )

    if "user-preferences" in enabled_contexts:
        app.include_router(
            create_preferences_router(
                store=context.preferences_store,
                get_current_user=get_current_user,
            )
        )

    if "strategy-management" in enabled_contexts:
        app.include_router(
            create_strategy_router(
                service=strategy_service,
                get_current_user=get_current_user,
                job_service=job_service,
                signal_service=signal_service,
            )
        )

    if "job-orchestration" in enabled_contexts:
        app.include_router(create_job_router(service=job_service, get_current_user=get_current_user))

    if "backtest-runner" in enabled_contexts:
        app.include_router(create_backtest_router(service=backtest_service, get_current_user=get_current_user, job_service=job_service))

    if "trading-account" in enabled_contexts:
        app.include_router(create_trading_router(service=trading_service, get_current_user=get_current_user, job_service=job_service))

    if "market-data" in enabled_contexts:
        app.include_router(create_market_router(service=context.market_service, get_current_user=get_current_user))

    if "risk-control" in enabled_contexts:
        app.include_router(create_risk_router(service=risk_service, get_current_user=get_current_user, job_service=job_service))

    if "signal-execution" in enabled_contexts:
        app.include_router(create_signal_router(service=signal_service, get_current_user=get_current_user, job_service=job_service))

    if "monitoring-realtime" in enabled_contexts:
        monitor_app = create_monitoring_app(
            user_repo=context.user_repo,
            session_store=context.session_store,
            signal_source=lambda user_id: [
                {
                    "id": item.id,
                    "userId": item.user_id,
                    "strategyId": item.strategy_id,
                    "symbol": item.symbol,
                    "status": item.status,
                }
                for item in context.signal_repo.list_signals(user_id=user_id)
            ],
            alert_source=lambda user_id: [
                {
                    "id": item.id,
                    "userId": item.user_id,
                    "accountId": item.account_id,
                    "severity": item.severity,
                    "status": item.status,
                    "message": item.message,
                    "acknowledgedAt": item.acknowledged_at.isoformat() if item.acknowledged_at else None,
                    "acknowledgedBy": item.acknowledged_by,
                    "resolvedAt": item.resolved_at.isoformat() if item.resolved_at else None,
                    "resolvedBy": item.resolved_by,
                    "notificationStatus": item.notification_status,
                    "notifiedAt": item.notified_at.isoformat() if item.notified_at else None,
                    "notifiedBy": item.notified_by,
                }
                for item in context.risk_repo.list_alerts(user_id=user_id)
            ],
            alert_task_source=lambda user_id: [
                {
                    "taskId": job.id,
                    "userId": job.user_id,
                    "taskType": job.task_type,
                    "status": job.status,
                    "result": job.result,
                }
                for job in job_service.list_jobs(user_id=user_id, task_type="risk_alert_notify")
            ],
        )
        for route in monitor_app.router.routes:
            if route.path in {"/monitor/summary", "/ws/monitor"}:
                app.router.routes.append(route)


def ensure_demo_account(*, context: CompositionContext, user_id: str) -> None:
    existing = context.trading_repo.list_accounts(user_id=user_id)
    if existing:
        return

    account = TradingAccount.create(user_id=user_id, account_name="默认模拟账户")
    context.trading_repo.save_account(account)


def permission_error_to_response() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=error_response(code="UNAUTHORIZED", message="unauthorized"),
    )
