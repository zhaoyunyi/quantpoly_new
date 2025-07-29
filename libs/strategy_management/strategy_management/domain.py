"""策略管理领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class StrategyInUseError(RuntimeError):
    """策略被运行中/排队中回测占用。"""


@dataclass
class Strategy:
    id: str
    user_id: str
    name: str
    template: str
    parameters: dict[str, Any] = field(default_factory=dict)
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
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            template=template,
            parameters=parameters or {},
            created_at=now,
            updated_at=now,
        )
