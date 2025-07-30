"""市场数据应用服务（含缓存与限流）。"""

from __future__ import annotations

from dataclasses import dataclass

from market_data.cache import InMemoryTTLCache
from market_data.domain import (
    MarketAsset,
    MarketCandle,
    MarketQuote,
    RateLimitExceededError,
    UpstreamUnavailableError,
)
from market_data.provider import MarketDataProvider
from market_data.rate_limit import SlidingWindowRateLimiter


@dataclass
class QuoteResult:
    quote: MarketQuote
    cache_hit: bool


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

    def search_assets(self, *, user_id: str, keyword: str, limit: int = 10) -> list[MarketAsset]:
        del user_id
        return self._provider.search(keyword=keyword, limit=limit)

    def get_quote(self, *, user_id: str, symbol: str) -> QuoteResult:
        normalized_symbol = symbol.upper()
        limit_key = f"quote:{user_id}"
        if not self._quote_rate_limiter.consume(limit_key):
            raise RateLimitExceededError()

        cache_key = f"quote:{normalized_symbol}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return QuoteResult(quote=cached, cache_hit=True)

        try:
            quote = self._provider.quote(symbol=normalized_symbol)
        except Exception as exc:
            if hasattr(exc, "code"):
                raise
            raise UpstreamUnavailableError(str(exc)) from exc

        self._cache.set(cache_key, quote, ttl_seconds=self._quote_cache_ttl_seconds)
        return QuoteResult(quote=quote, cache_hit=False)

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
