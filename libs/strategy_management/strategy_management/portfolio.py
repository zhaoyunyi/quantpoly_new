"""策略组合（Portfolio）聚合与读模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


_PORTFOLIO_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"active", "archived"},
    "active": {"draft", "archived"},
    "archived": set(),
}


class InvalidPortfolioConstraintsError(ValueError):
    """组合约束非法。"""


class InvalidPortfolioWeightsError(ValueError):
    """组合权重非法。"""


class InvalidPortfolioTransitionError(ValueError):
    """组合状态迁移非法。"""


class PortfolioMemberNotFoundError(KeyError):
    """组合成员策略不存在。"""


@dataclass
class PortfolioMember:
    strategy_id: str
    weight: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategyId": self.strategy_id,
            "weight": round(float(self.weight), 6),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass
class Portfolio:
    id: str
    user_id: str
    name: str
    constraints: dict[str, float]
    members: list[PortfolioMember] = field(default_factory=list)
    status: str = "draft"
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        name: str,
        constraints: dict[str, Any] | None = None,
    ) -> "Portfolio":
        now = datetime.now(timezone.utc)
        return cls(
            id=f"{user_id}-portfolio-{uuid.uuid4()}",
            user_id=user_id,
            name=str(name),
            constraints=_normalize_constraints(constraints),
            members=[],
            status="draft",
            version=1,
            created_at=now,
            updated_at=now,
        )

    @property
    def total_weight(self) -> float:
        return float(sum(member.weight for member in self.members))

    @property
    def member_count(self) -> int:
        return len(self.members)

    def _touch(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def update(self, *, name: str | None = None, constraints: dict[str, Any] | None = None) -> None:
        changed = False

        if name is not None:
            normalized_name = str(name).strip()
            if not normalized_name:
                raise InvalidPortfolioConstraintsError("portfolio.name is required")
            if normalized_name != self.name:
                self.name = normalized_name
                changed = True

        if constraints is not None:
            normalized_constraints = _normalize_constraints(constraints)
            weight_map = {member.strategy_id: member.weight for member in self.members}
            _validate_weights(weight_map=weight_map, constraints=normalized_constraints)
            if normalized_constraints != self.constraints:
                self.constraints = normalized_constraints
                changed = True

        if changed:
            self._touch()

    def transition_to(self, to_status: str) -> None:
        normalized = str(to_status).strip().lower()
        allowed = _PORTFOLIO_TRANSITIONS.get(self.status, set())
        if normalized not in allowed:
            raise InvalidPortfolioTransitionError(
                f"invalid_transition from={self.status} to={normalized}"
            )
        self.status = normalized
        self._touch()

    def activate(self) -> None:
        self.transition_to("active")

    def archive(self) -> None:
        self.transition_to("archived")

    def add_member(self, *, strategy_id: str, weight: float) -> None:
        normalized_id = str(strategy_id).strip()
        if not normalized_id:
            raise InvalidPortfolioWeightsError("strategyId is required")

        target_weight = _normalize_weight(weight)
        weight_map = {member.strategy_id: member.weight for member in self.members}
        weight_map[normalized_id] = target_weight
        _validate_weights(weight_map=weight_map, constraints=self.constraints)

        now = datetime.now(timezone.utc)
        for member in self.members:
            if member.strategy_id == normalized_id:
                if abs(member.weight - target_weight) <= 1e-9:
                    return
                member.weight = target_weight
                member.updated_at = now
                self._touch()
                return

        self.members.append(
            PortfolioMember(
                strategy_id=normalized_id,
                weight=target_weight,
                created_at=now,
                updated_at=now,
            )
        )
        self._touch()

    def remove_member(self, *, strategy_id: str) -> None:
        normalized_id = str(strategy_id).strip()
        new_members = [member for member in self.members if member.strategy_id != normalized_id]
        if len(new_members) == len(self.members):
            raise PortfolioMemberNotFoundError(f"member not found: {normalized_id}")
        self.members = new_members
        self._touch()

    def validate_target_weights(self, *, target_weights: dict[str, Any]) -> dict[str, float]:
        if not isinstance(target_weights, dict):
            raise InvalidPortfolioWeightsError("targetWeights must be an object")

        member_ids = {member.strategy_id for member in self.members}
        normalized: dict[str, float] = {}
        for strategy_id, raw_weight in target_weights.items():
            sid = str(strategy_id).strip()
            if sid not in member_ids:
                raise InvalidPortfolioWeightsError(f"unknown member strategy: {sid}")
            normalized[sid] = _normalize_weight(raw_weight)

        if not normalized:
            normalized = {member.strategy_id: member.weight for member in self.members}

        _validate_weights(weight_map=normalized, constraints=self.constraints)
        return normalized

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "name": self.name,
            "status": self.status,
            "version": self.version,
            "constraints": {
                "maxTotalWeight": round(float(self.constraints["maxTotalWeight"]), 6),
                "maxSingleWeight": round(float(self.constraints["maxSingleWeight"]), 6),
            },
            "totalWeight": round(self.total_weight, 6),
            "members": [member.to_dict() for member in self.members],
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


def _normalize_weight(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidPortfolioWeightsError("weight must be a number")

    weight = float(value)
    if weight <= 0:
        raise InvalidPortfolioWeightsError("weight must be > 0")
    return weight


def _normalize_constraints(constraints: dict[str, Any] | None) -> dict[str, float]:
    if constraints is None or constraints == {}:
        return {
            "maxTotalWeight": 1.0,
            "maxSingleWeight": 1.0,
        }

    if not isinstance(constraints, dict):
        raise InvalidPortfolioConstraintsError("constraints must be an object")

    max_total_raw = constraints.get("maxTotalWeight", 1.0)
    max_single_raw = constraints.get("maxSingleWeight", 1.0)

    if isinstance(max_total_raw, bool) or not isinstance(max_total_raw, (int, float)):
        raise InvalidPortfolioConstraintsError("constraints.maxTotalWeight must be a number")
    if isinstance(max_single_raw, bool) or not isinstance(max_single_raw, (int, float)):
        raise InvalidPortfolioConstraintsError("constraints.maxSingleWeight must be a number")

    max_total = float(max_total_raw)
    max_single = float(max_single_raw)

    if max_total <= 0:
        raise InvalidPortfolioConstraintsError("constraints.maxTotalWeight must be > 0")
    if max_single <= 0:
        raise InvalidPortfolioConstraintsError("constraints.maxSingleWeight must be > 0")
    if max_single > max_total:
        raise InvalidPortfolioConstraintsError("constraints.maxSingleWeight must be <= maxTotalWeight")

    return {
        "maxTotalWeight": max_total,
        "maxSingleWeight": max_single,
    }


def _validate_weights(*, weight_map: dict[str, float], constraints: dict[str, float]) -> None:
    max_total = float(constraints["maxTotalWeight"])
    max_single = float(constraints["maxSingleWeight"])

    total = 0.0
    for strategy_id, weight in weight_map.items():
        if weight <= 0:
            raise InvalidPortfolioWeightsError(f"weight must be > 0: {strategy_id}")
        if weight > max_single + 1e-9:
            raise InvalidPortfolioWeightsError(
                f"weight exceeds maxSingleWeight: {strategy_id}"
            )
        total += float(weight)

    if total > max_total + 1e-9:
        raise InvalidPortfolioWeightsError("total weight exceeds maxTotalWeight")


def _safe_float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _resolve_metrics(strategy_metrics: dict[str, dict[str, Any]], strategy_id: str) -> dict[str, Any]:
    value = strategy_metrics.get(strategy_id)
    if isinstance(value, dict):
        return value
    return {}


def build_portfolio_read_model(
    *,
    portfolio: Portfolio,
    strategy_metrics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    weighted_average_pnl = 0.0
    weighted_max_drawdown = 0.0

    member_items: list[dict[str, Any]] = []
    for member in portfolio.members:
        metrics = _resolve_metrics(strategy_metrics, member.strategy_id)
        average_pnl = _safe_float(metrics.get("averagePnl"))
        max_drawdown = _safe_float(metrics.get("maxDrawdown"))

        weighted_average_pnl += member.weight * average_pnl
        weighted_max_drawdown += member.weight * max_drawdown

        member_items.append(
            {
                "strategyId": member.strategy_id,
                "weight": round(member.weight, 6),
                "metrics": {
                    "averagePnl": round(average_pnl, 6),
                    "maxDrawdown": round(max_drawdown, 6),
                },
            }
        )

    member_count = len(member_items)
    correlation_base = 0.15 + 0.05 * max(0, member_count - 1)
    average_correlation = min(0.95, max(0.0, correlation_base))

    return {
        "portfolioId": portfolio.id,
        "portfolioName": portfolio.name,
        "status": portfolio.status,
        "version": portfolio.version,
        "memberCount": member_count,
        "members": member_items,
        "performanceSummary": {
            "weightedAveragePnl": round(weighted_average_pnl, 6),
            "weightedMaxDrawdown": round(weighted_max_drawdown, 6),
            "totalWeight": round(portfolio.total_weight, 6),
        },
        "correlationSummary": {
            "averageCorrelation": round(average_correlation, 6),
            "dispersion": round(1.0 - average_correlation, 6),
        },
    }


def _build_auto_target_weights(*, portfolio: Portfolio, strategy_metrics: dict[str, dict[str, Any]]) -> dict[str, float]:
    if not portfolio.members:
        return {}

    raw_scores: dict[str, float] = {}
    for member in portfolio.members:
        metrics = _resolve_metrics(strategy_metrics, member.strategy_id)
        average_pnl = _safe_float(metrics.get("averagePnl"))
        max_drawdown = abs(_safe_float(metrics.get("maxDrawdown")))
        score = max(0.0001, 1.0 + average_pnl - 2.5 * max_drawdown)
        raw_scores[member.strategy_id] = score

    score_total = sum(raw_scores.values())
    if score_total <= 0:
        score_total = float(len(raw_scores))
        raw_scores = {key: 1.0 for key in raw_scores}

    max_total = float(portfolio.constraints["maxTotalWeight"])
    max_single = float(portfolio.constraints["maxSingleWeight"])

    normalized: dict[str, float] = {}
    for strategy_id, score in raw_scores.items():
        normalized[strategy_id] = min(max_single, max_total * score / score_total)

    used = sum(normalized.values())
    if used < max_total - 1e-9:
        remain = max_total - used
        for strategy_id in sorted(normalized.keys()):
            room = max(0.0, max_single - normalized[strategy_id])
            delta = min(room, remain)
            normalized[strategy_id] += delta
            remain -= delta
            if remain <= 1e-9:
                break

    portfolio.validate_target_weights(target_weights=normalized)
    return normalized


def build_portfolio_rebalance_result(
    *,
    portfolio: Portfolio,
    strategy_metrics: dict[str, dict[str, Any]],
    target_weights: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if target_weights is not None and target_weights != {}:
        normalized_target = portfolio.validate_target_weights(target_weights=target_weights)
    else:
        normalized_target = _build_auto_target_weights(portfolio=portfolio, strategy_metrics=strategy_metrics)

    current_weights = {member.strategy_id: member.weight for member in portfolio.members}
    adjustments: list[dict[str, Any]] = []
    for strategy_id in sorted(normalized_target.keys()):
        from_weight = float(current_weights.get(strategy_id, 0.0))
        to_weight = float(normalized_target[strategy_id])
        adjustments.append(
            {
                "strategyId": strategy_id,
                "fromWeight": round(from_weight, 6),
                "toWeight": round(to_weight, 6),
                "delta": round(to_weight - from_weight, 6),
            }
        )

    concentration = 0.0
    if normalized_target:
        concentration = max(normalized_target.values())

    return {
        "portfolioId": portfolio.id,
        "version": portfolio.version,
        "targetWeights": {key: round(value, 6) for key, value in normalized_target.items()},
        "adjustments": adjustments,
        "riskSummary": {
            "concentration": round(concentration, 6),
            "totalTargetWeight": round(sum(normalized_target.values()), 6),
            "maxAllowedWeight": round(float(portfolio.constraints["maxSingleWeight"]), 6),
        },
    }


def build_portfolio_evaluation_result(
    *,
    portfolio: Portfolio,
    strategy_metrics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    read_model = build_portfolio_read_model(portfolio=portfolio, strategy_metrics=strategy_metrics)

    performance = read_model["performanceSummary"]
    risk_score = max(0.0, float(performance["weightedMaxDrawdown"]))

    return {
        "portfolioId": portfolio.id,
        "version": portfolio.version,
        "performanceSummary": dict(performance),
        "correlationSummary": dict(read_model["correlationSummary"]),
        "riskSummary": {
            "riskScore": round(risk_score, 6),
            "status": "ok" if risk_score <= 0.3 else "warn",
        },
    }


__all__ = [
    "InvalidPortfolioConstraintsError",
    "InvalidPortfolioWeightsError",
    "InvalidPortfolioTransitionError",
    "PortfolioMemberNotFoundError",
    "PortfolioMember",
    "Portfolio",
    "build_portfolio_read_model",
    "build_portfolio_rebalance_result",
    "build_portfolio_evaluation_result",
]
