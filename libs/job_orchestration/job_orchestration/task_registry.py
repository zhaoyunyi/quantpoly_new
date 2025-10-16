"""job_orchestration 任务类型注册表。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskSlaPolicy:
    """任务 SLA Policy。

    说明：该 policy 用于运行时治理与可观测，不依赖具体执行器实现。
    第一阶段采用 taskType 维度的静态策略。
    """

    priority: int = 50
    timeout_seconds: int = 900
    max_retries: int = 0
    concurrency_limit: int = 1

    def to_payload(self) -> dict[str, object]:
        return {
            "priority": int(self.priority),
            "timeoutSeconds": int(self.timeout_seconds),
            "maxRetries": int(self.max_retries),
            "concurrencyLimit": int(self.concurrency_limit),
        }


@dataclass(frozen=True)
class TaskTypeDefinition:
    task_type: str
    domain: str
    schedulable: bool = True
    sla: TaskSlaPolicy = field(default_factory=TaskSlaPolicy)

    def to_payload(self) -> dict[str, object]:
        payload = {
            "taskType": self.task_type,
            "domain": self.domain,
            "schedulable": self.schedulable,
        }
        payload.update(self.sla.to_payload())
        return payload


_INTERACTIVE_SLA = TaskSlaPolicy(
    priority=100,
    timeout_seconds=1800,
    max_retries=1,
    concurrency_limit=1,
)
_BATCH_SLA = TaskSlaPolicy(
    priority=50,
    timeout_seconds=1800,
    max_retries=0,
    concurrency_limit=2,
)
_MAINTENANCE_SLA = TaskSlaPolicy(
    priority=10,
    timeout_seconds=900,
    max_retries=0,
    concurrency_limit=1,
)


_TASK_REGISTRY: tuple[TaskTypeDefinition, ...] = (
    TaskTypeDefinition(
        task_type="backtest_run",
        domain="backtest",
        sla=_INTERACTIVE_SLA,
    ),
    TaskTypeDefinition(
        task_type="market_data_fetch",
        domain="market-data",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="market_data_sync",
        domain="market-data",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="market_indicators_calculate",
        domain="market-data",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="risk_account_evaluate",
        domain="risk",
        sla=_INTERACTIVE_SLA,
    ),
    TaskTypeDefinition(
        task_type="risk_alert_cleanup",
        domain="risk",
        sla=_MAINTENANCE_SLA,
    ),
    TaskTypeDefinition(
        task_type="risk_alert_notify",
        domain="risk",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="risk_batch_check",
        domain="risk",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="risk_continuous_monitor",
        domain="risk",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="risk_report_generate",
        domain="risk",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="risk_snapshot_generate_account",
        domain="risk",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="risk_snapshot_generate_all",
        domain="risk",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="signal_batch_cancel",
        domain="signal",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="signal_batch_execute",
        domain="signal",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="signal_batch_generate",
        domain="signal",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="signal_batch_process",
        domain="signal",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="signal_cleanup_expired",
        domain="signal",
        sla=_MAINTENANCE_SLA,
    ),
    TaskTypeDefinition(
        task_type="signal_insights_generate",
        domain="signal",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="signal_performance_calculate",
        domain="signal",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="strategy_backtest_run",
        domain="strategy",
        sla=_INTERACTIVE_SLA,
    ),
    TaskTypeDefinition(
        task_type="strategy_batch_execute",
        domain="strategy",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="strategy_optimization_suggest",
        domain="strategy",
        sla=_INTERACTIVE_SLA,
    ),
    TaskTypeDefinition(
        task_type="strategy_performance_analyze",
        domain="strategy",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="portfolio_evaluate",
        domain="strategy",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="portfolio_rebalance",
        domain="strategy",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="trading_account_cleanup",
        domain="trading",
        sla=_MAINTENANCE_SLA,
    ),
    TaskTypeDefinition(
        task_type="trading_batch_execute",
        domain="trading",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="trading_daily_stats_calculate",
        domain="trading",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="trading_pending_process",
        domain="trading",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="trading_refresh_prices",
        domain="trading",
        sla=_BATCH_SLA,
    ),
    TaskTypeDefinition(
        task_type="trading_risk_monitor",
        domain="trading",
        sla=_BATCH_SLA,
    ),
)


def list_task_type_definitions() -> list[TaskTypeDefinition]:
    return sorted(_TASK_REGISTRY, key=lambda item: item.task_type)


def supported_task_types() -> set[str]:
    return {item.task_type for item in _TASK_REGISTRY}


def get_task_type_definition(task_type: str) -> TaskTypeDefinition | None:
    for definition in _TASK_REGISTRY:
        if definition.task_type == task_type:
            return definition
    return None
