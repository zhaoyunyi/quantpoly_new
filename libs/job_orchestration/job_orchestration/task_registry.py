"""job_orchestration 任务类型注册表。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskTypeDefinition:
    task_type: str
    domain: str
    schedulable: bool = True
    legacy_names: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, object]:
        return {
            "taskType": self.task_type,
            "domain": self.domain,
            "schedulable": self.schedulable,
            "legacyNames": list(self.legacy_names),
        }


_TASK_REGISTRY: tuple[TaskTypeDefinition, ...] = (
    TaskTypeDefinition(
        task_type="backtest_run",
        domain="backtest",
        legacy_names=("backtest.execute_backtest",),
    ),
    TaskTypeDefinition(
        task_type="market_data_fetch",
        domain="market-data",
        legacy_names=("data.fetch_stock_data",),
    ),
    TaskTypeDefinition(
        task_type="market_data_sync",
        domain="market-data",
        legacy_names=("data.sync_market_data",),
    ),
    TaskTypeDefinition(
        task_type="market_indicators_calculate",
        domain="market-data",
        legacy_names=("data.calculate_technical_indicators",),
    ),
    TaskTypeDefinition(
        task_type="risk_account_evaluate",
        domain="risk",
        legacy_names=("risk.generate_account_risk_snapshot",),
    ),
    TaskTypeDefinition(
        task_type="risk_alert_cleanup",
        domain="risk",
        legacy_names=("risk.cleanup_old_alerts",),
    ),
    TaskTypeDefinition(
        task_type="risk_alert_notify",
        domain="risk",
        legacy_names=("risk.process_alert_notifications",),
    ),
    TaskTypeDefinition(
        task_type="risk_batch_check",
        domain="risk",
        legacy_names=("risk.batch_risk_check",),
    ),
    TaskTypeDefinition(
        task_type="risk_continuous_monitor",
        domain="risk",
        legacy_names=("risk.continuous_monitoring",),
    ),
    TaskTypeDefinition(
        task_type="risk_report_generate",
        domain="risk",
        legacy_names=("risk.generate_risk_report",),
    ),
    TaskTypeDefinition(
        task_type="risk_snapshot_generate_account",
        domain="risk",
        legacy_names=("risk.generate_account_risk_snapshot",),
    ),
    TaskTypeDefinition(
        task_type="risk_snapshot_generate_all",
        domain="risk",
        legacy_names=("risk.generate_all_risk_snapshots",),
    ),
    TaskTypeDefinition(
        task_type="signal_batch_cancel",
        domain="signal",
        legacy_names=("signal.batch_process_signals",),
    ),
    TaskTypeDefinition(
        task_type="signal_batch_execute",
        domain="signal",
        legacy_names=("signal.batch_process_signals",),
    ),
    TaskTypeDefinition(
        task_type="signal_batch_generate",
        domain="signal",
        legacy_names=("signal.batch_generate_signals",),
    ),
    TaskTypeDefinition(
        task_type="signal_batch_process",
        domain="signal",
        legacy_names=("signal.batch_process_signals",),
    ),
    TaskTypeDefinition(
        task_type="signal_cleanup_expired",
        domain="signal",
        legacy_names=("signal.cleanup_expired_signals",),
    ),
    TaskTypeDefinition(
        task_type="signal_insights_generate",
        domain="signal",
        legacy_names=("signal.generate_signal_insights",),
    ),
    TaskTypeDefinition(
        task_type="signal_performance_calculate",
        domain="signal",
        legacy_names=("signal.calculate_signal_performance",),
    ),
    TaskTypeDefinition(
        task_type="strategy_backtest_run",
        domain="strategy",
        legacy_names=("strategy.run_strategy_backtest",),
    ),
    TaskTypeDefinition(
        task_type="strategy_batch_execute",
        domain="strategy",
        legacy_names=("strategy.batch_execute_strategies",),
    ),
    TaskTypeDefinition(
        task_type="strategy_optimization_suggest",
        domain="strategy",
        legacy_names=("strategy.generate_optimization_suggestions",),
    ),
    TaskTypeDefinition(
        task_type="strategy_performance_analyze",
        domain="strategy",
        legacy_names=("strategy.analyze_strategy_performance",),
    ),
    TaskTypeDefinition(
        task_type="portfolio_evaluate",
        domain="strategy",
        legacy_names=("strategy.evaluate_portfolio",),
    ),
    TaskTypeDefinition(
        task_type="portfolio_rebalance",
        domain="strategy",
        legacy_names=("strategy.rebalance_portfolio",),
    ),
    TaskTypeDefinition(
        task_type="trading_account_cleanup",
        domain="trading",
        legacy_names=("trading.account_cleanup",),
    ),
    TaskTypeDefinition(
        task_type="trading_batch_execute",
        domain="trading",
        legacy_names=("trading.batch_trade_execution",),
    ),
    TaskTypeDefinition(
        task_type="trading_daily_stats_calculate",
        domain="trading",
        legacy_names=("trading.calculate_daily_stats",),
    ),
    TaskTypeDefinition(
        task_type="trading_pending_process",
        domain="trading",
        legacy_names=("trading.process_pending_trades",),
    ),
    TaskTypeDefinition(
        task_type="trading_refresh_prices",
        domain="trading",
        legacy_names=("trading.update_market_prices",),
    ),
    TaskTypeDefinition(
        task_type="trading_risk_monitor",
        domain="trading",
        legacy_names=("trading.risk_monitoring",),
    ),
)


def list_task_type_definitions() -> list[TaskTypeDefinition]:
    return sorted(_TASK_REGISTRY, key=lambda item: item.task_type)


def supported_task_types() -> set[str]:
    return {item.task_type for item in _TASK_REGISTRY}

