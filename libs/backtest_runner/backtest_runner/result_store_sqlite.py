"""回测结果 SQLite 存储。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any


class SQLiteBacktestResultStore:
    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
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

        with self._connect() as conn:
            conn.execute(
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
        with self._connect() as conn:
            row = conn.execute(
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
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM backtest_runner_result
                WHERE task_id = ? AND user_id = ?
                """,
                (task_id, user_id),
            )
            return cursor.rowcount > 0
