"""SQLite 持久化会话存储实现。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from user_auth.session import Session


def _to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _from_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class SQLiteSessionStore:
    """基于 sqlite3 的会话持久化存储。"""

    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists auth_sessions (
                    token text primary key,
                    user_id text not null,
                    created_at text not null,
                    expires_at text not null
                )
                """
            )
            conn.commit()

    def save(self, session: Session) -> None:
        with self._connect() as conn:
            conn.execute(
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
            conn.commit()

    def get_by_token(self, token: str) -> Session | None:
        with self._connect() as conn:
            row = conn.execute(
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
                conn.execute("delete from auth_sessions where token = ?", (token,))
                conn.commit()
                return None

            return session

    def revoke(self, token: str) -> None:
        with self._connect() as conn:
            conn.execute("delete from auth_sessions where token = ?", (token,))
            conn.commit()

