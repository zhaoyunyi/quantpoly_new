"""策略管理领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


_STRATEGY_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"active", "inactive", "archived"},
    "active": {"inactive", "archived"},
    "inactive": {"active", "archived"},
    "archived": set(),
}


class StrategyInUseError(RuntimeError):
    """策略被运行中/排队中回测占用。"""


class InvalidStrategyTransitionError(ValueError):
    """非法策略状态迁移。"""


@dataclass
class Strategy:
    id: str
    user_id: str
    name: str
    template: str
    parameters: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        name: str,
        template: str,
        parameters: dict[str, Any] | None = None,
    ) -> "Strategy":
        now = datetime.now(timezone.utc)
        return cls(
            id=f"{user_id}-{uuid.uuid4()}",
            user_id=user_id,
            name=name,
            template=template,
            parameters=parameters or {},
            status="draft",
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        *,
        name: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        changed = False

        if name is not None and name != self.name:
            self.name = name
            changed = True

        if parameters is not None and parameters != self.parameters:
            self.parameters = parameters
            changed = True

        if changed:
            self.updated_at = datetime.now(timezone.utc)

    def transition_to(self, to_status: str) -> None:
        allowed = _STRATEGY_TRANSITIONS.get(self.status, set())
        if to_status not in allowed:
            raise InvalidStrategyTransitionError(
                f"invalid_transition from={self.status} to={to_status}"
            )
        self.status = to_status
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        self.transition_to("active")

    def deactivate(self) -> None:
        self.transition_to("inactive")

    def archive(self) -> None:
        self.transition_to("archived")
