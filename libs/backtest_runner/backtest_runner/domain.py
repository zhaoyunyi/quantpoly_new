"""回测任务领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

_BACKTEST_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running", "cancelled"},
    "running": {"completed", "failed", "cancelled"},
    "failed": {"pending"},
    "cancelled": {"pending"},
    "completed": set(),
}


class InvalidBacktestTransitionError(ValueError):
    """非法回测状态迁移。"""


@dataclass
class BacktestTask:
    id: str
    user_id: str
    strategy_id: str
    config: dict[str, Any]
    idempotency_key: str | None = None
    status: str = "pending"
    metrics: dict[str, float] | None = None
    display_name: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        strategy_id: str,
        config: dict[str, Any],
        idempotency_key: str | None = None,
        display_name: str | None = None,
    ) -> "BacktestTask":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            config=config,
            idempotency_key=idempotency_key,
            display_name=display_name,
        )

    def transition_to(self, to_status: str, *, metrics: dict[str, float] | None = None) -> None:
        allowed = _BACKTEST_TRANSITIONS.get(self.status, set())
        if to_status not in allowed:
            raise InvalidBacktestTransitionError(
                f"invalid_transition from={self.status} to={to_status}"
            )
        self.status = to_status
        self.updated_at = datetime.now(timezone.utc)
        if to_status == "completed":
            self.metrics = metrics or {}
        elif to_status == "pending":
            self.metrics = None

    def rename(self, *, display_name: str | None) -> None:
        normalized = (display_name or "").strip()
        self.display_name = normalized or None
        self.updated_at = datetime.now(timezone.utc)
