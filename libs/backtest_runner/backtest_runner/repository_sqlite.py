"""回测任务 SQLite 持久化仓储。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from backtest_runner.domain import BacktestTask


class SQLiteBacktestRepository:
    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS backtest_runner_task (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    strategy_id TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    idempotency_key TEXT,
                    status TEXT NOT NULL,
                    metrics_json TEXT,
                    display_name TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(backtest_runner_task)").fetchall()
            }
            if "display_name" not in columns:
                conn.execute("ALTER TABLE backtest_runner_task ADD COLUMN display_name TEXT")

            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_backtest_user_idempotency
                ON backtest_runner_task(user_id, idempotency_key)
                WHERE idempotency_key IS NOT NULL
                """
            )

    @staticmethod
    def _to_dt(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _from_row(row) -> BacktestTask:
        metrics = json.loads(row[6]) if row[6] is not None else None
        return BacktestTask(
            id=row[0],
            user_id=row[1],
            strategy_id=row[2],
            config=json.loads(row[3]),
            idempotency_key=row[4],
            status=row[5],
            metrics=metrics,
            display_name=row[7],
            created_at=SQLiteBacktestRepository._to_dt(row[8]),
            updated_at=SQLiteBacktestRepository._to_dt(row[9]),
        )

    def save(self, task: BacktestTask) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO backtest_runner_task
                    (id, user_id, strategy_id, config_json, idempotency_key, status, metrics_json, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    strategy_id = excluded.strategy_id,
                    config_json = excluded.config_json,
                    idempotency_key = excluded.idempotency_key,
                    status = excluded.status,
                    metrics_json = excluded.metrics_json,
                    display_name = excluded.display_name,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    task.id,
                    task.user_id,
                    task.strategy_id,
                    json.dumps(task.config, ensure_ascii=False),
                    task.idempotency_key,
                    task.status,
                    json.dumps(task.metrics, ensure_ascii=False) if task.metrics is not None else None,
                    task.display_name,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                ),
            )

    def save_if_absent(self, task: BacktestTask) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO backtest_runner_task
                        (id, user_id, strategy_id, config_json, idempotency_key, status, metrics_json, display_name, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.id,
                        task.user_id,
                        task.strategy_id,
                        json.dumps(task.config, ensure_ascii=False),
                        task.idempotency_key,
                        task.status,
                        json.dumps(task.metrics, ensure_ascii=False) if task.metrics is not None else None,
                        task.display_name,
                        task.created_at.isoformat(),
                        task.updated_at.isoformat(),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def delete(self, *, user_id: str, task_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM backtest_runner_task
                WHERE id = ? AND user_id = ?
                """,
                (task_id, user_id),
            )
            return cursor.rowcount > 0

    def find_by_idempotency_key(self, *, user_id: str, idempotency_key: str) -> BacktestTask | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, strategy_id, config_json, idempotency_key, status, metrics_json, display_name, created_at, updated_at
                FROM backtest_runner_task
                WHERE user_id = ? AND idempotency_key = ?
                """,
                (user_id, idempotency_key),
            ).fetchone()

        if row is None:
            return None
        return self._from_row(row)

    def get_by_id(self, task_id: str, *, user_id: str) -> BacktestTask | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, strategy_id, config_json, idempotency_key, status, metrics_json, display_name, created_at, updated_at
                FROM backtest_runner_task
                WHERE id = ? AND user_id = ?
                """,
                (task_id, user_id),
            ).fetchone()

        if row is None:
            return None
        return self._from_row(row)

    def list_by_user(
        self,
        *,
        user_id: str,
        strategy_id: str | None = None,
        status: str | None = None,
    ) -> list[BacktestTask]:
        query = """
            SELECT id, user_id, strategy_id, config_json, idempotency_key, status, metrics_json, display_name, created_at, updated_at
            FROM backtest_runner_task
            WHERE user_id = ?
        """
        params: list[object] = [user_id]

        if strategy_id is not None:
            query += " AND strategy_id = ?"
            params.append(strategy_id)

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at ASC"

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [self._from_row(row) for row in rows]

    def list_related_by_strategy(
        self,
        *,
        user_id: str,
        strategy_id: str,
        exclude_task_id: str,
        status: str | None = None,
        limit: int = 10,
    ) -> list[BacktestTask]:
        normalized_limit = max(1, limit)
        query = """
            SELECT id, user_id, strategy_id, config_json, idempotency_key, status, metrics_json, display_name, created_at, updated_at
            FROM backtest_runner_task
            WHERE user_id = ? AND strategy_id = ? AND id != ?
        """
        params: list[object] = [user_id, strategy_id, exclude_task_id]

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at ASC LIMIT ?"
        params.append(normalized_limit)

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [self._from_row(row) for row in rows]
