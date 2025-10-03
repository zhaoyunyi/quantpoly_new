"""market_data 资产详情与目录过滤测试。"""

from __future__ import annotations

import pytest

from market_data.domain import MarketAsset, MarketDataError
from market_data.service import MarketDataService


class _Provider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        raise RuntimeError("unused")

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


def test_service_should_filter_catalog_by_market_and_asset_class():
    service = MarketDataService(provider=_Provider())

    nasdaq = service.list_catalog(user_id="u-1", limit=10, market="NASDAQ")
    crypto = service.list_catalog(user_id="u-1", limit=10, asset_class="crypto")

    assert len(nasdaq) == 2
    assert {item.symbol for item in nasdaq} == {"AAPL", "MSFT"}

    assert len(crypto) == 1
    assert crypto[0].symbol == "BTCUSD"


def test_service_should_return_catalog_asset_detail():
    service = MarketDataService(provider=_Provider())

    detail = service.get_catalog_asset_detail(user_id="u-1", symbol="aapl")

    assert detail.symbol == "AAPL"
    assert detail.name == "Apple"
    assert detail.exchange == "NASDAQ"
    assert detail.asset_class == "us_equity"


def test_service_should_raise_asset_not_found_error():
    service = MarketDataService(provider=_Provider())

    with pytest.raises(MarketDataError) as exc_info:
        service.get_catalog_asset_detail(user_id="u-1", symbol="TSLA")

    assert exc_info.value.code == "ASSET_NOT_FOUND"
