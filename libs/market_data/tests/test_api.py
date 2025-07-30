"""market_data API 路由测试。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, provider, rate_limit_max_requests: int = 20, quote_cache_ttl_seconds: int = 3):
    from market_data.api import create_router
    from market_data.service import MarketDataService

    class _User:
        def __init__(self):
            self.id = "u-1"

    def _get_current_user():
        return _User()

    service = MarketDataService(
        provider=provider,
        rate_limit_max_requests=rate_limit_max_requests,
        quote_cache_ttl_seconds=quote_cache_ttl_seconds,
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app


def test_quote_endpoint_returns_cache_hit_metadata():
    from market_data.domain import MarketQuote

    class _Provider:
        def __init__(self):
            self.calls = 0

        def search(self, *, keyword: str, limit: int):
            return []

        def quote(self, *, symbol: str):
            self.calls += 1
            return MarketQuote(
                symbol=symbol,
                name=f"{symbol} Inc.",
                price=123.0,
                previous_close=120.0,
                open_price=121.0,
                high_price=124.0,
                low_price=119.5,
                volume=12345.0,
                timestamp=datetime.now(timezone.utc),
            )

        def history(self, *, symbol: str, start_date: str, end_date: str, timeframe: str, limit: int | None):
            return []

    provider = _Provider()
    app = _build_app(provider=provider)
    client = TestClient(app)

    first = client.get("/market/quote/AAPL")
    second = client.get("/market/quote/AAPL")

    assert first.status_code == 200
    assert first.json()["success"] is True
    assert first.json()["data"]["metadata"]["cacheHit"] is False

    assert second.status_code == 200
    assert second.json()["success"] is True
    assert second.json()["data"]["metadata"]["cacheHit"] is True
    assert provider.calls == 1


def test_quote_endpoint_provider_timeout_returns_standard_error():
    from market_data.domain import UpstreamTimeoutError

    class _Provider:
        def search(self, *, keyword: str, limit: int):
            return []

        def quote(self, *, symbol: str):
            raise UpstreamTimeoutError()

        def history(self, *, symbol: str, start_date: str, end_date: str, timeframe: str, limit: int | None):
            return []

    app = _build_app(provider=_Provider())
    client = TestClient(app)

    resp = client.get("/market/quote/AAPL")

    assert resp.status_code == 504
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UPSTREAM_TIMEOUT"


def test_quote_endpoint_rate_limit_returns_standard_error():
    from market_data.domain import MarketQuote

    class _Provider:
        def search(self, *, keyword: str, limit: int):
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
            )

        def history(self, *, symbol: str, start_date: str, end_date: str, timeframe: str, limit: int | None):
            return []

    app = _build_app(provider=_Provider(), rate_limit_max_requests=1, quote_cache_ttl_seconds=0)
    client = TestClient(app)

    first = client.get("/market/quote/AAPL")
    second = client.get("/market/quote/MSFT")

    assert first.status_code == 200
    assert second.status_code == 429
    payload = second.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "RATE_LIMIT_EXCEEDED"

