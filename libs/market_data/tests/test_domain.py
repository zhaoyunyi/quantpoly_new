"""market_data 领域测试。"""

from __future__ import annotations

import pytest


def test_quote_repeated_query_hits_cache():
    from market_data.domain import MarketQuote
    from market_data.service import MarketDataService

    class _Provider:
        def __init__(self):
            self.calls = 0

        def search(self, *, keyword: str, limit: int):  # pragma: no cover - not used in this test
            return []

        def quote(self, *, symbol: str) -> MarketQuote:
            self.calls += 1
            return MarketQuote(
                symbol=symbol,
                name=f"{symbol} Inc.",
                price=100.0,
                previous_close=99.0,
                open_price=100.5,
                high_price=101.0,
                low_price=98.5,
                volume=1000.0,
            )

        def history(
            self,
            *,
            symbol: str,
            start_date: str,
            end_date: str,
            timeframe: str,
            limit: int | None,
        ):
            return []

    provider = _Provider()
    service = MarketDataService(provider=provider, quote_cache_ttl_seconds=60, rate_limit_max_requests=10)

    first = service.get_quote(user_id="u-1", symbol="AAPL")
    second = service.get_quote(user_id="u-1", symbol="AAPL")

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert provider.calls == 1


def test_quote_rate_limit_exceeded():
    from market_data.domain import RateLimitExceededError
    from market_data.service import MarketDataService

    class _Provider:
        def search(self, *, keyword: str, limit: int):
            return []

        def quote(self, *, symbol: str):
            from market_data.domain import MarketQuote

            return MarketQuote(
                symbol=symbol,
                name=f"{symbol} Inc.",
                price=100.0,
                previous_close=99.0,
                open_price=100.5,
                high_price=101.0,
                low_price=98.5,
                volume=1000.0,
            )

        def history(
            self,
            *,
            symbol: str,
            start_date: str,
            end_date: str,
            timeframe: str,
            limit: int | None,
        ):
            return []

    service = MarketDataService(
        provider=_Provider(),
        quote_cache_ttl_seconds=0,
        rate_limit_max_requests=1,
        rate_limit_window_seconds=60,
    )

    service.get_quote(user_id="u-1", symbol="AAPL")

    with pytest.raises(RateLimitExceededError) as exc_info:
        service.get_quote(user_id="u-1", symbol="MSFT")

    assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"


def test_alpaca_provider_timeout_maps_to_upstream_timeout_error():
    from market_data.alpaca_provider import AlpacaProvider
    from market_data.domain import UpstreamTimeoutError

    state = {"calls": 0}

    def _transport(_operation: str, **_kwargs):
        state["calls"] += 1
        raise TimeoutError("request timeout")

    provider = AlpacaProvider(transport=_transport, max_retries=2)

    with pytest.raises(UpstreamTimeoutError) as exc_info:
        provider.quote(symbol="AAPL")

    assert exc_info.value.code == "UPSTREAM_TIMEOUT"
    assert exc_info.value.retryable is True
    assert state["calls"] == 3

