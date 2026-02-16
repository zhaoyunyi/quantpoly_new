"""PostgreSQL 持久化密码找回 token 存储。"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from user_auth.password_reset import DEFAULT_RESET_TOKEN_TTL_SECONDS, PasswordResetToken


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _from_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class PostgresPasswordResetStore:
    def __init__(
        self,
        *,
        engine: Any,
        ttl_seconds: int = DEFAULT_RESET_TOKEN_TTL_SECONDS,
        now_provider: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._engine = engine
        self._ttl_seconds = ttl_seconds
        self._now_provider = now_provider
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
                create table if not exists auth_password_reset_tokens (
                    token_digest text primary key,
                    user_id text not null,
                    created_at text not null,
                    expires_at text not null,
                    consumed_at text
                )
                """,
            )

    def issue(self, *, user_id: str) -> PasswordResetToken:
        issued = PasswordResetToken.create(
            user_id=user_id,
            ttl_seconds=self._ttl_seconds,
            now_provider=self._now_provider,
        )

        with self._engine.begin() as conn:
            self._execute(
                conn,
                """
                insert into auth_password_reset_tokens(
                    token_digest, user_id, created_at, expires_at, consumed_at
                ) values (?, ?, ?, ?, NULL)
                """,
                (
                    _digest(issued.token),
                    issued.user_id,
                    _to_iso(issued.created_at),
                    _to_iso(issued.expires_at),
                ),
            )

        return issued

    def consume(self, token: str) -> PasswordResetToken | None:
        token_digest = _digest(token)
        with self._engine.begin() as conn:
            row = self._execute(
                conn,
                """
                select user_id, created_at, expires_at, consumed_at
                from auth_password_reset_tokens
                where token_digest = ?
                """,
                (token_digest,),
            ).fetchone()
            if row is None:
                return None

            user_id = str(row[0])
            created_at = _from_iso(str(row[1]))
            expires_at = _from_iso(str(row[2]))
            consumed_at = row[3]

            if consumed_at is not None:
                return None

            if self._now_provider() >= expires_at:
                self._execute(
                    conn,
                    "update auth_password_reset_tokens set consumed_at = ? where token_digest = ?",
                    (_to_iso(self._now_provider()), token_digest),
                )
                return None

            updated = self._execute(
                conn,
                """
                update auth_password_reset_tokens
                set consumed_at = ?
                where token_digest = ? and consumed_at is null
                """,
                (_to_iso(self._now_provider()), token_digest),
            )

            if updated.rowcount <= 0:
                return None

        return PasswordResetToken(
            token=token,
            user_id=user_id,
            created_at=created_at,
            expires_at=expires_at,
        )
