"""密码找回/重置 token 管理。"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol


DEFAULT_RESET_TOKEN_TTL_SECONDS = 3600
DEFAULT_RESET_REQUEST_MIN_INTERVAL_SECONDS = 60


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
        now_provider: Callable[[], datetime] = _utc_now,
    ) -> "PasswordResetToken":
        now = now_provider()
        return cls(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )

    @property
    def is_expired(self) -> bool:
        return _utc_now() >= self.expires_at


class PasswordResetStore(Protocol):
    def issue(self, *, user_id: str) -> PasswordResetToken: ...

    def consume(self, token: str) -> PasswordResetToken | None: ...


class InMemoryPasswordResetStore:
    def __init__(
        self,
        *,
        ttl_seconds: int = DEFAULT_RESET_TOKEN_TTL_SECONDS,
        now_provider: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._tokens: dict[str, PasswordResetToken] = {}
        self._ttl_seconds = ttl_seconds
        self._now_provider = now_provider

    def issue(self, *, user_id: str) -> PasswordResetToken:
        token = PasswordResetToken.create(
            user_id=user_id,
            ttl_seconds=self._ttl_seconds,
            now_provider=self._now_provider,
        )
        self._tokens[token.token] = token
        return token

    def consume(self, token: str) -> PasswordResetToken | None:
        reset = self._tokens.get(token)
        if reset is None:
            return None
        if self._now_provider() >= reset.expires_at:
            self._tokens.pop(token, None)
            return None
        self._tokens.pop(token, None)
        return reset


class PasswordResetRequestRateLimiter:
    def __init__(
        self,
        *,
        min_interval_seconds: int = DEFAULT_RESET_REQUEST_MIN_INTERVAL_SECONDS,
        now_provider: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._min_interval = timedelta(seconds=min_interval_seconds)
        self._now_provider = now_provider
        self._last_requests: dict[str, datetime] = {}

    def allow(self, *, key: str) -> bool:
        now = self._now_provider()
        last = self._last_requests.get(key)

        if last is None:
            self._last_requests[key] = now
            return True

        if (now - last) >= self._min_interval:
            self._last_requests[key] = now
            return True

        return False
