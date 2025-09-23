"""SQLite 持久化密码找回 token 存储。"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone

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


class SQLitePasswordResetStore:
    def __init__(
        self,
        *,
        db_path: str,
        ttl_seconds: int = DEFAULT_RESET_TOKEN_TTL_SECONDS,
        now_provider: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._db_path = db_path
        self._ttl_seconds = ttl_seconds
        self._now_provider = now_provider
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_password_reset_tokens (
                    token_digest TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT
                )
                """
            )
            conn.commit()

    def issue(self, *, user_id: str) -> PasswordResetToken:
        issued = PasswordResetToken.create(
            user_id=user_id,
            ttl_seconds=self._ttl_seconds,
            now_provider=self._now_provider,
        )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_password_reset_tokens(
                    token_digest, user_id, created_at, expires_at, consumed_at
                ) VALUES (?, ?, ?, ?, NULL)
                """,
                (
                    _digest(issued.token),
                    issued.user_id,
                    _to_iso(issued.created_at),
                    _to_iso(issued.expires_at),
                ),
            )
            conn.commit()

        return issued

    def consume(self, token: str) -> PasswordResetToken | None:
        token_digest = _digest(token)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, created_at, expires_at, consumed_at
                FROM auth_password_reset_tokens
                WHERE token_digest = ?
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
                conn.execute(
                    "UPDATE auth_password_reset_tokens SET consumed_at = ? WHERE token_digest = ?",
                    (_to_iso(self._now_provider()), token_digest),
                )
                conn.commit()
                return None

            updated = conn.execute(
                """
                UPDATE auth_password_reset_tokens
                SET consumed_at = ?
                WHERE token_digest = ? AND consumed_at IS NULL
                """,
                (_to_iso(self._now_provider()), token_digest),
            )
            conn.commit()

            if updated.rowcount <= 0:
                return None

        return PasswordResetToken(
            token=token,
            user_id=user_id,
            created_at=created_at,
            expires_at=expires_at,
        )
