"""job_orchestration 持久化与事务语义测试。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import IdempotencyConflictError, JobOrchestrationService


class _RaceSubmissionRepository(InMemoryJobRepository):
    def __init__(self) -> None:
        super().__init__()
        self._barrier = threading.Barrier(2)

    def find_by_idempotency_key(self, *, user_id: str, idempotency_key: str):
        found = super().find_by_idempotency_key(user_id=user_id, idempotency_key=idempotency_key)
        if found is None:
            self._barrier.wait(timeout=1)
        return found


class _FailBeforeCommitRepository(InMemoryJobRepository):
    def __init__(self) -> None:
        super().__init__()
        self.fail_next_commit = False

    def _before_commit(self, *, job) -> None:
        del job
        if self.fail_next_commit:
            self.fail_next_commit = False
            raise RuntimeError("persistence write failed")


def _build_service(repository: InMemoryJobRepository) -> JobOrchestrationService:
    return JobOrchestrationService(repository=repository, scheduler=InMemoryScheduler())


def test_concurrent_submit_same_idempotency_key_only_one_success():
    service = _build_service(_RaceSubmissionRepository())

    def _submit_one():
        try:
            service.submit_job(
                user_id="u-1",
                task_type="backtest_run",
                payload={"strategyId": "s-1"},
                idempotency_key="same-key",
            )
            return "ok"
        except IdempotencyConflictError:
            return "idempotency_conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_submit_one) for _ in range(2)]
        results = [future.result() for future in futures]

    assert results.count("ok") == 1
    assert results.count("idempotency_conflict") == 1
    assert len(service.list_jobs(user_id="u-1")) == 1


def test_retry_failed_job_persists_transition_back_to_queued():
    service = _build_service(InMemoryJobRepository())

    job = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="retry-key",
    )
    service.transition_job(user_id="u-1", job_id=job.id, to_status="running")
    service.transition_job(user_id="u-1", job_id=job.id, to_status="failed")

    retried = service.retry_job(user_id="u-1", job_id=job.id)
    stored = service.get_job(user_id="u-1", job_id=job.id)

    assert retried.status == "queued"
    assert stored is not None
    assert stored.status == "queued"


def test_retry_persistence_write_failure_rolls_back_state():
    repository = _FailBeforeCommitRepository()
    service = _build_service(repository)

    job = service.submit_job(
        user_id="u-1",
        task_type="backtest_run",
        payload={"strategyId": "s-1"},
        idempotency_key="rollback-key",
    )
    service.transition_job(user_id="u-1", job_id=job.id, to_status="running")
    service.transition_job(user_id="u-1", job_id=job.id, to_status="failed")

    repository.fail_next_commit = True
    with pytest.raises(RuntimeError, match="persistence write failed"):
        service.retry_job(user_id="u-1", job_id=job.id)

    stored = service.get_job(user_id="u-1", job_id=job.id)
    assert stored is not None
    assert stored.status == "failed"
