"""signal_execution SQLite 持久化仓储。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from signal_execution.domain import ExecutionRecord, TradingSignal


class SQLiteSignalRepository:
    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signal_execution_signal (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    strategy_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signal_execution_execution (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    signal_id TEXT NOT NULL,
                    strategy_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signal_execution_batch_record (
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    PRIMARY KEY(user_id, action, idempotency_key)
                )
                """
            )

    @staticmethod
    def _dt(value: str | None) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(value)

    @classmethod
    def _signal_from_row(cls, row) -> TradingSignal:
        return TradingSignal(
            id=row[0],
            user_id=row[1],
            strategy_id=row[2],
            account_id=row[3],
            symbol=row[4],
            side=row[5],
            status=row[6],
            created_at=datetime.fromisoformat(row[7]),
            updated_at=datetime.fromisoformat(row[8]),
            expires_at=cls._dt(row[9]),
            metadata=dict(json.loads(row[10] or "{}")),
        )

    @staticmethod
    def _execution_from_row(row) -> ExecutionRecord:
        return ExecutionRecord(
            id=row[0],
            user_id=row[1],
            signal_id=row[2],
            strategy_id=row[3],
            symbol=row[4],
            status=row[5],
            metrics=dict(json.loads(row[6] or "{}")),
            created_at=datetime.fromisoformat(row[7]),
        )

    def save_signal(self, signal: TradingSignal) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO signal_execution_signal
                    (id, user_id, strategy_id, account_id, symbol, side, status, created_at, updated_at, expires_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    strategy_id = excluded.strategy_id,
                    account_id = excluded.account_id,
                    symbol = excluded.symbol,
                    side = excluded.side,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    expires_at = excluded.expires_at,
                    metadata_json = excluded.metadata_json
                """,
                (
                    signal.id,
                    signal.user_id,
                    signal.strategy_id,
                    signal.account_id,
                    signal.symbol,
                    signal.side,
                    signal.status,
                    signal.created_at.isoformat(),
                    signal.updated_at.isoformat(),
                    signal.expires_at.isoformat() if signal.expires_at else None,
                    json.dumps(signal.metadata, ensure_ascii=False),
                ),
            )

    def get_signal(self, *, signal_id: str, user_id: str) -> TradingSignal | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, strategy_id, account_id, symbol, side, status, created_at, updated_at, expires_at, metadata_json
                FROM signal_execution_signal
                WHERE id = ? AND user_id = ?
                """,
                (signal_id, user_id),
            ).fetchone()
        if row is None:
            return None
        return self._signal_from_row(row)

    def get_signal_any(self, *, signal_id: str) -> TradingSignal | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, strategy_id, account_id, symbol, side, status, created_at, updated_at, expires_at, metadata_json
                FROM signal_execution_signal
                WHERE id = ?
                """,
                (signal_id,),
            ).fetchone()
        if row is None:
            return None
        return self._signal_from_row(row)

    def list_signals(
        self,
        *,
        user_id: str,
        keyword: str | None = None,
        strategy_id: str | None = None,
        account_id: str | None = None,
        symbol: str | None = None,
        status: str | None = None,
    ) -> list[TradingSignal]:
        clauses = ["user_id = ?"]
        params: list[object] = [user_id]

        if strategy_id is not None:
            clauses.append("strategy_id = ?")
            params.append(strategy_id)
        if account_id is not None:
            clauses.append("account_id = ?")
            params.append(account_id)
        if symbol is not None:
            clauses.append("symbol = ?")
            params.append(symbol)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)

        where_sql = " AND ".join(clauses)
        sql = (
            "SELECT id, user_id, strategy_id, account_id, symbol, side, status, created_at, updated_at, expires_at, metadata_json "
            "FROM signal_execution_signal "
            f"WHERE {where_sql} "
            "ORDER BY created_at ASC"
        )

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        items = [self._signal_from_row(row) for row in rows]
        if not keyword:
            return items

        keyword_lower = keyword.lower()
        return [
            item
            for item in items
            if keyword_lower in item.symbol.lower() or keyword_lower in item.strategy_id.lower()
        ]

    def save_execution(self, execution: ExecutionRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO signal_execution_execution
                    (id, user_id, signal_id, strategy_id, symbol, status, metrics_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    signal_id = excluded.signal_id,
                    strategy_id = excluded.strategy_id,
                    symbol = excluded.symbol,
                    status = excluded.status,
                    metrics_json = excluded.metrics_json,
                    created_at = excluded.created_at
                """,
                (
                    execution.id,
                    execution.user_id,
                    execution.signal_id,
                    execution.strategy_id,
                    execution.symbol,
                    execution.status,
                    json.dumps(execution.metrics, ensure_ascii=False),
                    execution.created_at.isoformat(),
                ),
            )

    def get_execution(self, *, execution_id: str, user_id: str) -> ExecutionRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, signal_id, strategy_id, symbol, status, metrics_json, created_at
                FROM signal_execution_execution
                WHERE id = ? AND user_id = ?
                """,
                (execution_id, user_id),
            ).fetchone()
        if row is None:
            return None
        return self._execution_from_row(row)

    def list_executions(
        self,
        *,
        user_id: str,
        signal_id: str | None = None,
        status: str | None = None,
    ) -> list[ExecutionRecord]:
        clauses = ["user_id = ?"]
        params: list[object] = [user_id]

        if signal_id is not None:
            clauses.append("signal_id = ?")
            params.append(signal_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)

        where_sql = " AND ".join(clauses)
        sql = (
            "SELECT id, user_id, signal_id, strategy_id, symbol, status, metrics_json, created_at "
            "FROM signal_execution_execution "
            f"WHERE {where_sql} "
            "ORDER BY created_at ASC"
        )

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._execution_from_row(item) for item in rows]

    def delete_signals_by_user(self, *, user_id: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM signal_execution_signal WHERE user_id = ?",
                (user_id,),
            )
        return cursor.rowcount

    def delete_expired_signals_by_user(self, *, user_id: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM signal_execution_signal WHERE user_id = ? AND status = 'expired'",
                (user_id,),
            )
        return cursor.rowcount

    def delete_all_signals(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM signal_execution_signal")
        return cursor.rowcount

    def delete_executions_before(self, *, cutoff: datetime) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM signal_execution_execution WHERE created_at < ?",
                (cutoff.isoformat(),),
            )
        return cursor.rowcount

    def get_batch_record(
        self,
        *,
        user_id: str,
        action: str,
        idempotency_key: str,
    ) -> tuple[str, dict] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT fingerprint, result_json
                FROM signal_execution_batch_record
                WHERE user_id = ? AND action = ? AND idempotency_key = ?
                """,
                (user_id, action, idempotency_key),
            ).fetchone()

        if row is None:
            return None
        return row[0], dict(json.loads(row[1] or "{}"))

    def save_batch_record(
        self,
        *,
        user_id: str,
        action: str,
        idempotency_key: str,
        fingerprint: str,
        result: dict,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO signal_execution_batch_record
                    (user_id, action, idempotency_key, fingerprint, result_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, action, idempotency_key) DO UPDATE SET
                    fingerprint = excluded.fingerprint,
                    result_json = excluded.result_json
                """,
                (
                    user_id,
                    action,
                    idempotency_key,
                    fingerprint,
                    json.dumps(result, ensure_ascii=False),
                ),
            )
