"""跨库访问策略与非法依赖检测。"""

from __future__ import annotations

from dataclasses import dataclass

from data_topology_boundary.catalog import BoundaryCatalog


@dataclass
class PolicyDecision:
    allowed: bool
    requires_acl: bool
    reason: str


class CrossDbPolicy:
    def __init__(self, *, catalog: BoundaryCatalog) -> None:
        self._catalog = catalog

    def validate_reference(self, *, from_model: str, to_model: str) -> PolicyDecision:
        from_db = self._catalog.model_database(from_model)
        to_db = self._catalog.model_database(to_model)

        if from_db is None or to_db is None:
            return PolicyDecision(
                allowed=False,
                requires_acl=False,
                reason="unknown model ownership",
            )

        if from_db == to_db:
            return PolicyDecision(
                allowed=True,
                requires_acl=False,
                reason="same database boundary",
            )

        return PolicyDecision(
            allowed=False,
            requires_acl=True,
            reason="cross database reference must go through ACL/anti-corruption layer",
        )


def detect_illegal_dependencies(
    *,
    edges: list[tuple[str, str]],
    policy: CrossDbPolicy,
) -> list[tuple[str, str]]:
    illegal: list[tuple[str, str]] = []
    for from_model, to_model in edges:
        decision = policy.validate_reference(from_model=from_model, to_model=to_model)
        if not decision.allowed:
            illegal.append((from_model, to_model))
    return illegal
