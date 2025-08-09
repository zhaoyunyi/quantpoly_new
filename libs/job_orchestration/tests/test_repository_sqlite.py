"""job_orchestration SQLite 仓储测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from job_orchestration.repository_sqlite import SQLiteJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import IdempotencyConflictError, JobOrchestrationService


def _sqlite_repo(db_path: Path) -> SQLiteJobRepository:
    return SQLiteJobRepository(db_path=str(db_path))


def test_sqlite_repository_persists_job_status_and_idempotency(tmp_path):
    db_path = tmp_path / "job_orchestration.sqlite3"

    repo1 = _sqlite_repo(db_path)
    service1 = JobOrchestrationService(repository=repo1, scheduler=InMemoryScheduler())

    job = service1.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="k-1",
    )
    service1.transition_job(user_id="u-1", job_id=job.id, to_status="running")
    service1.transition_job(user_id="u-1", job_id=job.id, to_status="failed")
    service1.retry_job(user_id="u-1", job_id=job.id)

    repo2 = _sqlite_repo(db_path)
    service2 = JobOrchestrationService(repository=repo2, scheduler=InMemoryScheduler())

    persisted = service2.get_job(user_id="u-1", job_id=job.id)
    assert persisted is not None
    assert persisted.status == "queued"

    with pytest.raises(IdempotencyConflictError):
        service2.submit_job(
            user_id="u-1",
            task_type="backtest_run",
            payload={"strategyId": "s-1"},
            idempotency_key="k-1",
        )
