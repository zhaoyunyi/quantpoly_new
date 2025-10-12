"""job_orchestration 任务类型注册表。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskTypeDefinition:
    task_type: str
    domain: str
    schedulable: bool = True

    def to_payload(self) -> dict[str, object]:
        return {
            "taskType": self.task_type,
            "domain": self.domain,
            "schedulable": self.schedulable,
        }


_TASK_REGISTRY: tuple[TaskTypeDefinition, ...] = (
    TaskTypeDefinition(
        task_type="backtest_run",
        domain="backtest",
    ),
    TaskTypeDefinition(
        task_type="market_data_fetch",
        domain="market-data",
    ),
    TaskTypeDefinition(
        task_type="market_data_sync",
        domain="market-data",
    ),
    TaskTypeDefinition(
        task_type="market_indicators_calculate",
        domain="market-data",
    ),
    TaskTypeDefinition(
        task_type="risk_account_evaluate",
        domain="risk",
    ),
    TaskTypeDefinition(
        task_type="risk_alert_cleanup",
        domain="risk",
    ),
    TaskTypeDefinition(
        task_type="risk_alert_notify",
        domain="risk",
    ),
    TaskTypeDefinition(
        task_type="risk_batch_check",
        domain="risk",
    ),
    TaskTypeDefinition(
        task_type="risk_continuous_monitor",
        domain="risk",
    ),
    TaskTypeDefinition(
        task_type="risk_report_generate",
        domain="risk",
    ),
    TaskTypeDefinition(
        task_type="risk_snapshot_generate_account",
        domain="risk",
    ),
    TaskTypeDefinition(
        task_type="risk_snapshot_generate_all",
        domain="risk",
    ),
    TaskTypeDefinition(
        task_type="signal_batch_cancel",
        domain="signal",
    ),
    TaskTypeDefinition(
        task_type="signal_batch_execute",
        domain="signal",
    ),
    TaskTypeDefinition(
        task_type="signal_batch_generate",
        domain="signal",
    ),
    TaskTypeDefinition(
        task_type="signal_batch_process",
        domain="signal",
    ),
    TaskTypeDefinition(
        task_type="signal_cleanup_expired",
        domain="signal",
    ),
    TaskTypeDefinition(
        task_type="signal_insights_generate",
        domain="signal",
    ),
    TaskTypeDefinition(
        task_type="signal_performance_calculate",
        domain="signal",
    ),
    TaskTypeDefinition(
        task_type="strategy_backtest_run",
        domain="strategy",
    ),
    TaskTypeDefinition(
        task_type="strategy_batch_execute",
        domain="strategy",
    ),
    TaskTypeDefinition(
        task_type="strategy_optimization_suggest",
        domain="strategy",
    ),
    TaskTypeDefinition(
        task_type="strategy_performance_analyze",
        domain="strategy",
    ),
    TaskTypeDefinition(
        task_type="portfolio_evaluate",
        domain="strategy",
    ),
    TaskTypeDefinition(
        task_type="portfolio_rebalance",
        domain="strategy",
    ),
    TaskTypeDefinition(
        task_type="trading_account_cleanup",
        domain="trading",
    ),
    TaskTypeDefinition(
        task_type="trading_batch_execute",
        domain="trading",
    ),
    TaskTypeDefinition(
        task_type="trading_daily_stats_calculate",
        domain="trading",
    ),
    TaskTypeDefinition(
        task_type="trading_pending_process",
        domain="trading",
    ),
    TaskTypeDefinition(
        task_type="trading_refresh_prices",
        domain="trading",
    ),
    TaskTypeDefinition(
        task_type="trading_risk_monitor",
        domain="trading",
    ),
)


def list_task_type_definitions() -> list[TaskTypeDefinition]:
    return sorted(_TASK_REGISTRY, key=lambda item: item.task_type)


def supported_task_types() -> set[str]:
    return {item.task_type for item in _TASK_REGISTRY}
