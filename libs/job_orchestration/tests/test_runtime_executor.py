"""job_orchestration 运行时执行器与恢复测试（Red->Green）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import JobOrchestrationService


def test_dispatch_job_with_inprocess_executor_updates_observability_fields():
    from job_orchestration.executor import InProcessJobExecutor

    executor = InProcessJobExecutor(
        handlers={
            "backtest_run": lambda payload: {
                "accepted": payload["strategyId"],
            }
        }
    )
    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
        executor=executor,
    )

    job = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-exec-1",
    )

    dispatched = service.dispatch_job(user_id="u-1", job_id=job.id)

    assert dispatched.status == "succeeded"
    assert dispatched.executor_name == "inprocess"
    assert dispatched.dispatch_id
    assert dispatched.started_at is not None
    assert dispatched.finished_at is not None
    assert dispatched.result == {"accepted": "s-1"}


def test_runtime_recovery_marks_running_jobs_failed_but_keeps_queued_jobs():
    repository = InMemoryJobRepository()
    scheduler = InMemoryScheduler()

    service = JobOrchestrationService(
        repository=repository,
        scheduler=scheduler,
        auto_recover=False,
    )

    running = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-running"},
        idempotency_key="k-running",
    )
    queued = service.submit_job(
        user_id="u-1",
        task_type="market_data_sync",
        payload={"symbols": ["AAPL"]},
        idempotency_key="k-queued",
    )

    service.transition_job(user_id="u-1", job_id=running.id, to_status="running")

    recovered_service = JobOrchestrationService(
        repository=repository,
        scheduler=scheduler,
        auto_recover=True,
    )
    runtime = recovered_service.runtime_status()

    assert runtime["recovery"]["recoveredRunningJobs"] == 1

    running_after = recovered_service.get_job(user_id="u-1", job_id=running.id)
    queued_after = recovered_service.get_job(user_id="u-1", job_id=queued.id)

    assert running_after is not None
    assert queued_after is not None
    assert running_after.status == "failed"
    assert running_after.error_code == "RUNTIME_RECOVERY"
    assert queued_after.status == "queued"


def test_sqlite_scheduler_persists_and_recovers_schedules(tmp_path: Path):
    from job_orchestration.scheduler import SQLiteScheduler

    db_path = tmp_path / "job_scheduler.sqlite3"

    scheduler_first = SQLiteScheduler(db_path=str(db_path))
    created = scheduler_first.register_interval(
        user_id="u-1",
        namespace="user:u-1",
        job_type="market_data_sync",
        every_seconds=60,
    )

    scheduler_second = SQLiteScheduler(db_path=str(db_path))
    recovered = scheduler_second.recover()
    rows = scheduler_second.list_schedules(user_id="u-1", namespace="user:u-1")

    assert recovered == 1
    assert len(rows) == 1
    assert rows[0].id == created.id



def test_dispatch_job_with_callable_updates_observability_fields():
    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    job = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-dispatch-callable-1",
    )

    dispatched = service.dispatch_job_with_callable(
        user_id="u-1",
        job_id=job.id,
        runner=lambda payload: {"accepted": payload["strategyId"]},
    )

    assert dispatched.status == "succeeded"
    assert dispatched.executor_name == "inprocess"
    assert dispatched.dispatch_id
    assert dispatched.started_at is not None
    assert dispatched.finished_at is not None
    assert dispatched.result == {"accepted": "s-1"}


def test_dispatch_job_with_callable_maps_failure_error_code_and_result():
    from job_orchestration.service import JobExecutionFailure

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    job = service.submit_job(
        user_id="u-1",
        task_type="market_data_sync",
        payload={"symbols": ["AAPL"]},
        idempotency_key="k-dispatch-callable-failed-1",
    )

    def _runner(_payload: dict):
        raise JobExecutionFailure(
            error_code="MARKET_DATA_SYNC_FAILED",
            error_message="market data sync completed with failures",
            result={"summary": {"failureCount": 1}},
        )

    failed = service.dispatch_job_with_callable(
        user_id="u-1",
        job_id=job.id,
        runner=_runner,
    )

    assert failed.status == "failed"
    assert failed.error_code == "MARKET_DATA_SYNC_FAILED"
    assert failed.error_message == "market data sync completed with failures"
    assert failed.result == {"summary": {"failureCount": 1}}
    assert failed.executor_name == "inprocess"
    assert failed.dispatch_id


def test_runtime_status_includes_executor_mode_and_execution_metrics():
    from job_orchestration.service import JobExecutionFailure

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    first = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-runtime-metrics-1",
    )
    service.dispatch_job_with_callable(
        user_id="u-1",
        job_id=first.id,
        runner=lambda _payload: {"ok": True},
    )

    second = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-2"},
        idempotency_key="k-runtime-metrics-2",
    )

    def _failed(_payload: dict):
        raise JobExecutionFailure(
            error_code="EXECUTION_FAILED",
            error_message="boom",
        )

    service.dispatch_job_with_callable(
        user_id="u-1",
        job_id=second.id,
        runner=_failed,
    )

    runtime = service.runtime_status()

    assert runtime["executor"]["mode"] == "inprocess"
    assert runtime["execution"]["dispatched"] == 2
    assert runtime["execution"]["succeeded"] == 1
    assert runtime["execution"]["failed"] == 1


def test_register_and_recover_system_schedule_templates_is_deduplicated():
    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
        auto_recover=False,
    )

    first = service.register_system_schedule_templates()
    second = service.register_system_schedule_templates()
    recovered = service.recover_system_schedule_templates()

    assert first["total"] >= 4
    assert first["created"] >= 4
    assert second["created"] == 0
    assert second["deduplicated"] == first["total"]
    assert recovered["created"] == 0

    runtime = service.runtime_status()
    assert runtime["systemSchedules"]["total"] >= 4
    assert runtime["systemSchedules"]["active"] >= 4


def test_dispatch_job_blocks_when_concurrency_limit_exceeded():
    """并发上限守卫：超过 SLA concurrencyLimit 时不进入 running。"""

    class _NoCallbackExecutor:
        @property
        def name(self) -> str:
            return "noop"

        def submit(self, *, job) -> str:  # type: ignore[no-untyped-def]
            return f"dispatch:{job.id}"

        def dispatch(self, *, job, dispatch_id: str, callback) -> None:  # type: ignore[no-untyped-def]
            del job, dispatch_id, callback
            # 故意不调用 callback，使任务保持 running。
            return

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
        executor=_NoCallbackExecutor(),
    )

    first = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-concurrency-1",
    )

    running = service.dispatch_job(user_id="u-1", job_id=first.id)
    assert running.status == "running"

    second = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-2"},
        idempotency_key="k-concurrency-2",
    )

    blocked = service.dispatch_job(user_id="u-1", job_id=second.id)

    assert blocked.status == "queued"
    assert blocked.error_code == "CONCURRENCY_LIMIT_EXCEEDED"
    assert blocked.error_message is not None


def test_dispatch_job_on_running_job_raises_invalid_transition():
    """并发守卫不应掩盖非法状态迁移。"""

    from job_orchestration.domain import InvalidJobTransitionError

    class _NoCallbackExecutor:
        @property
        def name(self) -> str:
            return "noop"

        def submit(self, *, job) -> str:  # type: ignore[no-untyped-def]
            return f"dispatch:{job.id}"

        def dispatch(self, *, job, dispatch_id: str, callback) -> None:  # type: ignore[no-untyped-def]
            del job, dispatch_id, callback
            return

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
        executor=_NoCallbackExecutor(),
    )

    job = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-dispatch-running-1",
    )

    running = service.dispatch_job(user_id="u-1", job_id=job.id)
    assert running.status == "running"

    with pytest.raises(InvalidJobTransitionError):
        service.dispatch_job(user_id="u-1", job_id=job.id)
