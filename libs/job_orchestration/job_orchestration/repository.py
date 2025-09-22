"""job_orchestration in-memory 仓储。"""

from __future__ import annotations

import copy
import threading

from job_orchestration.domain import Job


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._idempotency: dict[tuple[str, str], str] = {}
        self._lock = threading.RLock()

    def save(self, job: Job) -> None:
        with self._lock:
            self._before_commit(job=job)
            self._persist(job)

    def save_if_absent(self, job: Job) -> bool:
        with self._lock:
            key = (job.user_id, job.idempotency_key)
            if key in self._idempotency:
                return False

            self._before_commit(job=job)
            self._persist(job)
            return True

    def _before_commit(self, *, job: Job) -> None:
        del job

    def _persist(self, job: Job) -> None:
        stored = self._clone(job)
        self._jobs[stored.id] = stored
        self._idempotency[(stored.user_id, stored.idempotency_key)] = stored.id

    def _clone(self, job: Job) -> Job:
        return Job(
            id=job.id,
            user_id=job.user_id,
            task_type=job.task_type,
            payload=copy.deepcopy(job.payload),
            idempotency_key=job.idempotency_key,
            status=job.status,
            result=copy.deepcopy(job.result),
            error_code=job.error_code,
            error_message=job.error_message,
            executor_name=job.executor_name,
            dispatch_id=job.dispatch_id,
            started_at=job.started_at,
            finished_at=job.finished_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    def get(self, *, user_id: str, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.user_id != user_id:
                return None
            return self._clone(job)

    def list(
        self,
        *,
        user_id: str,
        status: str | None = None,
        task_type: str | None = None,
    ) -> list[Job]:
        with self._lock:
            return [
                self._clone(job)
                for job in self._jobs.values()
                if job.user_id == user_id
                and (status is None or job.status == status)
                and (task_type is None or job.task_type == task_type)
            ]

    def list_all(self, *, status: str | None = None) -> list[Job]:
        with self._lock:
            return [
                self._clone(job)
                for job in self._jobs.values()
                if status is None or job.status == status
            ]

    def find_by_idempotency_key(self, *, user_id: str, idempotency_key: str) -> Job | None:
        with self._lock:
            job_id = self._idempotency.get((user_id, idempotency_key))
            if job_id is None:
                return None
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return self._clone(job)
