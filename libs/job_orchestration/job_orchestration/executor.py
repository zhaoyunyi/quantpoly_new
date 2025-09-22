"""job_orchestration 任务执行器抽象与 in-process 基线实现。"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from job_orchestration.domain import Job


class JobExecutorError(RuntimeError):
    """执行器错误。"""


@dataclass(frozen=True)
class ExecutionCallbackPayload:
    job_id: str
    user_id: str
    dispatch_id: str
    executor_name: str
    status: str
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None


ExecutionCallback = Callable[[ExecutionCallbackPayload], None]


class JobExecutor(Protocol):
    @property
    def name(self) -> str: ...

    def submit(self, *, job: Job) -> str: ...

    def dispatch(self, *, job: Job, dispatch_id: str, callback: ExecutionCallback) -> None: ...


class InProcessJobExecutor:
    def __init__(
        self,
        *,
        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]] | None = None,
    ) -> None:
        self._handlers = dict(handlers or {})

    @property
    def name(self) -> str:
        return "inprocess"

    def submit(self, *, job: Job) -> str:
        del job
        return str(uuid.uuid4())

    def dispatch(self, *, job: Job, dispatch_id: str, callback: ExecutionCallback) -> None:
        handler = self._handlers.get(job.task_type)
        if handler is None:
            callback(
                ExecutionCallbackPayload(
                    job_id=job.id,
                    user_id=job.user_id,
                    dispatch_id=dispatch_id,
                    executor_name=self.name,
                    status="failed",
                    error_code="TASK_HANDLER_NOT_FOUND",
                    error_message=f"task handler not found for task_type={job.task_type}",
                )
            )
            return

        try:
            result = handler(dict(job.payload))
        except Exception as exc:  # noqa: BLE001
            callback(
                ExecutionCallbackPayload(
                    job_id=job.id,
                    user_id=job.user_id,
                    dispatch_id=dispatch_id,
                    executor_name=self.name,
                    status="failed",
                    error_code="EXECUTOR_DISPATCH_FAILED",
                    error_message=str(exc),
                )
            )
            return

        callback(
            ExecutionCallbackPayload(
                job_id=job.id,
                user_id=job.user_id,
                dispatch_id=dispatch_id,
                executor_name=self.name,
                status="succeeded",
                result=dict(result or {}),
            )
        )
