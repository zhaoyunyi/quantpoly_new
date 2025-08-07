"""market_data 目录/批量/最新行情测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from market_data.domain import MarketAsset, MarketQuote, RateLimitExceededError
from market_data.service import MarketDataService


class _Provider:
    def __init__(self):
        self.batch_calls = 0

    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        return MarketQuote(
            symbol=symbol,
            name=f"{symbol} Inc.",
            price=100.0,
            previous_close=99.0,
            open_price=99.5,
            high_price=101.0,
            low_price=98.0,
            volume=1000.0,
            timestamp=datetime.now(timezone.utc),
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
        del symbol, start_date, end_date, timeframe, limit
        return []

    def list_assets(self, *, limit: int):
        return [
            MarketAsset(symbol="aapl", name="Apple Inc.", exchange="NASDAQ"),
            MarketAsset(symbol="MSFT", name="Microsoft Corporation", exchange="NASDAQ"),
        ][:limit]

    def batch_quote(self, *, symbols: list[str]):
        self.batch_calls += 1
        result: dict[str, MarketQuote] = {}
        for symbol in symbols:
            if symbol == "AAPL":
                result[symbol] = MarketQuote(
                    symbol=symbol,
                    name="Apple Inc.",
                    price=188.0,
                    previous_close=186.0,
                    open_price=187.0,
                    high_price=189.0,
                    low_price=185.0,
                    volume=22000.0,
                    timestamp=datetime.now(timezone.utc),
                )
        return result

    def health(self):
        return {
            "provider": "fake",
            "healthy": True,
            "status": "ok",
            "message": "",
        }


def test_catalog_and_symbols_queries_are_supported():
    service = MarketDataService(provider=_Provider())

    catalog = service.list_catalog(user_id="u-1", limit=10)
    symbols = service.list_symbols(user_id="u-1", limit=10)

    assert len(catalog) == 2
    assert symbols == ["AAPL", "MSFT"]


def test_batch_quotes_and_latest_quote_source_semantics():
    provider = _Provider()
    service = MarketDataService(provider=provider, quote_cache_ttl_seconds=60, rate_limit_max_requests=10)

    batch = service.get_quotes(user_id="u-1", symbols=["aapl", "msft"])
    by_symbol = {item.symbol: item for item in batch.items}

    assert by_symbol["AAPL"].status == "ok"
    assert by_symbol["AAPL"].source == "provider"
    assert by_symbol["AAPL"].cache_hit is False
    assert by_symbol["MSFT"].status == "error"
    assert by_symbol["MSFT"].error_code == "QUOTE_NOT_AVAILABLE"

    first = service.get_latest_quote(user_id="u-1", symbol="AAPL")
    second = service.get_latest_quote(user_id="u-1", symbol="AAPL")

    assert first.source == "cache"
    assert second.source == "cache"
    assert provider.batch_calls == 1


def test_batch_quote_rate_limit_exceeded():
    service = MarketDataService(
        provider=_Provider(),
        quote_cache_ttl_seconds=0,
        rate_limit_max_requests=1,
        rate_limit_window_seconds=60,
    )

    service.get_quotes(user_id="u-1", symbols=["AAPL"])

    with pytest.raises(RateLimitExceededError) as exc_info:
        service.get_quotes(user_id="u-1", symbols=["MSFT"])

    assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"

