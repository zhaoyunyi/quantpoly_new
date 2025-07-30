"""Alpaca Provider 适配（带超时重试与错误映射）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from market_data.domain import (
    MarketAsset,
    MarketCandle,
    MarketQuote,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

Transport = Callable[..., Any]


class AlpacaProvider:
    def __init__(
        self,
        *,
        transport: Transport,
        max_retries: int = 1,
    ) -> None:
        self._transport = transport
        self._max_retries = max_retries

    def _call_with_retry(self, operation: str, **kwargs):
        for attempt in range(self._max_retries + 1):
            try:
                return self._transport(operation, **kwargs)
            except TimeoutError as exc:
                if attempt >= self._max_retries:
                    raise UpstreamTimeoutError() from exc
            except Exception as exc:  # pragma: no cover
                raise UpstreamUnavailableError(str(exc)) from exc

        raise UpstreamTimeoutError()

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        return float(value)

    @staticmethod
    def _to_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            text = value.replace("Z", "+00:00")
            return datetime.fromisoformat(text)
        return datetime.now(timezone.utc)

    def search(self, *, keyword: str, limit: int) -> list[MarketAsset]:
        payload = self._call_with_retry("search", keyword=keyword, limit=limit)
        items = payload.get("items", payload if isinstance(payload, list) else [])

        result: list[MarketAsset] = []
        for item in items:
            symbol = str(item.get("symbol", "")).upper()
            if not symbol:
                continue
            result.append(
                MarketAsset(
                    symbol=symbol,
                    name=item.get("name", symbol),
                    exchange=item.get("exchange"),
                    currency=item.get("currency", "USD"),
                    asset_class=item.get("assetClass", "us_equity"),
                    tradable=bool(item.get("tradable", True)),
                    fractionable=bool(item.get("fractionable", False)),
                )
            )

        return result[:limit]

    def quote(self, *, symbol: str) -> MarketQuote:
        payload = self._call_with_retry("quote", symbol=symbol.upper())
        return MarketQuote(
            symbol=symbol.upper(),
            name=payload.get("name", symbol.upper()),
            price=self._to_float(payload.get("price")),
            previous_close=self._to_float(payload.get("previousClose")),
            open_price=self._to_float(payload.get("open")),
            high_price=self._to_float(payload.get("high")),
            low_price=self._to_float(payload.get("low")),
            volume=self._to_float(payload.get("volume")),
            bid_price=self._to_float(payload.get("bidPrice")),
            ask_price=self._to_float(payload.get("askPrice")),
            timestamp=self._to_datetime(payload.get("timestamp")),
        )

    def history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ) -> list[MarketCandle]:
        payload = self._call_with_retry(
            "history",
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            limit=limit,
        )
        rows = payload.get("items", payload if isinstance(payload, list) else [])
        candles: list[MarketCandle] = []
        for row in rows:
            candles.append(
                MarketCandle(
                    timestamp=self._to_datetime(row.get("timestamp")),
                    open_price=float(row.get("open", 0)),
                    high_price=float(row.get("high", 0)),
                    low_price=float(row.get("low", 0)),
                    close_price=float(row.get("close", 0)),
                    volume=float(row.get("volume", 0)),
                )
            )
        return candles
