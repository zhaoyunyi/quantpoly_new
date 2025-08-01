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
        self.status = to_status
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ScheduleConfig:
    job_type: str
    schedule_type: str
    expression: str
