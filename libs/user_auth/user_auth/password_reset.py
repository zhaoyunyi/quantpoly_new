"""密码找回/重置 token 管理。"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


DEFAULT_RESET_TOKEN_TTL_SECONDS = 3600


@dataclass
class PasswordResetToken:
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        ttl_seconds: int = DEFAULT_RESET_TOKEN_TTL_SECONDS,
    ) -> "PasswordResetToken":
        now = datetime.now(timezone.utc)
        return cls(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


class InMemoryPasswordResetStore:
    def __init__(self) -> None:
        self._tokens: dict[str, PasswordResetToken] = {}

    def issue(self, *, user_id: str) -> PasswordResetToken:
        token = PasswordResetToken.create(user_id=user_id)
        self._tokens[token.token] = token
        return token

    def consume(self, token: str) -> PasswordResetToken | None:
        reset = self._tokens.get(token)
        if reset is None:
            return None
        if reset.is_expired:
            self._tokens.pop(token, None)
            return None
        self._tokens.pop(token, None)
        return reset

