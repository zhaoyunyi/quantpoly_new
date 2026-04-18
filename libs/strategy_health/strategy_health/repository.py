"""策略健康报告仓储实现。"""

from __future__ import annotations

import copy
import threading
from typing import Protocol

from strategy_health.domain import HealthReport


class HealthReportRepository(Protocol):
    def save(self, report: HealthReport) -> None: ...

    def get_by_id(self, report_id: str, *, user_id: str) -> HealthReport | None: ...

    def list_by_user(self, *, user_id: str) -> list[HealthReport]: ...


class InMemoryHealthReportRepository:
    def __init__(self) -> None:
        self._reports: dict[str, HealthReport] = {}
        self._lock = threading.RLock()

    def _clone(self, report: HealthReport) -> HealthReport:
        return HealthReport(
            id=report.id,
            user_id=report.user_id,
            strategy_id=report.strategy_id,
            config=copy.deepcopy(report.config),
            status=report.status,
            report=copy.deepcopy(report.report),
            created_at=report.created_at,
            completed_at=report.completed_at,
        )

    def save(self, report: HealthReport) -> None:
        with self._lock:
            self._reports[report.id] = self._clone(report)

    def get_by_id(self, report_id: str, *, user_id: str) -> HealthReport | None:
        with self._lock:
            report = self._reports.get(report_id)
            if report is None or report.user_id != user_id:
                return None
            return self._clone(report)

    def list_by_user(self, *, user_id: str) -> list[HealthReport]:
        with self._lock:
            return [
                self._clone(report)
                for report in sorted(self._reports.values(), key=lambda r: r.created_at, reverse=True)
                if report.user_id == user_id
            ]
