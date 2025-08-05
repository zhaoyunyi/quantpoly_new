"""backtest_runner 与 job_orchestration 适配测试。"""

from __future__ import annotations

import pytest

from backtest_runner.orchestration import JobOrchestrationBacktestDispatcher
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.service import BacktestIdempotencyConflictError, BacktestService
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import JobOrchestrationService


def _build_job_service() -> JobOrchestrationService:
    return JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )


def test_create_task_dispatches_backtest_job_to_orchestration():
    job_service = _build_job_service()
    dispatcher = JobOrchestrationBacktestDispatcher(job_service=job_service)
    service = BacktestService(repository=InMemoryBacktestRepository(), dispatcher=dispatcher)

    task = service.create_task(
        user_id="u-1",
        strategy_id="s-1",
        config={"symbol": "AAPL"},
        idempotency_key="b-1",
    )

    jobs = job_service.list_jobs(user_id="u-1")
    assert len(jobs) == 1
    assert jobs[0].task_type == "backtest_run"
    assert jobs[0].payload["backtestTaskId"] == task.id


def test_dispatch_conflict_rolls_back_local_backtest_task():
    class _ConflictDispatcher:
        def submit_backtest(self, task):
            del task
            raise BacktestIdempotencyConflictError("idempotency key already exists")

    service = BacktestService(
        repository=InMemoryBacktestRepository(),
        dispatcher=_ConflictDispatcher(),
    )

    with pytest.raises(BacktestIdempotencyConflictError):
        service.create_task(
            user_id="u-1",
            strategy_id="s-1",
            config={},
            idempotency_key="dup-key",
        )

    listing = service.list_tasks(user_id="u-1")
    assert listing["total"] == 0
