"""简易 TTL 缓存。"""

from __future__ import annotations

import time
from typing import Any


class InMemoryTTLCache:
    def __init__(self, *, clock=time.monotonic) -> None:
        self._clock = clock
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if self._clock() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        expires_at = self._clock() + max(ttl_seconds, 0)
        self._store[key] = (expires_at, value)
