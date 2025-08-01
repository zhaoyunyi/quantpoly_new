"""Celery 兼容适配器。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class CeleryJobAdapter:
    def __init__(self, *, dispatcher: Callable[[str, dict[str, Any]], str]) -> None:
        self._dispatcher = dispatcher

    def dispatch(self, *, task_type: str, payload: dict[str, Any]) -> str:
        return self._dispatcher(task_type, payload)
