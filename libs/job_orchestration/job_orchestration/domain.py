"""job_orchestration 领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "queued": {"running", "cancelled"},
    "running": {"succeeded", "failed", "cancelled"},
    "failed": {"queued", "cancelled"},
    "succeeded": set(),
    "cancelled": set(),
}


class InvalidJobTransitionError(ValueError):
    """非法任务状态迁移。"""


@dataclass
class Job:
    id: str
    user_id: str
    task_type: str
    payload: dict[str, Any]
    idempotency_key: str
    status: str = "queued"
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    executor_name: str | None = None
    dispatch_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        task_type: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> "Job":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            task_type=task_type,
            payload=payload,
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
        )

    def transition_to(self, to_status: str) -> None:
        allowed = _ALLOWED_TRANSITIONS.get(self.status, set())
        if to_status not in allowed:
            raise InvalidJobTransitionError(f"invalid_transition from={self.status} to={to_status}")

        now = datetime.now(timezone.utc)
        self.status = to_status

        if to_status == "queued":
            self.result = None
            self.error_code = None
            self.error_message = None
            self.executor_name = None
            self.dispatch_id = None
            self.started_at = None
            self.finished_at = None
        elif to_status == "running":
            if self.started_at is None:
                self.started_at = now
            self.finished_at = None
        elif to_status in {"succeeded", "failed", "cancelled"}:
            self.finished_at = now

        self.updated_at = now

    def start_execution(self, *, executor_name: str, dispatch_id: str) -> None:
        self.executor_name = executor_name
        self.dispatch_id = dispatch_id
        self.transition_to("running")

    def mark_succeeded(self, *, result: dict[str, Any] | None = None) -> None:
        self.transition_to("succeeded")
        self.result = dict(result or {})
        self.error_code = None
        self.error_message = None

    def mark_failed(self, *, error_code: str, error_message: str) -> None:
        self.transition_to("failed")
        self.result = None
        self.error_code = error_code
        self.error_message = error_message


@dataclass
class ScheduleConfig:
    id: str
    user_id: str
    namespace: str
    job_type: str
    schedule_type: str
    expression: str
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        namespace: str,
        job_type: str,
        schedule_type: str,
        expression: str,
    ) -> "ScheduleConfig":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            namespace=namespace,
            job_type=job_type,
            schedule_type=schedule_type,
            expression=expression,
            status="active",
            created_at=now,
            updated_at=now,
        )

    def stop(self) -> None:
        if self.status == "stopped":
            return
        self.status = "stopped"
        self.updated_at = datetime.now(timezone.utc)
