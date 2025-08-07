"""market_data API：目录/批量/最新/健康检查测试。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from market_data.api import create_router
from market_data.domain import MarketAsset, MarketQuote, UpstreamTimeoutError
from market_data.service import MarketDataService


class _Provider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        if symbol == "TSLA":
            raise UpstreamTimeoutError()
        return MarketQuote(
            symbol=symbol,
            name=f"{symbol} Inc.",
            price=200.0,
            previous_close=198.0,
            open_price=199.0,
            high_price=201.0,
            low_price=197.5,
            volume=123456.0,
            timestamp=datetime.now(timezone.utc),
        )

    def history(self, *, symbol: str, start_date: str, end_date: str, timeframe: str, limit: int | None):
        del symbol, start_date, end_date, timeframe, limit
        return []

    def list_assets(self, *, limit: int):
        return [
            MarketAsset(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ"),
            MarketAsset(symbol="MSFT", name="Microsoft", exchange="NASDAQ"),
        ][:limit]

    def batch_quote(self, *, symbols: list[str]):
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
            "healthy": False,
            "status": "degraded",
            "message": "rate limited",
        }


def _build_app() -> TestClient:
    class _User:
        id = "u-1"

    def _get_current_user():
        return _User()

    service = MarketDataService(provider=_Provider(), quote_cache_ttl_seconds=60)
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return TestClient(app)


def test_catalog_and_symbols_endpoints():
    client = _build_app()

    catalog = client.get("/market/catalog", params={"limit": 2})
    symbols = client.get("/market/symbols", params={"limit": 2})

    assert catalog.status_code == 200
    assert catalog.json()["success"] is True
    assert len(catalog.json()["data"]["items"]) == 2

    assert symbols.status_code == 200
    assert symbols.json()["success"] is True
    assert symbols.json()["data"]["items"] == ["AAPL", "MSFT"]


def test_batch_quotes_and_latest_endpoint_semantics():
    client = _build_app()

    batch = client.post("/market/quotes", json={"symbols": ["aapl", "msft"]})
    latest_first = client.get("/market/latest/AAPL")
    latest_second = client.get("/market/latest/AAPL")

    assert batch.status_code == 200
    assert batch.json()["success"] is True
    items = batch.json()["data"]["items"]
    assert len(items) == 2
    assert items[0]["symbol"] == "AAPL"
    assert items[0]["status"] == "ok"
    assert items[1]["symbol"] == "MSFT"
    assert items[1]["status"] == "error"
    assert items[1]["errorCode"] == "QUOTE_NOT_AVAILABLE"

    assert latest_first.status_code == 200
    assert latest_first.json()["data"]["metadata"]["source"] == "cache"
    assert latest_second.json()["data"]["metadata"]["cacheHit"] is True


def test_provider_health_endpoint_and_retryable_error_field():
    client = _build_app()

    health = client.get("/market/provider-health")
    timeout = client.get("/market/latest/TSLA")

    assert health.status_code == 200
    assert health.json()["data"]["healthy"] is False
    assert health.json()["data"]["status"] == "degraded"

    assert timeout.status_code == 504
    assert timeout.json()["success"] is False
    assert timeout.json()["error"]["code"] == "UPSTREAM_TIMEOUT"
    assert timeout.json()["error"]["retryable"] is True
