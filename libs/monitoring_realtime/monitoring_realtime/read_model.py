"""monitoring-realtime Read Model。

该模块用于承载跨上下文聚合查询（运营摘要）的计算逻辑，保持：
- 框架无关（不依赖 FastAPI / WebSocket）
- 可复算（可从 snapshot JSON 复算）

目标：REST/WS/CLI 共享同一摘要口径，避免语义漂移。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

SourceFn = Callable[[str], list[dict[str, Any]]]


def _item_user_id(item: dict[str, Any]) -> str | None:
    if "userId" in item:
        value = item.get("userId")
        return str(value) if value is not None else None
    if "user_id" in item:
        value = item.get("user_id")
        return str(value) if value is not None else None
    return None


def _status_text(item: dict[str, Any]) -> str:
    raw = item.get("status")
    return str(raw).strip().lower() if raw is not None else ""


def _filter_owned_items(*, user_id: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        owner = _item_user_id(item)
        if owner is not None and owner != user_id:
            continue
        result.append(item)
    return result


def _count_statuses(items: list[dict[str, Any]], statuses: set[str]) -> int:
    return sum(1 for item in items if _status_text(item) in statuses)


def build_operational_summary(
    *,
    user_id: str,
    account_source: SourceFn,
    strategy_source: SourceFn,
    backtest_source: SourceFn,
    task_source: SourceFn,
    signal_source: SourceFn,
    alert_source: SourceFn,
    latency_ms: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    """构建监控运营摘要（v2）。

    说明：该摘要属于监控上下文的显式 Read Model。输入通过 source 注入，
    以隔离其他 bounded context 的存储/实现细节。
    """

    degraded_reasons: list[str] = []
    source_status: dict[str, str] = {}

    def _collect(name: str, source: SourceFn) -> list[dict[str, Any]]:
        try:
            raw = source(user_id)
        except Exception:  # noqa: BLE001
            source_status[name] = "degraded"
            degraded_reasons.append(f"{name}_unavailable")
            return []

        if not isinstance(raw, list):
            source_status[name] = "degraded"
            degraded_reasons.append(f"{name}_invalid")
            return []

        source_status[name] = "ok"
        return _filter_owned_items(
            user_id=user_id,
            items=[item for item in raw if isinstance(item, dict)],
        )

    user_accounts = _collect("accounts", account_source)
    user_strategies = _collect("strategies", strategy_source)
    user_backtests = _collect("backtests", backtest_source)
    user_tasks = _collect("tasks", task_source)
    user_signals = _collect("signals", signal_source)
    user_alerts = _collect("alerts", alert_source)

    active_accounts = [
        item
        for item in user_accounts
        if bool(
            item.get(
                "isActive",
                item.get(
                    "is_active",
                    _status_text(item)
                    not in {"disabled", "inactive", "closed", "archived"},
                ),
            )
        )
    ]
    active_strategies = [
        item
        for item in user_strategies
        if _status_text(item) in {"active", "running", "enabled", "live"}
    ]

    open_alerts = [item for item in user_alerts if _status_text(item) != "resolved"]
    critical_alerts = [
        item
        for item in open_alerts
        if str(item.get("severity", "")).strip().lower() in {"critical", "high"}
    ]

    generated_at = (now or datetime.now(timezone.utc)).isoformat()

    summary = {
        "type": "monitor.summary",
        "generatedAt": generated_at,
        "metadata": {
            "version": "v2",
            "latencyMs": max(0, int(latency_ms)),
            "sources": source_status,
        },
        "accounts": {
            "total": len(user_accounts),
            "active": len(active_accounts),
        },
        "strategies": {
            "total": len(user_strategies),
            "active": len(active_strategies),
        },
        "backtests": {
            "total": len(user_backtests),
            "pending": _count_statuses(user_backtests, {"pending", "queued"}),
            "running": _count_statuses(user_backtests, {"running"}),
            "completed": _count_statuses(user_backtests, {"completed", "succeeded"}),
            "failed": _count_statuses(user_backtests, {"failed"}),
            "cancelled": _count_statuses(user_backtests, {"cancelled", "canceled"}),
        },
        "tasks": {
            "total": len(user_tasks),
            "queued": _count_statuses(user_tasks, {"queued", "pending"}),
            "running": _count_statuses(user_tasks, {"running"}),
            "succeeded": _count_statuses(user_tasks, {"succeeded", "completed"}),
            "failed": _count_statuses(user_tasks, {"failed"}),
            "cancelled": _count_statuses(user_tasks, {"cancelled", "canceled"}),
        },
        "signals": {
            "total": len(user_signals),
            "pending": _count_statuses(user_signals, {"pending"}),
            "expired": _count_statuses(user_signals, {"expired"}),
        },
        "alerts": {
            "total": len(user_alerts),
            "open": len(open_alerts),
            "critical": len(critical_alerts),
        },
        "degraded": {
            "enabled": len(degraded_reasons) > 0,
            "reasons": degraded_reasons,
        },
    }

    summary["isEmpty"] = (
        summary["accounts"]["total"]
        + summary["strategies"]["total"]
        + summary["backtests"]["total"]
        + summary["tasks"]["total"]
        + summary["signals"]["total"]
        + summary["alerts"]["total"]
    ) == 0

    return summary


def build_operational_summary_from_snapshot(
    *,
    user_id: str,
    snapshot: Mapping[str, Any],
    latency_ms: int = 0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """从 JSON snapshot 复算运营摘要。

    snapshot 为可序列化 dict，推荐包含：
    accounts/strategies/backtests/tasks/signals/alerts。
    """

    def _get_list(key: str) -> list[dict[str, Any]]:
        raw = snapshot.get(key, [])
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    return build_operational_summary(
        user_id=user_id,
        account_source=lambda _uid: _get_list("accounts"),
        strategy_source=lambda _uid: _get_list("strategies"),
        backtest_source=lambda _uid: _get_list("backtests"),
        task_source=lambda _uid: _get_list("tasks"),
        signal_source=lambda _uid: _get_list("signals"),
        alert_source=lambda _uid: _get_list("alerts"),
        latency_ms=latency_ms,
        now=now,
    )
