from __future__ import annotations

from apps.backend_app.router_registry import build_context
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


def test_build_context_should_use_postgres_health_report_repository(monkeypatch):
    monkeypatch.setattr(
        "apps.backend_app.router_registry._build_postgres_engine",
        lambda postgres_dsn: _SqliteEngine(),
    )

    context = build_context(
        storage_backend="postgres",
        postgres_dsn="postgresql://example",
    )

    assert isinstance(context.health_repo, PostgresHealthReportRepository)
