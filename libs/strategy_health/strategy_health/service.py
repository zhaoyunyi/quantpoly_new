"""策略健康报告服务。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from strategy_health.analysis import (
    analyze_out_of_sample,
    analyze_parameter_sensitivity,
    calculate_overfit_score,
)
from strategy_health.domain import HealthReport
from strategy_health.engine import (
    SimulationConfigurationError,
    UnsupportedTemplateError,
    run_simulation,
    supports_template,
)
from strategy_health.repository import HealthReportRepository


class HealthReportExecutionError(RuntimeError):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class StrategyHealthService:
    def __init__(
        self,
        *,
        repository: HealthReportRepository,
        market_history_reader: Callable[..., Any] | None = None,
    ) -> None:
        self._repository = repository
        self._market_history_reader = market_history_reader

    def _fail_report(
        self,
        *,
        report: HealthReport,
        code: str,
        message: str,
    ) -> HealthReportExecutionError:
        report.status = "failed"
        report.report = {"error": message}
        self._repository.save(report)
        return HealthReportExecutionError(code=code, message=message)

    def _extract_close_prices(self, rows: Any) -> list[float]:
        if rows is None:
            return []
        prices: list[float] = []
        for row in list(rows):
            value: Any = None
            if isinstance(row, dict):
                value = row.get("close") or row.get("close_price") or row.get("c")
            else:
                for key in ("close_price", "close", "c"):
                    if hasattr(row, key):
                        value = getattr(row, key)
                        if value is not None:
                            break
            if value is None:
                continue
            try:
                prices.append(float(value))
            except (TypeError, ValueError):
                continue
        return prices

    def create_report(self, *, user_id: str, config: dict[str, Any]) -> HealthReport:
        """创建健康报告任务。"""
        strategy_id = config.get("strategyId")
        report = HealthReport.create(user_id=user_id, config=config, strategy_id=strategy_id)
        self._repository.save(report)
        return report

    def execute_report(self, *, user_id: str, report_id: str) -> HealthReport:
        """执行健康分析。"""
        report = self._repository.get_by_id(report_id, user_id=user_id)
        if report is None:
            raise HealthReportExecutionError(code="REPORT_NOT_FOUND", message="report not found")

        report.status = "running"
        self._repository.save(report)

        config = report.config
        template = str(config.get("template", "")).strip().lower()
        parameters = dict(config.get("parameters") or {})
        initial_capital = float(config.get("initialCapital", 100000))
        commission_rate = float(config.get("commissionRate", 0.0))

        if not supports_template(template):
            raise self._fail_report(
                report=report,
                code="UNSUPPORTED_TEMPLATE",
                message=f"unsupported template: {template or 'unknown'}",
            )

        try:
            close_prices = self._resolve_close_prices(user_id=user_id, config=config)
        except Exception as exc:
            raise self._fail_report(
                report=report,
                code="MARKET_DATA_UNAVAILABLE",
                message=str(exc),
            ) from exc

        if not close_prices:
            raise self._fail_report(
                report=report,
                code="NO_MARKET_DATA",
                message="no market data available",
            )

        try:
            sensitivity = analyze_parameter_sensitivity(
                close_prices, template, parameters, initial_capital, commission_rate
            )
            oos = analyze_out_of_sample(
                close_prices, template, parameters, initial_capital, commission_rate
            )
            baseline = run_simulation(close_prices, template, parameters, initial_capital, commission_rate)
            trade_count = int(baseline["metrics"]["tradeCount"])
            overall_score, overfit_risk, warnings = calculate_overfit_score(sensitivity, oos, trade_count)

            report.status = "completed"
            report.completed_at = datetime.now(timezone.utc)
            report.report = {
                "overallScore": overall_score,
                "overfitRisk": overfit_risk,
                "inSampleReturn": oos["inSampleReturn"],
                "outSampleReturn": oos["outSampleReturn"],
                "returnRatio": oos["returnRatio"],
                "paramSensitivity": {
                    r.param_name: {
                        "rating": r.rating,
                        "originalValue": r.original_value,
                        "variations": r.variations,
                    }
                    for r in sensitivity
                },
                "tradeCount": trade_count,
                "maxDrawdown": baseline["metrics"]["maxDrawdown"],
                "sharpeRatio": baseline["metrics"]["sharpeRatio"],
                "warnings": warnings,
            }
        except UnsupportedTemplateError as exc:
            raise self._fail_report(
                report=report,
                code="UNSUPPORTED_TEMPLATE",
                message=str(exc),
            ) from exc
        except SimulationConfigurationError as exc:
            raise self._fail_report(
                report=report,
                code="INVALID_CONFIGURATION",
                message=str(exc),
            ) from exc
        except Exception as exc:
            raise self._fail_report(
                report=report,
                code="ANALYSIS_FAILED",
                message=str(exc),
            ) from exc

        self._repository.save(report)
        return report

    def _resolve_close_prices(self, *, user_id: str, config: dict[str, Any]) -> list[float]:
        inline_prices = config.get("prices")
        if isinstance(inline_prices, list) and inline_prices:
            return [float(p) for p in inline_prices]

        if self._market_history_reader is None:
            return []

        symbol = str(config.get("symbol", "")).strip().upper()
        if not symbol:
            return []

        start_date = config.get("startDate")
        end_date = config.get("endDate")
        timeframe = str(config.get("timeframe", "1Day"))

        rows = self._market_history_reader(
            user_id=user_id,
            symbol=symbol,
            start_date=str(start_date) if start_date else "1970-01-01",
            end_date=str(end_date) if end_date else "2100-01-01",
            timeframe=timeframe,
            limit=None,
        )
        return self._extract_close_prices(rows)

    def get_report(self, *, user_id: str, report_id: str) -> HealthReport | None:
        return self._repository.get_by_id(report_id, user_id=user_id)

    def list_reports(self, *, user_id: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        all_items = self._repository.list_by_user(user_id=user_id)
        total = len(all_items)
        start = max(page - 1, 0) * page_size
        end = start + page_size
        return {
            "items": all_items[start:end],
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
