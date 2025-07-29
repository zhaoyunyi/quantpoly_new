"""回测任务领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

_BACKTEST_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running", "cancelled"},
    "running": {"completed", "failed", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


class InvalidBacktestTransitionError(ValueError):
    """非法回测状态迁移。"""


@dataclass
class BacktestTask:
    id: str
    user_id: str
    strategy_id: str
    config: dict[str, Any]
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        strategy_id: str,
        config: dict[str, Any],
    ) -> "BacktestTask":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            config=config,
        )

    def transition_to(self, to_status: str) -> None:
        allowed = _BACKTEST_TRANSITIONS.get(self.status, set())
        if to_status not in allowed:
            raise InvalidBacktestTransitionError(
                f"invalid_transition from={self.status} to={to_status}"
            )
        self.status = to_status
        self.updated_at = datetime.now(timezone.utc)
