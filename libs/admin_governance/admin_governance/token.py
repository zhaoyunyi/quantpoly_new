"""高风险动作确认令牌。"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable


@dataclass
class ConfirmationToken:
    token: str
    actor_id: str
    action: str
    target: str
    expires_at: datetime
    used: bool = False


class InMemoryConfirmationTokenStore:
    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._tokens: dict[str, ConfirmationToken] = {}

    def issue(
        self,
        *,
        actor_id: str,
        action: str,
        target: str,
        ttl_seconds: int = 300,
    ) -> str:
        token = secrets.token_urlsafe(24)
        self._tokens[token] = ConfirmationToken(
            token=token,
            actor_id=actor_id,
            action=action,
            target=target,
            expires_at=self._clock() + timedelta(seconds=ttl_seconds),
        )
        return token

    def consume(
        self,
        *,
        token: str,
        actor_id: str,
        action: str,
        target: str,
    ) -> bool:
        found = self._tokens.get(token)
        if found is None:
            return False
        if found.used:
            return False
        if self._clock() >= found.expires_at:
            return False
        if found.actor_id != actor_id or found.action != action or found.target != target:
            return False

        found.used = True
        self._tokens[token] = found
        return True
