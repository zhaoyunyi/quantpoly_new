"""策略健康报告领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class OverfitRisk(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SensitivityResult:
    param_name: str
    original_value: float
    variations: list[dict[str, Any]]
    rating: str


@dataclass
class HealthReport:
    id: str
    user_id: str
    strategy_id: str | None
    config: dict[str, Any]
    status: str = "pending"
    report: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        config: dict[str, Any],
        strategy_id: str | None = None,
    ) -> "HealthReport":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            config=config,
        )
