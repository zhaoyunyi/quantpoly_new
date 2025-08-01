"""job_orchestration in-memory 仓储。"""

from __future__ import annotations

from job_orchestration.domain import Job


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._idempotency: dict[tuple[str, str], str] = {}

    def save(self, job: Job) -> None:
        self._jobs[job.id] = job
        self._idempotency[(job.user_id, job.idempotency_key)] = job.id

    def get(self, *, user_id: str, job_id: str) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None or job.user_id != user_id:
            return None
        return job

    def list(self, *, user_id: str, status: str | None = None) -> list[Job]:
        return [
            job
            for job in self._jobs.values()
            if job.user_id == user_id and (status is None or job.status == status)
        ]

    def find_by_idempotency_key(self, *, user_id: str, idempotency_key: str) -> Job | None:
        job_id = self._idempotency.get((user_id, idempotency_key))
        if job_id is None:
            return None
        return self._jobs.get(job_id)
