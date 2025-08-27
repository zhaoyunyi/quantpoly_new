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
    strategy_id: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        rule_name: str,
        threshold: float,
        strategy_id: str | None = None,
    ) -> "RiskRule":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
            rule_name=rule_name,
            threshold=threshold,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        *,
        rule_name: str | None = None,
        threshold: float | None = None,
        strategy_id: str | None = None,
    ) -> None:
        if rule_name is not None:
            self.rule_name = rule_name
        if threshold is not None:
            self.threshold = threshold
        if strategy_id is not None:
            self.strategy_id = strategy_id
        self.updated_at = datetime.now(timezone.utc)

    def set_active(self, *, is_active: bool) -> None:
        self.is_active = is_active
        self.updated_at = datetime.now(timezone.utc)


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
    acknowledged_by: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    notification_status: str | None = None
    notified_at: datetime | None = None
    notified_by: str | None = None

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

    def acknowledge(self, *, actor_id: str) -> None:
        if self.status == "resolved":
            return
        self.status = "acknowledged"
        self.acknowledged_at = datetime.now(timezone.utc)
        self.acknowledged_by = actor_id

    def resolve(self, *, actor_id: str) -> None:
        self.status = "resolved"
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = actor_id

    def mark_notified(self, *, actor_id: str, notification_status: str = "sent") -> None:
        if self.status == "open":
            self.acknowledge(actor_id=actor_id)
        self.notification_status = notification_status
        self.notified_at = datetime.now(timezone.utc)
        self.notified_by = actor_id


@dataclass
class RiskAssessmentSnapshot:
    id: str
    user_id: str
    account_id: str
    strategy_id: str | None
    risk_score: float
    risk_level: str
    triggered_rule_ids: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None,
        risk_score: float,
        risk_level: str,
        triggered_rule_ids: list[str],
    ) -> "RiskAssessmentSnapshot":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
            risk_score=risk_score,
            risk_level=risk_level,
            triggered_rule_ids=list(triggered_rule_ids),
        )
