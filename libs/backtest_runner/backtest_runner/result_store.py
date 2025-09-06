"""回测结果存储（in-memory）。"""

from __future__ import annotations

import copy
import threading
from datetime import datetime, timezone
from typing import Any


class InMemoryBacktestResultStore:
    def __init__(self) -> None:
        self._results: dict[str, dict[str, dict[str, Any]]] = {}
        self._lock = threading.RLock()

    def save_result(self, *, user_id: str, task_id: str, result: dict[str, Any]) -> None:
        payload = copy.deepcopy(result)
        payload.setdefault("updatedAt", datetime.now(timezone.utc).isoformat())
        with self._lock:
            bucket = self._results.setdefault(user_id, {})
            bucket[task_id] = payload

    def get_result(self, *, user_id: str, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            item = self._results.get(user_id, {}).get(task_id)
            if item is None:
                return None
            return copy.deepcopy(item)

    def delete_result(self, *, user_id: str, task_id: str) -> bool:
        with self._lock:
            bucket = self._results.get(user_id)
            if not bucket or task_id not in bucket:
                return False
            del bucket[task_id]
            if not bucket:
                self._results.pop(user_id, None)
            return True
