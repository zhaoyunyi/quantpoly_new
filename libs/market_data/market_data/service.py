"""市场数据应用服务（含缓存与限流）。"""

from __future__ import annotations

import time
from dataclasses import dataclass

from market_data.cache import InMemoryTTLCache
from market_data.domain import (
    BatchQuoteItem,
    MarketAsset,
    MarketCandle,
    MarketDataError,
    MarketQuote,
    RateLimitExceededError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from market_data.provider import MarketDataProvider
from market_data.rate_limit import SlidingWindowRateLimiter


@dataclass
class QuoteResult:
    quote: MarketQuote
    cache_hit: bool
    source: str = "provider"


@dataclass
class BatchQuoteResult:
    items: list[BatchQuoteItem]
    timestamp: int


class MarketDataService:
    def __init__(
        self,
        *,
        provider: MarketDataProvider,
        quote_cache_ttl_seconds: int = 3,
        rate_limit_max_requests: int = 20,
        rate_limit_window_seconds: int = 10,
        cache: InMemoryTTLCache | None = None,
        quote_rate_limiter: SlidingWindowRateLimiter | None = None,
    ) -> None:
        self._provider = provider
        self._quote_cache_ttl_seconds = quote_cache_ttl_seconds
        self._cache = cache or InMemoryTTLCache()
        self._quote_rate_limiter = quote_rate_limiter or SlidingWindowRateLimiter(
            max_requests=rate_limit_max_requests,
            window_seconds=rate_limit_window_seconds,
        )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper()

    def _normalize_symbols(self, symbols: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for symbol in symbols:
            normalized = self._normalize_symbol(symbol)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    def _consume_quote_limit(self, *, user_id: str) -> None:
        limit_key = f"quote:{user_id}"
        if not self._quote_rate_limiter.consume(limit_key):
            raise RateLimitExceededError()

    def _map_provider_error(self, exc: Exception) -> MarketDataError:
        if isinstance(exc, MarketDataError):
            return exc
        if isinstance(exc, TimeoutError):
            return UpstreamTimeoutError(str(exc))
        return UpstreamUnavailableError(str(exc))

    def search_assets(self, *, user_id: str, keyword: str, limit: int = 10) -> list[MarketAsset]:
        del user_id
        return self._provider.search(keyword=keyword, limit=limit)

    def list_catalog(self, *, user_id: str, limit: int = 100) -> list[MarketAsset]:
        del user_id
        if hasattr(self._provider, "list_assets"):
            items = self._provider.list_assets(limit=limit)
        else:
            items = self._provider.search(keyword="", limit=limit)

        result: list[MarketAsset] = []
        for item in items:
            normalized = self._normalize_symbol(item.symbol)
            if not normalized:
                continue
            if normalized != item.symbol:
                item = MarketAsset(
                    symbol=normalized,
                    name=item.name,
                    exchange=item.exchange,
                    currency=item.currency,
                    asset_class=item.asset_class,
                    tradable=item.tradable,
                    fractionable=item.fractionable,
                )
            result.append(item)

        return result[:limit]

    def list_symbols(self, *, user_id: str, limit: int = 100) -> list[str]:
        items = self.list_catalog(user_id=user_id, limit=limit)
        return [item.symbol for item in items]

    def get_latest_quote(self, *, user_id: str, symbol: str) -> QuoteResult:
        normalized_symbol = self._normalize_symbol(symbol)
        self._consume_quote_limit(user_id=user_id)

        cache_key = f"quote:{normalized_symbol}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return QuoteResult(quote=cached, cache_hit=True, source="cache")

        try:
            quote = self._provider.quote(symbol=normalized_symbol)
        except Exception as exc:  # noqa: BLE001
            raise self._map_provider_error(exc) from exc

        self._cache.set(cache_key, quote, ttl_seconds=self._quote_cache_ttl_seconds)
        return QuoteResult(quote=quote, cache_hit=False, source="provider")

    def get_quote(self, *, user_id: str, symbol: str) -> QuoteResult:
        return self.get_latest_quote(user_id=user_id, symbol=symbol)

    def get_quotes(self, *, user_id: str, symbols: list[str]) -> BatchQuoteResult:
        normalized_symbols = self._normalize_symbols(symbols)
        timestamp = int(time.time())
        if not normalized_symbols:
            return BatchQuoteResult(items=[], timestamp=timestamp)

        self._consume_quote_limit(user_id=user_id)

        cached_quotes: dict[str, MarketQuote] = {}
        missed_symbols: list[str] = []
        for symbol in normalized_symbols:
            cache_key = f"quote:{symbol}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                cached_quotes[symbol] = cached
            else:
                missed_symbols.append(symbol)

        fetched_quotes: dict[str, MarketQuote] = {}
        if missed_symbols:
            try:
                if hasattr(self._provider, "batch_quote"):
                    fetched_quotes = self._provider.batch_quote(symbols=missed_symbols)
                else:
                    fetched_quotes = {symbol: self._provider.quote(symbol=symbol) for symbol in missed_symbols}
            except Exception as exc:  # noqa: BLE001
                raise self._map_provider_error(exc) from exc

            for symbol, quote in fetched_quotes.items():
                cache_key = f"quote:{self._normalize_symbol(symbol)}"
                self._cache.set(cache_key, quote, ttl_seconds=self._quote_cache_ttl_seconds)

        items: list[BatchQuoteItem] = []
        for symbol in normalized_symbols:
            if symbol in cached_quotes:
                items.append(
                    BatchQuoteItem(
                        symbol=symbol,
                        quote=cached_quotes[symbol],
                        status="ok",
                        cache_hit=True,
                        source="cache",
                    )
                )
                continue

            quote = fetched_quotes.get(symbol)
            if quote is None:
                items.append(
                    BatchQuoteItem(
                        symbol=symbol,
                        status="error",
                        error_code="QUOTE_NOT_AVAILABLE",
                        error_message=f"quote not available for {symbol}",
                        cache_hit=False,
                        source="provider",
                    )
                )
                continue

            items.append(
                BatchQuoteItem(
                    symbol=symbol,
                    quote=quote,
                    status="ok",
                    cache_hit=False,
                    source="provider",
                )
            )

        return BatchQuoteResult(items=items, timestamp=timestamp)

    def provider_health(self, *, user_id: str) -> dict:
        del user_id
        payload: dict = {
            "provider": self._provider.__class__.__name__.replace("Provider", "").lower() or "unknown",
            "healthy": False,
            "status": "unknown",
            "message": "provider health not available",
        }

        if hasattr(self._provider, "health"):
            try:
                raw = self._provider.health()
                if isinstance(raw, dict):
                    payload.update(raw)
            except Exception as exc:  # noqa: BLE001
                payload.update(
                    {
                        "healthy": False,
                        "status": "degraded",
                        "message": str(exc),
                    }
                )

        payload["timestamp"] = int(time.time())
        return payload

    def get_history(
        self,
        *,
        user_id: str,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1Day",
        limit: int | None = None,
    ) -> list[MarketCandle]:
        del user_id
        return self._provider.history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            limit=limit,
        )
