"""admin_governance 领域模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ActionPolicy:
    action: str
    min_role: str
    min_level: int
    requires_confirmation: bool
    high_risk: bool


@dataclass
class PolicyResult:
    allowed: bool
    action: str
    reason: str


@dataclass
class AuditRecord:
    actor: str
    action: str
    target: str
    result: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: dict[str, Any] = field(default_factory=dict)
