"""risk_control 领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RiskRule:
    id: str
    user_id: str
    account_id: str
    rule_name: str
    threshold: float
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        rule_name: str,
        threshold: float,
    ) -> "RiskRule":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            rule_name=rule_name,
            threshold=threshold,
        )


@dataclass
class RiskAlert:
    id: str
    user_id: str
    account_id: str
    rule_name: str
    severity: str
    message: str
    status: str = "open"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        rule_name: str,
        severity: str,
        message: str,
    ) -> "RiskAlert":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            rule_name=rule_name,
            severity=severity,
            message=message,
        )

    def acknowledge(self) -> None:
        self.status = "acknowledged"
        self.acknowledged_at = datetime.now(timezone.utc)

    def resolve(self) -> None:
        self.status = "resolved"
        self.resolved_at = datetime.now(timezone.utc)
