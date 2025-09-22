"""job_orchestration 应用服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from job_orchestration.domain import InvalidJobTransitionError, Job, ScheduleConfig
from job_orchestration.executor import ExecutionCallbackPayload, InProcessJobExecutor, JobExecutor
from job_orchestration.task_registry import list_task_type_definitions, supported_task_types


class JobRepository(Protocol):
    def save(self, job: Job) -> None: ...

    def save_if_absent(self, job: Job) -> bool: ...

    def get(self, *, user_id: str, job_id: str) -> Job | None: ...

    def list(self, *, user_id: str, status: str | None = None, task_type: str | None = None) -> list[Job]: ...

    def list_all(self, *, status: str | None = None) -> list[Job]: ...

    def find_by_idempotency_key(self, *, user_id: str, idempotency_key: str) -> Job | None: ...


class JobScheduler(Protocol):
    running: bool

    def register_interval(
        self,
        *,
        job_type: str,
        every_seconds: int,
        user_id: str = "system",
        namespace: str = "system",
    ) -> ScheduleConfig: ...

    def register_cron(
        self,
        *,
        job_type: str,
        cron_expr: str,
        user_id: str = "system",
        namespace: str = "system",
    ) -> ScheduleConfig: ...

    def list_schedules(self, *, user_id: str | None = None, namespace: str | None = None) -> list[ScheduleConfig]: ...

    def get_schedule(self, *, schedule_id: str) -> ScheduleConfig | None: ...

    def stop_schedule(self, *, schedule_id: str) -> ScheduleConfig | None: ...

    def recover(self) -> int: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...


class IdempotencyConflictError(RuntimeError):
    """幂等键冲突。"""


class JobAccessDeniedError(PermissionError):
    """无权访问任务。"""


class ScheduleAccessDeniedError(PermissionError):
    """无权访问调度配置。"""


class JobOrchestrationService:
    def __init__(
        self,
        *,
        repository: JobRepository,
        scheduler: JobScheduler,
        executor: JobExecutor | None = None,
        auto_recover: bool = True,
    ) -> None:
        self._repository = repository
        self._scheduler = scheduler
        self._executor = executor or InProcessJobExecutor()
        self._last_recovery: dict[str, Any] = {
            "recoveredRunningJobs": 0,
            "recoveredSchedules": 0,
            "recoveredAt": None,
        }

        if auto_recover:
            self.recover_runtime()

    def supported_task_types(self) -> list[str]:
        return sorted(supported_task_types())

    def task_type_registry(self) -> list[dict[str, Any]]:
        return [item.to_payload() for item in list_task_type_definitions()]

    def _assert_task_type_supported(self, *, task_type: str) -> None:
        if task_type not in supported_task_types():
            raise ValueError(f"unsupported task_type={task_type}")

    def _namespace_for_user(self, *, user_id: str) -> str:
        return f"user:{user_id}"

    def _load_owned_job(self, *, user_id: str, job_id: str) -> Job:
        job = self._repository.get(user_id=user_id, job_id=job_id)
        if job is None:
            raise JobAccessDeniedError("job does not belong to current user")
        return job

    def submit_job(
        self,
        *,
        user_id: str,
        task_type: str,
        payload: dict,
        idempotency_key: str,
    ) -> Job:
        self._assert_task_type_supported(task_type=task_type)

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

    def find_by_idempotency_key(self, *, user_id: str, idempotency_key: str) -> Job | None:
        return self._repository.find_by_idempotency_key(user_id=user_id, idempotency_key=idempotency_key)

    def get_job(self, *, user_id: str, job_id: str) -> Job | None:
        return self._repository.get(user_id=user_id, job_id=job_id)

    def list_jobs(
        self,
        *,
        user_id: str,
        status: str | None = None,
        task_type: str | None = None,
    ) -> list[Job]:
        return self._repository.list(user_id=user_id, status=status, task_type=task_type)

    def transition_job(self, *, user_id: str, job_id: str, to_status: str) -> Job:
        job = self._load_owned_job(user_id=user_id, job_id=job_id)

        job.transition_to(to_status)
        self._repository.save(job)
        return job

    def start_job(self, *, user_id: str, job_id: str) -> Job:
        return self.transition_job(user_id=user_id, job_id=job_id, to_status="running")

    def succeed_job(self, *, user_id: str, job_id: str, result: dict) -> Job:
        job = self._load_owned_job(user_id=user_id, job_id=job_id)

        job.mark_succeeded(result=result)
        self._repository.save(job)
        return job

    def fail_job(self, *, user_id: str, job_id: str, error_code: str, error_message: str) -> Job:
        job = self._load_owned_job(user_id=user_id, job_id=job_id)

        job.mark_failed(error_code=error_code, error_message=error_message)
        self._repository.save(job)
        return job

    def _apply_execution_callback(self, event: ExecutionCallbackPayload) -> None:
        job = self._repository.get(user_id=event.user_id, job_id=event.job_id)
        if job is None:
            return

        if event.status == "succeeded":
            job.mark_succeeded(result=dict(event.result or {}))
        else:
            job.mark_failed(
                error_code=event.error_code or "EXECUTION_FAILED",
                error_message=event.error_message or "job execution failed",
            )

        job.executor_name = event.executor_name
        job.dispatch_id = event.dispatch_id
        self._repository.save(job)

    def dispatch_job(self, *, user_id: str, job_id: str) -> Job:
        job = self._load_owned_job(user_id=user_id, job_id=job_id)

        dispatch_id = self._executor.submit(job=job)
        job.start_execution(executor_name=self._executor.name, dispatch_id=dispatch_id)
        self._repository.save(job)

        self._executor.dispatch(
            job=job,
            dispatch_id=dispatch_id,
            callback=self._apply_execution_callback,
        )

        refreshed = self._repository.get(user_id=user_id, job_id=job_id)
        if refreshed is None:
            raise JobAccessDeniedError("job does not belong to current user")
        return refreshed

    def cancel_job(self, *, user_id: str, job_id: str) -> Job:
        return self.transition_job(user_id=user_id, job_id=job_id, to_status="cancelled")

    def retry_job(self, *, user_id: str, job_id: str) -> Job:
        return self.transition_job(user_id=user_id, job_id=job_id, to_status="queued")

    def recover_runtime(self) -> dict[str, Any]:
        running_jobs = self._repository.list_all(status="running")
        recovered_running_jobs = 0

        for job in running_jobs:
            job.mark_failed(
                error_code="RUNTIME_RECOVERY",
                error_message="job interrupted by runtime restart",
            )
            self._repository.save(job)
            recovered_running_jobs += 1

        recovered_schedules = self._scheduler.recover()

        self._last_recovery = {
            "recoveredRunningJobs": recovered_running_jobs,
            "recoveredSchedules": recovered_schedules,
            "recoveredAt": datetime.now(timezone.utc).isoformat(),
        }
        return dict(self._last_recovery)

    def runtime_status(self) -> dict[str, Any]:
        return {
            "executor": {
                "name": self._executor.name,
            },
            "scheduler": {
                "running": bool(self._scheduler.running),
            },
            "recovery": dict(self._last_recovery),
        }

    def schedule_interval(self, *, user_id: str, task_type: str, every_seconds: int) -> ScheduleConfig:
        self._assert_task_type_supported(task_type=task_type)
        namespace = self._namespace_for_user(user_id=user_id)
        return self._scheduler.register_interval(
            user_id=user_id,
            namespace=namespace,
            job_type=task_type,
            every_seconds=every_seconds,
        )

    def schedule_cron(self, *, user_id: str, task_type: str, cron_expr: str) -> ScheduleConfig:
        self._assert_task_type_supported(task_type=task_type)
        namespace = self._namespace_for_user(user_id=user_id)
        return self._scheduler.register_cron(
            user_id=user_id,
            namespace=namespace,
            job_type=task_type,
            cron_expr=cron_expr,
        )

    def list_schedules(self, *, user_id: str) -> list[ScheduleConfig]:
        namespace = self._namespace_for_user(user_id=user_id)
        return self._scheduler.list_schedules(user_id=user_id, namespace=namespace)

    def get_schedule(self, *, user_id: str, schedule_id: str) -> ScheduleConfig | None:
        schedule = self._scheduler.get_schedule(schedule_id=schedule_id)
        if schedule is None:
            return None
        if schedule.user_id != user_id:
            return None
        if schedule.namespace != self._namespace_for_user(user_id=user_id):
            return None
        return schedule

    def stop_schedule(self, *, user_id: str, schedule_id: str) -> ScheduleConfig:
        schedule = self.get_schedule(user_id=user_id, schedule_id=schedule_id)
        if schedule is None:
            raise ScheduleAccessDeniedError("schedule access denied")

        stopped = self._scheduler.stop_schedule(schedule_id=schedule_id)
        if stopped is None:
            raise ScheduleAccessDeniedError("schedule access denied")
        return stopped

    def start_scheduler(self, *, user_id: str) -> None:
        del user_id
        self._scheduler.start()

    def stop_scheduler(self, *, user_id: str) -> None:
        del user_id
        self._scheduler.stop()


__all__ = [
    "JobOrchestrationService",
    "IdempotencyConflictError",
    "JobAccessDeniedError",
    "ScheduleAccessDeniedError",
    "InvalidJobTransitionError",
]
