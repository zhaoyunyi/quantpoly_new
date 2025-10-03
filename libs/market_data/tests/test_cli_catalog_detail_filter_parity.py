"""market_data CLI 资产详情与目录过滤测试。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import pytest

from market_data import cli
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


@pytest.fixture(autouse=True)
def _reset_service(monkeypatch):
    monkeypatch.setattr(cli, "_service", MarketDataService(provider=_Provider()))


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_catalog_should_support_filters(capsys):
    nasdaq = _run(
        cli._cmd_catalog,
        capsys=capsys,
        user_id="u-1",
        limit=10,
        market="NASDAQ",
        asset_class=None,
    )
    crypto = _run(
        cli._cmd_catalog,
        capsys=capsys,
        user_id="u-1",
        limit=10,
        market=None,
        asset_class="crypto",
    )

    assert nasdaq["success"] is True
    assert len(nasdaq["data"]["items"]) == 2

    assert crypto["success"] is True
    assert len(crypto["data"]["items"]) == 1
    assert crypto["data"]["items"][0]["symbol"] == "BTCUSD"


def test_cli_should_return_catalog_detail(capsys):
    detail = _run(
        cli._cmd_catalog_detail,
        capsys=capsys,
        user_id="u-1",
        symbol="AAPL",
    )

    assert detail["success"] is True
    assert detail["data"]["asset"]["symbol"] == "AAPL"
    assert detail["data"]["asset"]["status"] in {"active", "inactive"}
