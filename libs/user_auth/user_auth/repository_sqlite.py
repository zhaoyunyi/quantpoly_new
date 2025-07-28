"""SQLite 持久化用户仓储实现。"""

from __future__ import annotations

import sqlite3

from user_auth.domain import Credential, User


class SQLiteUserRepository:
    """基于 sqlite3 的用户仓储。"""

    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists auth_users (
                    id text primary key,
                    email text unique not null,
                    hashed_password text not null,
                    is_active integer not null,
                    email_verified integer not null default 0
                )
                """
            )
            conn.commit()

        # 向后兼容：旧库缺少 email_verified 列时补齐
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    alter table auth_users
                    add column email_verified integer not null default 0
                    """
                )
                conn.commit()
        except sqlite3.OperationalError:
            # duplicate column name 等场景忽略
            pass

    def save(self, user: User) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into auth_users(id, email, hashed_password, is_active, email_verified)
                values (?, ?, ?, ?, ?)
                on conflict(id) do update set
                    email=excluded.email,
                    hashed_password=excluded.hashed_password,
                    is_active=excluded.is_active,
                    email_verified=excluded.email_verified
                """,
                (
                    user.id,
                    user.email,
                    user.credential.hashed_password,
                    1 if user.is_active else 0,
                    1 if user.email_verified else 0,
                ),
            )
            conn.commit()

    def _to_user(self, row: tuple[str, str, str, int, int] | None) -> User | None:
        if row is None:
            return None
        return User(
            id=row[0],
            email=row[1],
            credential=Credential(hashed_password=row[2]),
            is_active=bool(row[3]),
            email_verified=bool(row[4]),
        )

    def get_by_id(self, user_id: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                "select id, email, hashed_password, is_active, email_verified from auth_users where id = ?",
                (user_id,),
            ).fetchone()
        return self._to_user(row)

    def get_by_email(self, email: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                "select id, email, hashed_password, is_active, email_verified from auth_users where email = ?",
                (email,),
            ).fetchone()
        return self._to_user(row)

    def email_exists(self, email: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "select 1 from auth_users where email = ? limit 1",
                (email,),
            ).fetchone()
        return row is not None
