"""平台统一鉴权辅助能力。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdminDecision:
    is_admin: bool
    source: str


def resolve_admin_decision(actor: Any) -> AdminDecision:
    role = getattr(actor, "role", None)
    if isinstance(role, str) and role.strip().lower() == "admin":
        return AdminDecision(is_admin=True, source="role")

    is_admin = getattr(actor, "is_admin", None)
    if isinstance(is_admin, bool) and is_admin:
        return AdminDecision(is_admin=True, source="is_admin")

    level = getattr(actor, "level", None)
    if isinstance(level, int) and level >= 10:
        return AdminDecision(is_admin=True, source="level")

    return AdminDecision(is_admin=False, source="none")


def is_admin_actor(actor: Any) -> bool:
    return resolve_admin_decision(actor).is_admin
