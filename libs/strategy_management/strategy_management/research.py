"""策略研究领域模型与读模型转换。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


_ALLOWED_OPTIMIZATION_DIRECTIONS = {"maximize", "minimize"}
_ALLOWED_QUERY_STATUSES = {"succeeded", "failed", "cancelled"}


class InvalidResearchParameterSpaceError(ValueError):
    """研究参数空间非法。"""


class InvalidResearchStatusFilterError(ValueError):
    """研究结果状态过滤条件非法。"""


@dataclass(frozen=True)
class OptimizationObjective:
    metric: str
    direction: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "OptimizationObjective":
        if payload is None or payload == {}:
            return cls(metric="averagePnl", direction="maximize")

        if not isinstance(payload, dict):
            raise InvalidResearchParameterSpaceError("objective must be an object")

        metric_raw = payload.get("metric", "averagePnl")
        direction_raw = payload.get("direction", "maximize")

        metric = str(metric_raw).strip()
        direction = str(direction_raw).strip().lower()

        if not metric:
            raise InvalidResearchParameterSpaceError("objective.metric is required")
        if direction not in _ALLOWED_OPTIMIZATION_DIRECTIONS:
            raise InvalidResearchParameterSpaceError("objective.direction must be maximize or minimize")

        return cls(metric=metric, direction=direction)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class OptimizationParameterRange:
    minimum: float
    maximum: float
    step: float

    @staticmethod
    def _to_number(*, field_name: str, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidResearchParameterSpaceError(f"{field_name} must be a number")
        return float(value)

    @classmethod
    def from_payload(cls, *, parameter_name: str, payload: dict[str, Any]) -> "OptimizationParameterRange":
        if not isinstance(payload, dict):
            raise InvalidResearchParameterSpaceError(f"parameterSpace.{parameter_name} must be an object")

        minimum = cls._to_number(field_name=f"parameterSpace.{parameter_name}.min", value=payload.get("min"))
        maximum = cls._to_number(field_name=f"parameterSpace.{parameter_name}.max", value=payload.get("max"))
        step = cls._to_number(field_name=f"parameterSpace.{parameter_name}.step", value=payload.get("step"))

        if maximum < minimum:
            raise InvalidResearchParameterSpaceError(f"parameterSpace.{parameter_name}.max must be >= min")
        if step <= 0:
            raise InvalidResearchParameterSpaceError(f"parameterSpace.{parameter_name}.step must be > 0")

        return cls(minimum=minimum, maximum=maximum, step=step)

    def to_dict(self) -> dict[str, float]:
        return {
            "min": self.minimum,
            "max": self.maximum,
            "step": self.step,
        }


@dataclass(frozen=True)
class OptimizationResult:
    strategy_id: str
    template: str
    generated_at: str
    objective: dict[str, Any]
    parameter_space: dict[str, dict[str, float]]
    constraints: dict[str, Any]
    metrics: dict[str, Any]
    score: float
    suggestions: list[dict[str, Any]]
    version: str = "v2"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "strategyId": self.strategy_id,
            "template": self.template,
            "generatedAt": self.generated_at,
            "objective": dict(self.objective),
            "parameterSpace": {
                name: dict(value)
                for name, value in self.parameter_space.items()
            },
            "constraints": dict(self.constraints),
            "metrics": dict(self.metrics),
            "score": self.score,
            "suggestions": [dict(item) for item in self.suggestions],
        }


@dataclass(frozen=True)
class ResearchRun:
    task_id: str
    task_type: str
    strategy_id: str
    status: str
    created_at: str
    updated_at: str
    finished_at: str | None
    optimization_result: dict[str, Any] | None
    error: dict[str, Any] | None

    @classmethod
    def from_job(cls, job: Any) -> "ResearchRun":
        raw_result = getattr(job, "result", None)
        optimization_result: dict[str, Any] | None = None
        if isinstance(raw_result, dict):
            nested = raw_result.get("optimizationResult")
            if isinstance(nested, dict):
                optimization_result = dict(nested)
            elif raw_result:
                optimization_result = dict(raw_result)

        error: dict[str, Any] | None = None
        if getattr(job, "status", None) == "failed":
            error = {
                "code": getattr(job, "error_code", None),
                "message": getattr(job, "error_message", None),
            }

        return cls(
            task_id=str(getattr(job, "id")),
            task_type=str(getattr(job, "task_type")),
            strategy_id=str(getattr(job, "payload", {}).get("strategyId", "")),
            status=str(getattr(job, "status")),
            created_at=_to_iso(getattr(job, "created_at", None)),
            updated_at=_to_iso(getattr(job, "updated_at", None)),
            finished_at=_to_iso(getattr(job, "finished_at", None)),
            optimization_result=optimization_result,
            error=error,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "taskId": self.task_id,
            "taskType": self.task_type,
            "strategyId": self.strategy_id,
            "status": self.status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "finishedAt": self.finished_at,
            "optimizationResult": dict(self.optimization_result) if isinstance(self.optimization_result, dict) else None,
            "error": dict(self.error) if isinstance(self.error, dict) else None,
        }


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _normalize_parameter_space(payload: dict[str, Any] | None) -> dict[str, dict[str, float]]:
    if payload is None or payload == {}:
        return {}

    if not isinstance(payload, dict):
        raise InvalidResearchParameterSpaceError("parameterSpace must be an object")

    normalized: dict[str, dict[str, float]] = {}
    for parameter_name, raw_range in payload.items():
        name = str(parameter_name).strip()
        if not name:
            raise InvalidResearchParameterSpaceError("parameterSpace key cannot be empty")

        parsed = OptimizationParameterRange.from_payload(
            parameter_name=name,
            payload=raw_range,
        )
        normalized[name] = parsed.to_dict()

    return normalized


def _normalize_constraints(payload: dict[str, Any] | None) -> dict[str, Any]:
    if payload is None or payload == {}:
        return {}

    if not isinstance(payload, dict):
        raise InvalidResearchParameterSpaceError("constraints must be an object")

    return dict(payload)


def _safe_float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def build_optimization_result(
    *,
    strategy_id: str,
    template: str,
    metrics: dict[str, Any],
    objective: dict[str, Any] | None,
    parameter_space: dict[str, Any] | None,
    constraints: dict[str, Any] | None,
) -> dict[str, Any]:
    objective_value = OptimizationObjective.from_payload(objective)
    parameter_space_value = _normalize_parameter_space(parameter_space)
    constraints_value = _normalize_constraints(constraints)

    metric_value = _safe_float(metrics.get(objective_value.metric))
    score = metric_value if objective_value.direction == "maximize" else -metric_value

    suggestion_message = "保持当前参数"
    if score < 0:
        suggestion_message = "降低风险敞口"

    generated_at = datetime.now(timezone.utc).isoformat()
    result = OptimizationResult(
        strategy_id=strategy_id,
        template=template,
        generated_at=generated_at,
        objective=objective_value.to_dict(),
        parameter_space=parameter_space_value,
        constraints=constraints_value,
        metrics=dict(metrics),
        score=round(score, 6),
        suggestions=[
            {
                "code": "OPTIMIZE_PNL",
                "message": suggestion_message,
                "metric": objective_value.metric,
                "direction": objective_value.direction,
            }
        ],
    )
    return result.to_dict()


def _normalize_status_filter(status: str | None) -> str | None:
    if status is None:
        return None

    normalized = status.strip().lower()
    if normalized == "":
        return None

    if normalized not in _ALLOWED_QUERY_STATUSES:
        raise InvalidResearchStatusFilterError("status must be one of succeeded/failed/cancelled")

    return normalized


def build_research_results_listing(
    *,
    jobs: list[Any],
    strategy_id: str,
    status: str | None,
    limit: int,
) -> dict[str, Any]:
    status_filter = _normalize_status_filter(status)
    safe_limit = max(1, int(limit))

    filtered: list[Any] = []
    for job in jobs:
        if str(getattr(job, "task_type", "")) != "strategy_optimization_suggest":
            continue

        payload = getattr(job, "payload", {})
        if str(payload.get("strategyId", "")) != strategy_id:
            continue

        if status_filter is not None and str(getattr(job, "status", "")) != status_filter:
            continue

        filtered.append(job)

    filtered.sort(
        key=lambda item: (
            getattr(item, "created_at", None) is not None,
            getattr(item, "created_at", None),
        ),
        reverse=True,
    )

    items = [ResearchRun.from_job(item).to_dict() for item in filtered[:safe_limit]]

    return {
        "items": items,
        "total": len(filtered),
    }


__all__ = [
    "InvalidResearchParameterSpaceError",
    "InvalidResearchStatusFilterError",
    "OptimizationObjective",
    "OptimizationParameterRange",
    "OptimizationResult",
    "ResearchRun",
    "build_optimization_result",
    "build_research_results_listing",
]
