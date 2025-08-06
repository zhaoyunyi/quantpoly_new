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
                    email_verified integer not null default 0,
                    role text not null default 'user',
                    level integer not null default 1,
                    display_name text
                )
                """
            )
            conn.commit()

        migration_sql = [
            "alter table auth_users add column email_verified integer not null default 0",
            "alter table auth_users add column role text not null default 'user'",
            "alter table auth_users add column level integer not null default 1",
            "alter table auth_users add column display_name text",
        ]
        for statement in migration_sql:
            try:
                with self._connect() as conn:
                    conn.execute(statement)
                    conn.commit()
            except sqlite3.OperationalError:
                pass

    def save(self, user: User) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into auth_users(
                    id, email, hashed_password, is_active, email_verified, role, level, display_name
                )
                values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                    email=excluded.email,
                    hashed_password=excluded.hashed_password,
                    is_active=excluded.is_active,
                    email_verified=excluded.email_verified,
                    role=excluded.role,
                    level=excluded.level,
                    display_name=excluded.display_name
                """,
                (
                    user.id,
                    user.email,
                    user.credential.hashed_password,
                    1 if user.is_active else 0,
                    1 if user.email_verified else 0,
                    user.role,
                    user.level,
                    user.display_name,
                ),
            )
            conn.commit()

    def _to_user(
        self,
        row: tuple[str, str, str, int, int, str | None, int | None, str | None] | None,
    ) -> User | None:
        if row is None:
            return None
        role = row[5] if row[5] is not None else "user"
        level = int(row[6]) if row[6] is not None else 1
        return User(
            id=row[0],
            email=row[1],
            credential=Credential(hashed_password=row[2]),
            is_active=bool(row[3]),
            email_verified=bool(row[4]),
            role=role,
            level=level,
            display_name=row[7],
        )

    def get_by_id(self, user_id: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                select id, email, hashed_password, is_active, email_verified, role, level, display_name
                from auth_users where id = ?
                """,
                (user_id,),
            ).fetchone()
        return self._to_user(row)

    def get_by_email(self, email: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                select id, email, hashed_password, is_active, email_verified, role, level, display_name
                from auth_users where email = ?
                """,
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

    def list_users(
        self,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        where = ""
        params: list[object] = []
        if status is not None:
            where = " where is_active = ?"
            params.append(1 if status == "active" else 0)

        offset = max(0, page - 1) * page_size

        with self._connect() as conn:
            count_row = conn.execute(
                f"select count(*) from auth_users{where}",  # noqa: S608
                tuple(params),
            ).fetchone()
            total = int(count_row[0]) if count_row else 0

            rows = conn.execute(
                f"""
                select id, email, hashed_password, is_active, email_verified, role, level, display_name
                from auth_users{where}
                order by email asc
                limit ? offset ?
                """,  # noqa: S608
                tuple(params + [page_size, offset]),
            ).fetchall()

        items: list[User] = []
        for row in rows:
            user = self._to_user(row)
            if user is not None:
                items.append(user)

        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }

    def update_user_level(self, *, user_id: str, level: int) -> User | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.set_level(level)
        self.save(user)
        return user

    def update_user_status(self, *, user_id: str, is_active: bool) -> User | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        if is_active:
            user.enable()
        else:
            user.disable()
        self.save(user)
        return user
