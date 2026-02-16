"""PostgreSQL 持久化用户仓储实现。"""

from __future__ import annotations

from typing import Any

from user_auth.domain import Credential, User


class PostgresUserRepository:
    """基于 SQLAlchemy Engine 的 PostgreSQL 用户仓储。"""

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
                """,
            )

    def save(self, user: User) -> None:
        with self._engine.begin() as conn:
            self._execute(
                conn,
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
        with self._engine.begin() as conn:
            row = self._execute(
                conn,
                """
                select id, email, hashed_password, is_active, email_verified, role, level, display_name
                from auth_users where id = ?
                """,
                (user_id,),
            ).fetchone()
        return self._to_user(row)

    def get_by_email(self, email: str) -> User | None:
        with self._engine.begin() as conn:
            row = self._execute(
                conn,
                """
                select id, email, hashed_password, is_active, email_verified, role, level, display_name
                from auth_users where email = ?
                """,
                (email,),
            ).fetchone()
        return self._to_user(row)

    def email_exists(self, email: str) -> bool:
        with self._engine.begin() as conn:
            row = self._execute(
                conn,
                "select 1 from auth_users where email = ? limit 1",
                (email,),
            ).fetchone()
        return row is not None

    def create_admin_user(
        self,
        *,
        email: str,
        password: str,
        display_name: str | None = None,
        role: str | None = "user",
        level: int | None = 1,
        is_active: bool = True,
        email_verified: bool = False,
    ) -> User:
        if self.email_exists(email):
            raise ValueError("email already exists")

        user = User.register(email=email, password=password)

        if display_name is not None:
            user.update_profile(display_name=display_name)
        if role is not None:
            user.set_role(role)
        if level is not None:
            user.set_level(level)
        if email_verified:
            user.verify_email()
        if not is_active:
            user.disable()

        self.save(user)
        return user

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

        with self._engine.begin() as conn:
            count_row = self._execute(
                conn,
                f"select count(*) from auth_users{where}",  # noqa: S608
                tuple(params),
            ).fetchone()
            total = int(count_row[0]) if count_row else 0

            rows = self._execute(
                conn,
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

    def delete(self, user_id: str) -> bool:
        with self._engine.begin() as conn:
            cursor = self._execute(
                conn,
                "delete from auth_users where id = ?",
                (user_id,),
            )
            return cursor.rowcount > 0
