"""market_data 数据管道读模型存储。

当前实现为内存存储，用于迁移期的任务化能力补齐。
后续可替换为 SQLite/Postgres 等持久化实现。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class SyncedSymbolRecord:
    user_id: str
    symbol: str
    start_date: str
    end_date: str
    timeframe: str
    row_count: int
    synced_at: datetime


class InMemoryMarketDataPipelineStore:
    def __init__(self) -> None:
        self._synced_symbols: dict[str, dict[str, SyncedSymbolRecord]] = {}
        self._sync_results: dict[str, dict[str, dict[str, Any]]] = {}

    def record_synced_symbol(
        self,
        *,
        user_id: str,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        row_count: int,
    ) -> SyncedSymbolRecord:
        record = SyncedSymbolRecord(
            user_id=user_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            row_count=row_count,
            synced_at=datetime.now(timezone.utc),
        )
        bucket = self._synced_symbols.setdefault(user_id, {})
        bucket[symbol] = record
        return record

    def list_synced_symbols(self, *, user_id: str) -> list[str]:
        bucket = self._synced_symbols.get(user_id, {})
        return sorted(bucket.keys())

    def record_sync_result(self, *, user_id: str, task_id: str, result: dict[str, Any]) -> None:
        bucket = self._sync_results.setdefault(user_id, {})
        bucket[task_id] = dict(result)

    def get_sync_result(self, *, user_id: str, task_id: str) -> dict[str, Any] | None:
        return self._sync_results.get(user_id, {}).get(task_id)

