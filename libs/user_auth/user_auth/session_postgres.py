"""PostgreSQL 持久化会话存储实现。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from user_auth.session import Session


def _to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _from_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class PostgresSessionStore:
    """基于 SQLAlchemy Engine 的会话持久化存储。"""

    def __init__(self, *, engine: Any) -> None:
        self._engine = engine
        self._ensure_schema()

    @staticmethod
    def _execute(conn, sql: str, params: tuple | list | None = None):
        normalized_sql = sql.replace("?", "%s")
        if params is None:
            return conn.exec_driver_sql(normalized_sql)
        return conn.exec_driver_sql(normalized_sql, tuple(params))

    def _ensure_schema(self) -> None:
        with self._engine.begin() as conn:
            self._execute(
                conn,
                """
                create table if not exists auth_sessions (
                    token text primary key,
                    user_id text not null,
                    created_at text not null,
                    expires_at text not null
                )
                """,
            )

    def save(self, session: Session) -> None:
        with self._engine.begin() as conn:
            self._execute(
                conn,
                """
                insert into auth_sessions(token, user_id, created_at, expires_at)
                values (?, ?, ?, ?)
                on conflict(token) do update set
                    user_id=excluded.user_id,
                    created_at=excluded.created_at,
                    expires_at=excluded.expires_at
                """,
                (
                    session.token,
                    session.user_id,
                    _to_iso(session.created_at),
                    _to_iso(session.expires_at),
                ),
            )

    def get_by_token(self, token: str) -> Session | None:
        with self._engine.begin() as conn:
            row = self._execute(
                conn,
                "select token, user_id, created_at, expires_at from auth_sessions where token = ?",
                (token,),
            ).fetchone()

            if row is None:
                return None

            session = Session(
                token=row[0],
                user_id=row[1],
                created_at=_from_iso(row[2]),
                expires_at=_from_iso(row[3]),
            )

            if session.is_expired:
                self._execute(conn, "delete from auth_sessions where token = ?", (token,))
                return None

            return session

    def revoke(self, token: str) -> None:
        with self._engine.begin() as conn:
            self._execute(conn, "delete from auth_sessions where token = ?", (token,))

    def revoke_by_user(self, *, user_id: str) -> int:
        with self._engine.begin() as conn:
            row = self._execute(
                conn,
                "select count(*) from auth_sessions where user_id = ?",
                (user_id,),
            ).fetchone()
            self._execute(conn, "delete from auth_sessions where user_id = ?", (user_id,))
        return int(row[0]) if row is not None else 0
