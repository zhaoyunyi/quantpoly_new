"""job_orchestration 调度抽象与实现。"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from job_orchestration.domain import ScheduleConfig


class InMemoryScheduler:
    def __init__(self) -> None:
        self._schedules: list[ScheduleConfig] = []
        self.running = False

    def register_interval(
        self,
        *,
        job_type: str,
        every_seconds: int,
        user_id: str = "system",
        namespace: str = "system",
    ) -> ScheduleConfig:
        schedule = ScheduleConfig.create(
            user_id=user_id,
            namespace=namespace,
            job_type=job_type,
            schedule_type="interval",
            expression=str(every_seconds),
        )
        self._schedules.append(schedule)
        return schedule

    def register_cron(
        self,
        *,
        job_type: str,
        cron_expr: str,
        user_id: str = "system",
        namespace: str = "system",
    ) -> ScheduleConfig:
        schedule = ScheduleConfig.create(
            user_id=user_id,
            namespace=namespace,
            job_type=job_type,
            schedule_type="cron",
            expression=cron_expr,
        )
        self._schedules.append(schedule)
        return schedule

    def list_schedules(
        self,
        *,
        user_id: str | None = None,
        namespace: str | None = None,
    ) -> list[ScheduleConfig]:
        items = list(self._schedules)
        if user_id is not None:
            items = [item for item in items if item.user_id == user_id]
        if namespace is not None:
            items = [item for item in items if item.namespace == namespace]
        return items

    def get_schedule(self, *, schedule_id: str) -> ScheduleConfig | None:
        for schedule in self._schedules:
            if schedule.id == schedule_id:
                return schedule
        return None

    def stop_schedule(self, *, schedule_id: str) -> ScheduleConfig | None:
        schedule = self.get_schedule(schedule_id=schedule_id)
        if schedule is None:
            return None
        schedule.stop()
        return schedule

    def recover(self) -> int:
        return len([item for item in self._schedules if item.status == "active"])

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False


class SQLiteScheduler:
    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self.running = False
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_orchestration_schedule (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    job_type TEXT NOT NULL,
                    schedule_type TEXT NOT NULL,
                    expression TEXT NOT NULL,
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
    def _from_row(row) -> ScheduleConfig:
        return ScheduleConfig(
            id=row[0],
            user_id=row[1],
            namespace=row[2],
            job_type=row[3],
            schedule_type=row[4],
            expression=row[5],
            status=row[6],
            created_at=SQLiteScheduler._to_dt(row[7]),
            updated_at=SQLiteScheduler._to_dt(row[8]),
        )

    def _save(self, schedule: ScheduleConfig) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO job_orchestration_schedule
                    (id, user_id, namespace, job_type, schedule_type, expression, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    namespace = excluded.namespace,
                    job_type = excluded.job_type,
                    schedule_type = excluded.schedule_type,
                    expression = excluded.expression,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    schedule.id,
                    schedule.user_id,
                    schedule.namespace,
                    schedule.job_type,
                    schedule.schedule_type,
                    schedule.expression,
                    schedule.status,
                    schedule.created_at.isoformat(),
                    schedule.updated_at.isoformat(),
                ),
            )

    def register_interval(
        self,
        *,
        job_type: str,
        every_seconds: int,
        user_id: str = "system",
        namespace: str = "system",
    ) -> ScheduleConfig:
        schedule = ScheduleConfig.create(
            user_id=user_id,
            namespace=namespace,
            job_type=job_type,
            schedule_type="interval",
            expression=str(every_seconds),
        )
        self._save(schedule)
        return schedule

    def register_cron(
        self,
        *,
        job_type: str,
        cron_expr: str,
        user_id: str = "system",
        namespace: str = "system",
    ) -> ScheduleConfig:
        schedule = ScheduleConfig.create(
            user_id=user_id,
            namespace=namespace,
            job_type=job_type,
            schedule_type="cron",
            expression=cron_expr,
        )
        self._save(schedule)
        return schedule

    def list_schedules(
        self,
        *,
        user_id: str | None = None,
        namespace: str | None = None,
    ) -> list[ScheduleConfig]:
        query = (
            "SELECT id, user_id, namespace, job_type, schedule_type, expression, status, created_at, updated_at "
            "FROM job_orchestration_schedule WHERE 1 = 1"
        )
        params: list[str] = []

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        if namespace is not None:
            query += " AND namespace = ?"
            params.append(namespace)

        query += " ORDER BY created_at ASC"

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [self._from_row(row) for row in rows]

    def get_schedule(self, *, schedule_id: str) -> ScheduleConfig | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, namespace, job_type, schedule_type, expression, status, created_at, updated_at
                FROM job_orchestration_schedule
                WHERE id = ?
                """,
                (schedule_id,),
            ).fetchone()

        if row is None:
            return None
        return self._from_row(row)

    def stop_schedule(self, *, schedule_id: str) -> ScheduleConfig | None:
        schedule = self.get_schedule(schedule_id=schedule_id)
        if schedule is None:
            return None

        schedule.stop()
        self._save(schedule)
        return schedule

    def recover(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM job_orchestration_schedule WHERE status = 'active'"
            ).fetchone()
        return int(row[0] if row else 0)

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False
