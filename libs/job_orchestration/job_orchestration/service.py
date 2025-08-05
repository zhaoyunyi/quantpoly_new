"""job_orchestration 应用服务。"""

from __future__ import annotations

from job_orchestration.domain import InvalidJobTransitionError, Job
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler

_SUPPORTED_TASK_TYPES = {
    "backtest_run",
    "market_data_sync",
}


class IdempotencyConflictError(RuntimeError):
    """幂等键冲突。"""


class JobAccessDeniedError(PermissionError):
    """无权访问任务。"""


class JobOrchestrationService:
    def __init__(
        self,
        *,
        repository: InMemoryJobRepository,
        scheduler: InMemoryScheduler,
    ) -> None:
        self._repository = repository
        self._scheduler = scheduler

    def submit_job(
        self,
        *,
        user_id: str,
        task_type: str,
        payload: dict,
        idempotency_key: str,
    ) -> Job:
        if task_type not in _SUPPORTED_TASK_TYPES:
            raise ValueError(f"unsupported task_type={task_type}")

        exists = self._repository.find_by_idempotency_key(
            user_id=user_id,
            idempotency_key=idempotency_key,
        )
        if exists is not None:
            raise IdempotencyConflictError("idempotency key already exists")

        job = Job.create(
            user_id=user_id,
            task_type=task_type,
            payload=payload,
            idempotency_key=idempotency_key,
        )
        created = self._repository.save_if_absent(job)
        if not created:
            raise IdempotencyConflictError("idempotency key already exists")
        return job

    def get_job(self, *, user_id: str, job_id: str) -> Job | None:
        return self._repository.get(user_id=user_id, job_id=job_id)

    def list_jobs(self, *, user_id: str, status: str | None = None) -> list[Job]:
        return self._repository.list(user_id=user_id, status=status)

    def transition_job(self, *, user_id: str, job_id: str, to_status: str) -> Job:
        job = self._repository.get(user_id=user_id, job_id=job_id)
        if job is None:
            raise JobAccessDeniedError("job does not belong to current user")

        job.transition_to(to_status)
        self._repository.save(job)
        return job

    def cancel_job(self, *, user_id: str, job_id: str) -> Job:
        return self.transition_job(user_id=user_id, job_id=job_id, to_status="cancelled")

    def retry_job(self, *, user_id: str, job_id: str) -> Job:
        return self.transition_job(user_id=user_id, job_id=job_id, to_status="queued")

    def schedule_interval(self, *, user_id: str, task_type: str, every_seconds: int) -> None:
        del user_id
        self._scheduler.register_interval(job_type=task_type, every_seconds=every_seconds)

    def schedule_cron(self, *, user_id: str, task_type: str, cron_expr: str) -> None:
        del user_id
        self._scheduler.register_cron(job_type=task_type, cron_expr=cron_expr)

    def start_scheduler(self, *, user_id: str) -> None:
        del user_id
        self._scheduler.start()

    def stop_scheduler(self, *, user_id: str) -> None:
        del user_id
        self._scheduler.stop()

    def list_schedules(self, *, user_id: str):
        del user_id
        return self._scheduler.list_schedules()


__all__ = [
    "JobOrchestrationService",
    "IdempotencyConflictError",
    "JobAccessDeniedError",
    "InvalidJobTransitionError",
]
