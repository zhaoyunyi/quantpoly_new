"""任务编排 SQLite 持久化仓储。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from job_orchestration.domain import Job


class SQLiteJobRepository:
    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            row[1]
            for row in conn.execute("PRAGMA table_info(job_orchestration_job)").fetchall()
        }
        if "result_json" not in existing:
            conn.execute("ALTER TABLE job_orchestration_job ADD COLUMN result_json TEXT")
        if "error_code" not in existing:
            conn.execute("ALTER TABLE job_orchestration_job ADD COLUMN error_code TEXT")
        if "error_message" not in existing:
            conn.execute("ALTER TABLE job_orchestration_job ADD COLUMN error_message TEXT")

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_orchestration_job (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, idempotency_key)
                )
                """
            )
            self._ensure_columns(conn)

    @staticmethod
    def _to_dt(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _from_row(row) -> Job:
        result_json = row[6]
        return Job(
            id=row[0],
            user_id=row[1],
            task_type=row[2],
            payload=json.loads(row[3]),
            idempotency_key=row[4],
            status=row[5],
            result=json.loads(result_json) if result_json else None,
            error_code=row[7],
            error_message=row[8],
            created_at=SQLiteJobRepository._to_dt(row[9]),
            updated_at=SQLiteJobRepository._to_dt(row[10]),
        )

    def save(self, job: Job) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO job_orchestration_job
                    (id, user_id, task_type, payload_json, idempotency_key, status, result_json, error_code, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    task_type = excluded.task_type,
                    payload_json = excluded.payload_json,
                    idempotency_key = excluded.idempotency_key,
                    status = excluded.status,
                    result_json = excluded.result_json,
                    error_code = excluded.error_code,
                    error_message = excluded.error_message,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    job.id,
                    job.user_id,
                    job.task_type,
                    json.dumps(job.payload, ensure_ascii=False),
                    job.idempotency_key,
                    job.status,
                    json.dumps(job.result, ensure_ascii=False) if job.result is not None else None,
                    job.error_code,
                    job.error_message,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )

    def save_if_absent(self, job: Job) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO job_orchestration_job
                        (id, user_id, task_type, payload_json, idempotency_key, status, result_json, error_code, error_message, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.id,
                        job.user_id,
                        job.task_type,
                        json.dumps(job.payload, ensure_ascii=False),
                        job.idempotency_key,
                        job.status,
                        json.dumps(job.result, ensure_ascii=False) if job.result is not None else None,
                        job.error_code,
                        job.error_message,
                        job.created_at.isoformat(),
                        job.updated_at.isoformat(),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get(self, *, user_id: str, job_id: str) -> Job | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, task_type, payload_json, idempotency_key, status, result_json, error_code, error_message, created_at, updated_at
                FROM job_orchestration_job
                WHERE id = ? AND user_id = ?
                """,
                (job_id, user_id),
            ).fetchone()

        if row is None:
            return None
        return self._from_row(row)

    def list(
        self,
        *,
        user_id: str,
        status: str | None = None,
        task_type: str | None = None,
    ) -> list[Job]:
        query = (
            "SELECT id, user_id, task_type, payload_json, idempotency_key, status, result_json, error_code, error_message, created_at, updated_at "
            "FROM job_orchestration_job WHERE user_id = ?"
        )
        params: list[str] = [user_id]

        if status is not None:
            query += " AND status = ?"
            params.append(status)
        if task_type is not None:
            query += " AND task_type = ?"
            params.append(task_type)

        query += " ORDER BY created_at ASC"

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [self._from_row(row) for row in rows]

    def find_by_idempotency_key(self, *, user_id: str, idempotency_key: str) -> Job | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, task_type, payload_json, idempotency_key, status, result_json, error_code, error_message, created_at, updated_at
                FROM job_orchestration_job
                WHERE user_id = ? AND idempotency_key = ?
                """,
                (user_id, idempotency_key),
            ).fetchone()

        if row is None:
            return None
        return self._from_row(row)
