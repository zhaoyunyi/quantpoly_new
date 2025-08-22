"""job_orchestration 领域测试。"""

from __future__ import annotations

import pytest


def test_submit_job_supports_backtest_and_market_data_types():
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    backtest = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-backtest-1",
    )
    market = service.submit_job(
        user_id="u-1",
        task_type="market_data_sync",
        payload={"symbol": "AAPL"},
        idempotency_key="k-market-1",
    )

    assert backtest.status == "queued"
    assert market.status == "queued"


def test_idempotency_key_conflict_for_same_user():
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import IdempotencyConflictError, JobOrchestrationService

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="same-key",
    )

    with pytest.raises(IdempotencyConflictError):
        service.submit_job(
            user_id="u-1",
            task_type="backtest_run",
            payload={"strategyId": "s-2"},
            idempotency_key="same-key",
        )


def test_cancel_foreign_job_rejected():
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobAccessDeniedError, JobOrchestrationService

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    job = service.submit_job(
        user_id="u-2",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-1",
    )

    with pytest.raises(JobAccessDeniedError):
        service.cancel_job(user_id="u-1", job_id=job.id)


def test_retry_failed_job_returns_queued():
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    job = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-1",
    )
    service.transition_job(user_id="u-1", job_id=job.id, to_status="running")
    service.transition_job(user_id="u-1", job_id=job.id, to_status="failed")

    retried = service.retry_job(user_id="u-1", job_id=job.id)
    assert retried.status == "queued"


def test_public_methods_require_user_id():
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    with pytest.raises(TypeError):
        service.list_jobs()  # type: ignore[misc]


def test_supported_task_types_cover_wave3_worker_tasks():
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    supported = service.supported_task_types()

    assert "strategy_batch_execute" in supported
    assert "signal_batch_generate" in supported
    assert "risk_report_generate" in supported
    assert "trading_daily_stats_calculate" in supported
    assert "market_indicators_calculate" in supported
