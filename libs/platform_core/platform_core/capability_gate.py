"""能力门禁评估逻辑。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CapabilityGateInput:
    wave: str
    capabilities: list[dict[str, Any]]
    post_cutover_metrics: dict[str, Any]
    thresholds: dict[str, Any]


def parse_gate_input(payload: dict[str, Any]) -> CapabilityGateInput:
    wave = str(payload.get("wave") or "unknown-wave")
    capabilities = payload.get("capabilities") or []
    if not isinstance(capabilities, list):
        raise ValueError("capabilities must be a list")

    post_cutover_metrics = payload.get("postCutoverMetrics") or {}
    if not isinstance(post_cutover_metrics, dict):
        raise ValueError("postCutoverMetrics must be an object")

    thresholds = payload.get("thresholds") or {}
    if not isinstance(thresholds, dict):
        raise ValueError("thresholds must be an object")

    merged_thresholds = {
        "maxErrorRate": float(thresholds.get("maxErrorRate", 0.05)),
        "maxP95LatencyMs": int(thresholds.get("maxP95LatencyMs", 800)),
        "maxQueueBacklog": int(thresholds.get("maxQueueBacklog", 200)),
    }

    return CapabilityGateInput(
        wave=wave,
        capabilities=capabilities,
        post_cutover_metrics=post_cutover_metrics,
        thresholds=merged_thresholds,
    )


def evaluate_gate(payload: dict[str, Any]) -> dict[str, Any]:
    gate_input = parse_gate_input(payload)

    blockers: list[str] = []
    passed_count = 0
    failed_count = 0
    critical_failed = 0

    for item in gate_input.capabilities:
        capability_id = str(item.get("id") or "unknown")
        passed = bool(item.get("passed", False))
        critical = bool(item.get("critical", False))

        if passed:
            passed_count += 1
            continue

        failed_count += 1
        if critical:
            critical_failed += 1
            blockers.append(f"critical_capability_missing:{capability_id}")
        else:
            blockers.append(f"capability_missing:{capability_id}")

    metrics = gate_input.post_cutover_metrics
    error_rate = float(metrics.get("errorRate", 0.0))
    p95_latency = int(metrics.get("p95LatencyMs", 0))
    queue_backlog = int(metrics.get("queueBacklog", 0))
    data_leakage = bool(metrics.get("dataLeakage", False))

    if error_rate > gate_input.thresholds["maxErrorRate"]:
        blockers.append("metric_threshold_breach:errorRate")

    if p95_latency > gate_input.thresholds["maxP95LatencyMs"]:
        blockers.append("metric_threshold_breach:p95LatencyMs")

    if queue_backlog > gate_input.thresholds["maxQueueBacklog"]:
        blockers.append("metric_threshold_breach:queueBacklog")

    if data_leakage:
        blockers.append("security_breach:dataLeakage")

    allowed = len(blockers) == 0
    rollback_required = (not allowed) and (
        critical_failed > 0
        or data_leakage
        or error_rate > gate_input.thresholds["maxErrorRate"]
    )

    return {
        "wave": gate_input.wave,
        "allowed": allowed,
        "rollbackRequired": rollback_required,
        "blockers": blockers,
        "summary": {
            "total": len(gate_input.capabilities),
            "passed": passed_count,
            "failed": failed_count,
            "criticalFailed": critical_failed,
        },
        "metrics": {
            "errorRate": error_rate,
            "p95LatencyMs": p95_latency,
            "queueBacklog": queue_backlog,
            "dataLeakage": data_leakage,
        },
        "thresholds": gate_input.thresholds,
    }
