from __future__ import annotations

from strategy_health.domain import HealthReport
from strategy_health.repository_postgres import PostgresHealthReportRepository


class _SqliteEngine:
    def __init__(self) -> None:
        import sqlite3

        self._conn = sqlite3.connect(":memory:")

    def begin(self):
        return _SqliteTransaction(self._conn)


class _SqliteTransaction:
    def __init__(self, conn) -> None:
        self._conn = conn

    def __enter__(self):
        return _SqliteConnection(self._conn)

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()


class _SqliteConnection:
    def __init__(self, conn) -> None:
        self._conn = conn

    def exec_driver_sql(self, sql: str, params: tuple | None = None):
        normalized_sql = sql.replace("%s", "?")
        if params is None:
            return self._conn.execute(normalized_sql)
        return self._conn.execute(normalized_sql, params)


def test_postgres_health_report_repository_should_round_trip_reports():
    repository = PostgresHealthReportRepository(
        engine=_SqliteEngine()
    )
    report = HealthReport.create(
        user_id="u-1",
        config={"template": "moving_average", "parameters": {"shortWindow": 5, "longWindow": 20}},
        strategy_id="s-1",
    )
    report.status = "completed"
    report.report = {"overallScore": 82, "sharpeRatio": 1.3}

    repository.save(report)

    stored = repository.get_by_id(report.id, user_id="u-1")

    assert stored is not None
    assert stored.id == report.id
    assert stored.report == {"overallScore": 82, "sharpeRatio": 1.3}
    assert repository.list_by_user(user_id="u-1")[0].id == report.id
