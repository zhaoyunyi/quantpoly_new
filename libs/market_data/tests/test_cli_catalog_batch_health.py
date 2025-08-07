"""market_data CLI：目录/批量/最新/健康检查命令测试。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from market_data import cli
from market_data.domain import MarketAsset, MarketQuote
from market_data.service import MarketDataService


class _Provider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        return MarketQuote(
            symbol=symbol,
            name=f"{symbol} Inc.",
            price=150.0,
            previous_close=149.0,
            open_price=149.5,
            high_price=151.0,
            low_price=148.0,
            volume=10000.0,
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
            MarketAsset(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ"),
            MarketAsset(symbol="MSFT", name="Microsoft", exchange="NASDAQ"),
        ][:limit]

    def batch_quote(self, *, symbols: list[str]):
        return {
            "AAPL": MarketQuote(
                symbol="AAPL",
                name="Apple Inc.",
                price=188.0,
                previous_close=186.0,
                open_price=187.0,
                high_price=189.0,
                low_price=185.0,
                volume=22000.0,
                timestamp=datetime.now(timezone.utc),
            )
        }

    def health(self):
        return {
            "provider": "fake",
            "healthy": True,
            "status": "ok",
            "message": "",
        }


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_catalog_symbols_quotes_latest_and_provider_health(capsys, monkeypatch):
    service = MarketDataService(provider=_Provider(), quote_cache_ttl_seconds=60)
    monkeypatch.setattr(cli, "_service", service)

    catalog = _run(cli._cmd_catalog, capsys=capsys, user_id="u-1", limit=2)
    symbols = _run(cli._cmd_symbols, capsys=capsys, user_id="u-1", limit=2)
    quotes = _run(cli._cmd_quotes, capsys=capsys, user_id="u-1", symbols="aapl,msft")
    latest = _run(cli._cmd_latest, capsys=capsys, user_id="u-1", symbol="AAPL")
    health = _run(cli._cmd_provider_health, capsys=capsys, user_id="u-1")

    assert catalog["success"] is True
    assert len(catalog["data"]["items"]) == 2

    assert symbols["success"] is True
    assert symbols["data"]["items"] == ["AAPL", "MSFT"]

    assert quotes["success"] is True
    assert quotes["data"]["items"][0]["symbol"] == "AAPL"
    assert quotes["data"]["items"][1]["symbol"] == "MSFT"
    assert quotes["data"]["items"][1]["status"] == "error"

    assert latest["success"] is True
    assert latest["data"]["metadata"]["source"] == "cache"

    assert health["success"] is True
    assert health["data"]["status"] == "ok"
