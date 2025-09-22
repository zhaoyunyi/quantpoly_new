"""job_orchestration 运行时执行器与恢复测试（Red->Green）。"""

from __future__ import annotations

from pathlib import Path

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
