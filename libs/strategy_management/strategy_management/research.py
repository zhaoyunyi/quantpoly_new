"""策略研究领域模型与读模型转换。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from time import perf_counter
from typing import Any


_ALLOWED_OPTIMIZATION_DIRECTIONS = {"maximize", "minimize"}
_ALLOWED_OPTIMIZATION_METHODS = {"grid", "bayesian"}
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
class OptimizationBudget:
    max_trials: int
    max_duration_seconds: float
    early_stop_score: float | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "OptimizationBudget":
        if payload is None or payload == {}:
            return cls(max_trials=20, max_duration_seconds=60.0, early_stop_score=None)

        if not isinstance(payload, dict):
            raise InvalidResearchParameterSpaceError("budget must be an object")

        max_trials_raw = payload.get("maxTrials", 20)
        max_duration_raw = payload.get("maxDurationSeconds", 60)
        early_stop_raw = payload.get("earlyStopScore", None)

        if isinstance(max_trials_raw, bool) or not isinstance(max_trials_raw, int):
            raise InvalidResearchParameterSpaceError("budget.maxTrials must be an integer")
        if max_trials_raw <= 0:
            raise InvalidResearchParameterSpaceError("budget.maxTrials must be > 0")

        if isinstance(max_duration_raw, bool) or not isinstance(max_duration_raw, (int, float)):
            raise InvalidResearchParameterSpaceError("budget.maxDurationSeconds must be a number")
        max_duration_seconds = float(max_duration_raw)
        if max_duration_seconds <= 0:
            raise InvalidResearchParameterSpaceError("budget.maxDurationSeconds must be > 0")

        early_stop_score: float | None = None
        if early_stop_raw is not None:
            if isinstance(early_stop_raw, bool) or not isinstance(early_stop_raw, (int, float)):
                raise InvalidResearchParameterSpaceError("budget.earlyStopScore must be a number")
            early_stop_score = float(early_stop_raw)

        return cls(
            max_trials=max_trials_raw,
            max_duration_seconds=max_duration_seconds,
            early_stop_score=early_stop_score,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "maxTrials": self.max_trials,
            "maxDurationSeconds": self.max_duration_seconds,
            "earlyStopScore": self.early_stop_score,
        }


@dataclass(frozen=True)
class OptimizationResult:
    strategy_id: str
    template: str
    generated_at: str
    method: str
    objective: dict[str, Any]
    parameter_space: dict[str, dict[str, float]]
    constraints: dict[str, Any]
    budget: dict[str, Any]
    trials: list[dict[str, Any]]
    best_candidate: dict[str, Any] | None
    budget_usage: dict[str, Any]
    convergence: dict[str, Any]
    metrics: dict[str, Any]
    score: float
    suggestions: list[dict[str, Any]]
    version: str = "v3"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "strategyId": self.strategy_id,
            "template": self.template,
            "generatedAt": self.generated_at,
            "method": self.method,
            "objective": dict(self.objective),
            "parameterSpace": {
                name: dict(value)
                for name, value in self.parameter_space.items()
            },
            "constraints": dict(self.constraints),
            "budget": dict(self.budget),
            "trials": [dict(item) for item in self.trials],
            "bestCandidate": dict(self.best_candidate) if isinstance(self.best_candidate, dict) else None,
            "budgetUsage": dict(self.budget_usage),
            "convergence": dict(self.convergence),
            "metrics": dict(self.metrics),
            "score": self.score,
            "suggestions": [dict(item) for item in self.suggestions],
        }


@dataclass(frozen=True)
class ResearchRun:
    task_id: str
    task_type: str
    strategy_id: str
    method: str | None
    version: str | None
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

        payload = getattr(job, "payload", {})
        resolved_method = _resolve_job_method(payload=payload, optimization_result=optimization_result)
        resolved_version = _resolve_job_version(optimization_result=optimization_result)

        error: dict[str, Any] | None = None
        if getattr(job, "status", None) == "failed":
            error = {
                "code": getattr(job, "error_code", None),
                "message": getattr(job, "error_message", None),
            }

        return cls(
            task_id=str(getattr(job, "id")),
            task_type=str(getattr(job, "task_type")),
            strategy_id=str(payload.get("strategyId", "")),
            method=resolved_method,
            version=resolved_version,
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
            "method": self.method,
            "version": self.version,
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


def _normalize_method(method: str | None) -> str:
    if method is None:
        return "grid"

    normalized = str(method).strip().lower()
    if normalized == "":
        return "grid"
    if normalized not in _ALLOWED_OPTIMIZATION_METHODS:
        raise InvalidResearchParameterSpaceError("method must be one of grid/bayesian")
    return normalized


def _safe_float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _build_axis_values(parameter_range: dict[str, float]) -> list[float]:
    minimum = float(parameter_range["min"])
    maximum = float(parameter_range["max"])
    step = float(parameter_range["step"])

    values: list[float] = []
    cursor = minimum
    epsilon = step / 1_000_000

    while cursor <= maximum + epsilon:
        values.append(round(cursor, 6))
        cursor += step

    if not values:
        values.append(round(minimum, 6))

    if values[-1] < maximum - epsilon:
        values.append(round(maximum, 6))

    deduplicated: list[float] = []
    for value in values:
        if not deduplicated or abs(deduplicated[-1] - value) > 1e-6:
            deduplicated.append(value)

    return deduplicated


def _to_number_literal(value: float) -> int | float:
    rounded_int = int(round(value))
    if abs(value - rounded_int) < 1e-9:
        return rounded_int
    return round(value, 6)


def _build_parameter_axes(parameter_space: dict[str, dict[str, float]]) -> list[tuple[str, list[float]]]:
    axes: list[tuple[str, list[float]]] = []
    for name in sorted(parameter_space.keys()):
        values = _build_axis_values(parameter_space[name])
        axes.append((name, values))
    return axes


def _estimate_total_candidates(axes: list[tuple[str, list[float]]]) -> int:
    if not axes:
        return 1

    total = 1
    for _, values in axes:
        total *= len(values)
    return total


def _iter_grid_candidates(axes: list[tuple[str, list[float]]]):
    if not axes:
        yield {}
        return

    names = [name for name, _ in axes]
    value_lists = [values for _, values in axes]
    for values in product(*value_lists):
        yield {name: _to_number_literal(float(value)) for name, value in zip(names, values, strict=True)}


def _iter_bayesian_candidates(axes: list[tuple[str, list[float]]]):
    if not axes:
        yield {}
        return

    names = [name for name, _ in axes]
    value_lists = [values for _, values in axes]
    center_indexes = [len(values) // 2 for values in value_lists]
    index_ranges = [range(len(values)) for values in value_lists]

    ranked_candidates: list[tuple[int, tuple[int, ...]]] = []
    for index_tuple in product(*index_ranges):
        distance = sum(
            abs(index_value - center_index)
            for index_value, center_index in zip(index_tuple, center_indexes, strict=True)
        )
        ranked_candidates.append((distance, index_tuple))

    ranked_candidates.sort(key=lambda item: (item[0], item[1]))

    for _, index_tuple in ranked_candidates:
        yield {
            name: _to_number_literal(float(values[index]))
            for name, values, index in zip(names, value_lists, index_tuple, strict=True)
        }


def _resolve_job_method(*, payload: dict[str, Any], optimization_result: dict[str, Any] | None) -> str | None:
    if isinstance(optimization_result, dict):
        method = optimization_result.get("method")
        if isinstance(method, str) and method.strip():
            return method.strip().lower()

    payload_method = payload.get("method") if isinstance(payload, dict) else None
    if isinstance(payload_method, str) and payload_method.strip():
        return payload_method.strip().lower()

    return "grid"


def _resolve_job_version(*, optimization_result: dict[str, Any] | None) -> str | None:
    if isinstance(optimization_result, dict):
        version = optimization_result.get("version")
        if isinstance(version, str) and version.strip():
            return version.strip()
    return None


def _evaluate_trial(
    *,
    method: str,
    index: int,
    candidate: dict[str, int | float],
    metrics: dict[str, Any],
    objective: OptimizationObjective,
    parameter_space: dict[str, dict[str, float]],
    constraints: dict[str, Any],
) -> dict[str, Any]:
    metric_value = _safe_float(metrics.get(objective.metric))

    adjustment = 0.0
    for order, parameter_name in enumerate(sorted(parameter_space.keys()), start=1):
        parameter_range = parameter_space[parameter_name]
        minimum = float(parameter_range["min"])
        maximum = float(parameter_range["max"])
        span = max(maximum - minimum, 1e-6)

        raw_value = _safe_float(candidate.get(parameter_name, minimum))
        normalized = (raw_value - minimum) / span - 0.5
        adjustment += normalized / float(order)

    weighted_metric = metric_value + (abs(metric_value) + 1.0) * adjustment * 0.2

    violations: list[str] = []
    max_drawdown_limit = constraints.get("maxDrawdown") if isinstance(constraints, dict) else None
    if isinstance(max_drawdown_limit, (int, float)) and not isinstance(max_drawdown_limit, bool):
        measured_drawdown = _safe_float(metrics.get("maxDrawdown"))
        if measured_drawdown > float(max_drawdown_limit):
            violations.append("maxDrawdown")

    score = weighted_metric if objective.direction == "maximize" else -weighted_metric
    if violations:
        score -= 1.0

    return {
        "trialId": f"trial-{index + 1}",
        "method": method,
        "parameters": dict(candidate),
        "metric": objective.metric,
        "score": round(score, 6),
        "feasible": len(violations) == 0,
        "violations": violations,
    }


def _build_trial_runner(
    *,
    method: str,
    axes: list[tuple[str, list[float]]],
):
    if method == "bayesian":
        return _iter_bayesian_candidates(axes)
    return _iter_grid_candidates(axes)


def build_optimization_result(
    *,
    strategy_id: str,
    template: str,
    metrics: dict[str, Any],
    objective: dict[str, Any] | None,
    parameter_space: dict[str, Any] | None,
    constraints: dict[str, Any] | None,
    method: str | None = None,
    budget: dict[str, Any] | None = None,
) -> dict[str, Any]:
    objective_value = OptimizationObjective.from_payload(objective)
    parameter_space_value = _normalize_parameter_space(parameter_space)
    constraints_value = _normalize_constraints(constraints)
    method_value = _normalize_method(method)
    budget_value = OptimizationBudget.from_payload(budget)

    axes = _build_parameter_axes(parameter_space_value)
    total_candidates = _estimate_total_candidates(axes)

    start_at = perf_counter()
    trials: list[dict[str, Any]] = []
    best_candidate: dict[str, Any] | None = None
    early_stop_reason = "parameter_space_exhausted"

    for candidate in _build_trial_runner(method=method_value, axes=axes):
        if len(trials) >= budget_value.max_trials:
            early_stop_reason = "max_trials_reached"
            break

        elapsed_seconds = perf_counter() - start_at
        if elapsed_seconds >= budget_value.max_duration_seconds:
            early_stop_reason = "max_duration_reached"
            break

        trial = _evaluate_trial(
            method=method_value,
            index=len(trials),
            candidate=candidate,
            metrics=metrics,
            objective=objective_value,
            parameter_space=parameter_space_value,
            constraints=constraints_value,
        )
        trials.append(trial)

        if best_candidate is None or float(trial["score"]) > float(best_candidate["score"]):
            best_candidate = {
                "trialId": trial["trialId"],
                "score": trial["score"],
                "parameters": dict(trial["parameters"]),
                "feasible": trial["feasible"],
            }

        if budget_value.early_stop_score is not None and float(trial["score"]) >= budget_value.early_stop_score:
            early_stop_reason = "early_stop_score_reached"
            break

    elapsed_ms = max(0, int((perf_counter() - start_at) * 1000))

    if not trials and early_stop_reason == "parameter_space_exhausted":
        early_stop_reason = "max_duration_reached"

    if best_candidate is None:
        best_candidate = {
            "trialId": "",
            "score": 0.0,
            "parameters": {},
            "feasible": False,
        }

    score = round(float(best_candidate["score"]), 6)

    suggestion_message = "保持当前参数"
    if score < 0:
        suggestion_message = "降低风险敞口"

    generated_at = datetime.now(timezone.utc).isoformat()
    result = OptimizationResult(
        strategy_id=strategy_id,
        template=template,
        generated_at=generated_at,
        method=method_value,
        objective=objective_value.to_dict(),
        parameter_space=parameter_space_value,
        constraints=constraints_value,
        budget=budget_value.to_dict(),
        trials=trials,
        best_candidate=best_candidate,
        budget_usage={
            "usedTrials": len(trials),
            "remainingTrials": max(0, budget_value.max_trials - len(trials)),
            "usedDurationMs": elapsed_ms,
            "maxTrials": budget_value.max_trials,
            "maxDurationSeconds": budget_value.max_duration_seconds,
            "totalCandidates": total_candidates,
        },
        convergence={
            "status": "converged" if early_stop_reason in {"early_stop_score_reached", "parameter_space_exhausted"} else "budget_exhausted",
            "earlyStopReason": early_stop_reason,
            "bestScore": score,
        },
        metrics=dict(metrics),
        score=score,
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


def _normalize_method_filter(method: str | None) -> str | None:
    if method is None:
        return None

    normalized = method.strip().lower()
    if normalized == "":
        return None

    if normalized not in _ALLOWED_OPTIMIZATION_METHODS:
        raise InvalidResearchParameterSpaceError("method must be one of grid/bayesian")

    return normalized


def _normalize_version_filter(version: str | None) -> str | None:
    if version is None:
        return None

    normalized = version.strip()
    if normalized == "":
        return None

    return normalized


def build_research_results_listing(
    *,
    jobs: list[Any],
    strategy_id: str,
    status: str | None,
    method: str | None = None,
    version: str | None = None,
    limit: int,
) -> dict[str, Any]:
    status_filter = _normalize_status_filter(status)
    method_filter = _normalize_method_filter(method)
    version_filter = _normalize_version_filter(version)
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

        optimization_result = None
        raw_result = getattr(job, "result", None)
        if isinstance(raw_result, dict):
            nested = raw_result.get("optimizationResult")
            if isinstance(nested, dict):
                optimization_result = nested
            elif raw_result:
                optimization_result = raw_result

        if method_filter is not None:
            job_method = _resolve_job_method(payload=payload, optimization_result=optimization_result)
            if job_method != method_filter:
                continue

        if version_filter is not None:
            job_version = _resolve_job_version(optimization_result=optimization_result)
            if job_version != version_filter:
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
