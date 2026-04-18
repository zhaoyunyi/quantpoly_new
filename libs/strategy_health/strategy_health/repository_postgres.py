"""策略健康报告 Postgres 持久化仓储。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from strategy_health.domain import HealthReport


class PostgresHealthReportRepository:
    def __init__(self, *, engine: Any) -> None:
        self._engine = engine
        self._init_schema()

    @staticmethod
    def _execute(conn, sql: str, params: tuple | list | None = None):
        normalized_sql = sql.replace("?", "%s")
        if params is None:
            return conn.exec_driver_sql(normalized_sql)
        return conn.exec_driver_sql(normalized_sql, tuple(params))

    def _init_schema(self) -> None:
        with self._engine.begin() as conn:
            self._execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS strategy_health_report (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    strategy_id TEXT,
                    config_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    report_json TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """,
            )

    @staticmethod
    def _to_dt(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _from_row(row) -> HealthReport:
        return HealthReport(
            id=row[0],
            user_id=row[1],
            strategy_id=row[2],
            config=json.loads(row[3]),
            status=row[4],
            report=json.loads(row[5]) if row[5] is not None else None,
            created_at=PostgresHealthReportRepository._to_dt(row[6]),
            completed_at=PostgresHealthReportRepository._to_dt(row[7]) if row[7] is not None else None,
        )

    def save(self, report: HealthReport) -> None:
        with self._engine.begin() as conn:
            self._execute(
                conn,
                """
                INSERT INTO strategy_health_report
                    (id, user_id, strategy_id, config_json, status, report_json, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    strategy_id = excluded.strategy_id,
                    config_json = excluded.config_json,
                    status = excluded.status,
                    report_json = excluded.report_json,
                    created_at = excluded.created_at,
                    completed_at = excluded.completed_at
                """,
                (
                    report.id,
                    report.user_id,
                    report.strategy_id,
                    json.dumps(report.config, ensure_ascii=False),
                    report.status,
                    json.dumps(report.report, ensure_ascii=False) if report.report is not None else None,
                    report.created_at.isoformat(),
                    report.completed_at.isoformat() if report.completed_at is not None else None,
                ),
            )

    def get_by_id(self, report_id: str, *, user_id: str) -> HealthReport | None:
        with self._engine.begin() as conn:
            row = self._execute(
                conn,
                """
                SELECT id, user_id, strategy_id, config_json, status, report_json, created_at, completed_at
                FROM strategy_health_report
                WHERE id = ? AND user_id = ?
                """,
                (report_id, user_id),
            ).fetchone()

        if row is None:
            return None
        return self._from_row(row)

    def list_by_user(self, *, user_id: str) -> list[HealthReport]:
        with self._engine.begin() as conn:
            rows = self._execute(
                conn,
                """
                SELECT id, user_id, strategy_id, config_json, status, report_json, created_at, completed_at
                FROM strategy_health_report
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()

        return [self._from_row(row) for row in rows]
