"""backtest_runner 库。"""

from backtest_runner.domain import BacktestTask, InvalidBacktestTransitionError
from backtest_runner.orchestration import JobOrchestrationBacktestDispatcher
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.result_store import InMemoryBacktestResultStore
from backtest_runner.result_store_sqlite import SQLiteBacktestResultStore
from backtest_runner.repository_sqlite import SQLiteBacktestRepository
from backtest_runner.service import (
    BacktestAccessDeniedError,
    BacktestDeleteInvalidStateError,
    BacktestDispatchError,
    BacktestExecutionError,
    BacktestIdempotencyConflictError,
    BacktestService,
)

__all__ = [
    "BacktestTask",
    "InvalidBacktestTransitionError",
    "InMemoryBacktestRepository",
    "SQLiteBacktestRepository",
    "InMemoryBacktestResultStore",
    "SQLiteBacktestResultStore",
    "BacktestIdempotencyConflictError",
    "BacktestAccessDeniedError",
    "BacktestDeleteInvalidStateError",
    "BacktestDispatchError",
    "BacktestExecutionError",
    "JobOrchestrationBacktestDispatcher",
    "BacktestService",
]
