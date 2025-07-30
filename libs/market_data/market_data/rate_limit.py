"""简易滑动窗口限流器。"""

from __future__ import annotations

import time
from collections import deque


class SlidingWindowRateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: int, clock=time.monotonic) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._events: dict[str, deque[float]] = {}

    def consume(self, key: str) -> bool:
        now = self._clock()
        events = self._events.setdefault(key, deque())
        lower_bound = now - self._window_seconds

        while events and events[0] <= lower_bound:
            events.popleft()

        if len(events) >= self._max_requests:
            return False

        events.append(now)
        return True
