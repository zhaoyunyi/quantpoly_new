"""会话管理模块。

提供 opaque session token 的创建、查询、撤销与过期管理。
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

DEFAULT_TTL_SECONDS = 86400 * 7  # 7 天


@dataclass
class Session:
    """会话模型。"""

    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime

    @classmethod
    def create(
        cls,
        user_id: str,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> "Session":
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


class SessionStore:
    """内存会话存储（生产环境应替换为数据库实现）。"""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def save(self, session: Session) -> None:
        self._sessions[session.token] = session

    def get_by_token(self, token: str) -> Session | None:
        session = self._sessions.get(token)
        if session is None:
            return None
        if session.is_expired:
            del self._sessions[token]
            return None
        return session

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)

    def revoke_by_user(self, *, user_id: str) -> int:
        tokens = [item.token for item in self._sessions.values() if item.user_id == user_id]
        for token in tokens:
            self._sessions.pop(token, None)
        return len(tokens)
