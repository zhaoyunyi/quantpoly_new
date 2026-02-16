"""策略管理 Postgres 持久化仓储。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from strategy_management.domain import Strategy


class PostgresStrategyRepository:
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
                CREATE TABLE IF NOT EXISTS strategy_management_strategy (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    template TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _to_dt(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _from_row(row) -> Strategy:
        return Strategy(
            id=row[0],
            user_id=row[1],
            name=row[2],
            template=row[3],
            parameters=json.loads(row[4]),
            status=row[5],
            created_at=PostgresStrategyRepository._to_dt(row[6]),
            updated_at=PostgresStrategyRepository._to_dt(row[7]),
        )

    def save(self, strategy: Strategy) -> None:
        with self._engine.begin() as conn:
            self._execute(conn, 
                """
                INSERT INTO strategy_management_strategy
                    (id, user_id, name, template, parameters_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    name = excluded.name,
                    template = excluded.template,
                    parameters_json = excluded.parameters_json,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    strategy.id,
                    strategy.user_id,
                    strategy.name,
                    strategy.template,
                    json.dumps(strategy.parameters, ensure_ascii=False),
                    strategy.status,
                    strategy.created_at.isoformat(),
                    strategy.updated_at.isoformat(),
                ),
            )

    def get_by_id(self, strategy_id: str, *, user_id: str) -> Strategy | None:
        with self._engine.begin() as conn:
            row = self._execute(conn, 
                """
                SELECT id, user_id, name, template, parameters_json, status, created_at, updated_at
                FROM strategy_management_strategy
                WHERE id = ? AND user_id = ?
                """,
                (strategy_id, user_id),
            ).fetchone()

        if row is None:
            return None
        return self._from_row(row)

    def list_by_user(self, *, user_id: str) -> list[Strategy]:
        with self._engine.begin() as conn:
            rows = self._execute(conn, 
                """
                SELECT id, user_id, name, template, parameters_json, status, created_at, updated_at
                FROM strategy_management_strategy
                WHERE user_id = ?
                ORDER BY created_at ASC
                """,
                (user_id,),
            ).fetchall()

        return [self._from_row(row) for row in rows]

    def delete(self, strategy_id: str, *, user_id: str) -> bool:
        with self._engine.begin() as conn:
            cursor = self._execute(conn, 
                """
                DELETE FROM strategy_management_strategy
                WHERE id = ? AND user_id = ?
                """,
                (strategy_id, user_id),
            )
            return cursor.rowcount > 0
