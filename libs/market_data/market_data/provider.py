"""市场数据 Provider 协议。"""

from __future__ import annotations

from typing import Any, Protocol

from market_data.domain import MarketAsset, MarketCandle, MarketQuote


class MarketDataProvider(Protocol):
    def search(self, *, keyword: str, limit: int) -> list[MarketAsset]:
        ...

    def quote(self, *, symbol: str) -> MarketQuote:
        ...

    def history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ) -> list[MarketCandle]:
        ...

    def list_assets(self, *, limit: int) -> list[MarketAsset]:
        ...

    def batch_quote(self, *, symbols: list[str]) -> dict[str, MarketQuote]:
        ...

    def health(self) -> dict[str, Any]:
        ...
