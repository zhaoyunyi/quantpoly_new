"""market_data API 资产详情与目录过滤测试。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from market_data.api import create_router
from market_data.domain import MarketAsset, MarketQuote
from market_data.service import MarketDataService


class _Provider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        return MarketQuote(symbol=symbol, name=symbol, price=1.0, timestamp=datetime.now(timezone.utc))

    def history(self, *, symbol: str, start_date: str, end_date: str, timeframe: str, limit: int | None):
        del symbol, start_date, end_date, timeframe, limit
        return []

    def list_assets(self, *, limit: int):
        return [
            MarketAsset(symbol="AAPL", name="Apple", exchange="NASDAQ", asset_class="us_equity", tradable=True),
            MarketAsset(symbol="MSFT", name="Microsoft", exchange="NASDAQ", asset_class="us_equity", tradable=True),
            MarketAsset(symbol="BTCUSD", name="Bitcoin", exchange="CRYPTO", asset_class="crypto", tradable=False),
        ][:limit]

    def health(self):
        return {"provider": "fake", "healthy": True, "status": "ok", "message": ""}


def _build_client() -> TestClient:
    class _User:
        id = "u-1"

    def _get_current_user(request=None):
        return _User()

    service = MarketDataService(provider=_Provider())
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return TestClient(app)


def test_api_catalog_should_support_market_and_asset_class_filters():
    client = _build_client()

    nasdaq = client.get("/market/catalog", params={"market": "NASDAQ", "limit": 10})
    crypto = client.get("/market/catalog", params={"assetClass": "crypto", "limit": 10})

    assert nasdaq.status_code == 200
    assert nasdaq.json()["success"] is True
    assert len(nasdaq.json()["data"]["items"]) == 2

    assert crypto.status_code == 200
    assert crypto.json()["success"] is True
    assert len(crypto.json()["data"]["items"]) == 1
    assert crypto.json()["data"]["items"][0]["symbol"] == "BTCUSD"


def test_api_should_return_catalog_asset_detail_and_status_field():
    client = _build_client()

    resp = client.get("/market/catalog/AAPL")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["asset"]["symbol"] == "AAPL"
    assert payload["data"]["asset"]["exchange"] == "NASDAQ"
    assert payload["data"]["asset"]["assetClass"] == "us_equity"
    assert payload["data"]["asset"]["status"] in {"active", "inactive"}


def test_api_should_return_not_found_for_unknown_catalog_symbol():
    client = _build_client()

    resp = client.get("/market/catalog/TSLA")

    assert resp.status_code == 404
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ASSET_NOT_FOUND"
