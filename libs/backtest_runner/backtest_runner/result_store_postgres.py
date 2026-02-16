"""回测结果 Postgres 存储。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


class PostgresBacktestResultStore:
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
            self._execute(conn, 
                """
                CREATE TABLE IF NOT EXISTS backtest_runner_result (
                    task_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (task_id, user_id)
                )
                """
            )

    def save_result(self, *, user_id: str, task_id: str, result: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload = dict(result)
        payload.setdefault("updatedAt", now)

        with self._engine.begin() as conn:
            self._execute(conn, 
                """
                INSERT INTO backtest_runner_result (task_id, user_id, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(task_id, user_id) DO UPDATE SET
                    result_json = excluded.result_json,
                    updated_at = excluded.updated_at
                """,
                (
                    task_id,
                    user_id,
                    json.dumps(payload, ensure_ascii=False),
                    now,
                    now,
                ),
            )

    def get_result(self, *, user_id: str, task_id: str) -> dict[str, Any] | None:
        with self._engine.begin() as conn:
            row = self._execute(conn, 
                """
                SELECT result_json
                FROM backtest_runner_result
                WHERE task_id = ? AND user_id = ?
                """,
                (task_id, user_id),
            ).fetchone()

        if row is None:
            return None
        return json.loads(row[0])

    def delete_result(self, *, user_id: str, task_id: str) -> bool:
        with self._engine.begin() as conn:
            cursor = self._execute(conn, 
                """
                DELETE FROM backtest_runner_result
                WHERE task_id = ? AND user_id = ?
                """,
                (task_id, user_id),
            )
            return cursor.rowcount > 0
