"""交易运营读模型存储。

用于在迁移期以最小成本支持“日统计”等运营视图读取。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class TradingOperationsStore(Protocol):
    def save_daily_stats(self, *, user_id: str, date: str, account_id: str, snapshot: dict[str, Any]) -> None: ...

    def get_daily_stats(self, *, user_id: str, date: str, account_id: str) -> dict[str, Any] | None: ...


@dataclass
class InMemoryTradingOperationsStore:
    def __init__(self) -> None:
        self._daily_stats: dict[tuple[str, str, str], dict[str, Any]] = {}

    def save_daily_stats(self, *, user_id: str, date: str, account_id: str, snapshot: dict[str, Any]) -> None:
        self._daily_stats[(user_id, date, account_id)] = dict(snapshot)

    def get_daily_stats(self, *, user_id: str, date: str, account_id: str) -> dict[str, Any] | None:
        payload = self._daily_stats.get((user_id, date, account_id))
        if payload is None:
            return None
        return dict(payload)

