"""market_data CLI 测试。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from market_data import cli
from market_data.domain import MarketAsset, MarketCandle, MarketQuote
from market_data.service import MarketDataService


class _Provider:
    def search(self, *, keyword: str, limit: int):
        return [
            MarketAsset(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ"),
            MarketAsset(symbol="MSFT", name="Microsoft Corporation", exchange="NASDAQ"),
        ][:limit]

    def quote(self, *, symbol: str):
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
        return [
            MarketCandle(
                timestamp=datetime(2026, 2, 1, tzinfo=timezone.utc),
                open_price=100.0,
                high_price=110.0,
                low_price=95.0,
                close_price=108.0,
                volume=10000.0,
            )
        ]


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_search_outputs_items(capsys, monkeypatch):
    service = MarketDataService(provider=_Provider())
    monkeypatch.setattr(cli, "_service", service)

    data = _run(cli._cmd_search, capsys=capsys, user_id="u-1", keyword="aa", limit=2)

    assert data["success"] is True
    assert len(data["data"]["items"]) == 2
    assert data["data"]["items"][0]["symbol"] == "AAPL"


def test_cli_quote_outputs_cache_metadata(capsys, monkeypatch):
    service = MarketDataService(provider=_Provider(), quote_cache_ttl_seconds=60)
    monkeypatch.setattr(cli, "_service", service)

    first = _run(cli._cmd_quote, capsys=capsys, user_id="u-1", symbol="AAPL")
    second = _run(cli._cmd_quote, capsys=capsys, user_id="u-1", symbol="AAPL")

    assert first["success"] is True
    assert first["data"]["metadata"]["cacheHit"] is False
    assert second["data"]["metadata"]["cacheHit"] is True


def test_cli_history_outputs_items(capsys, monkeypatch):
    service = MarketDataService(provider=_Provider())
    monkeypatch.setattr(cli, "_service", service)

    data = _run(
        cli._cmd_history,
        capsys=capsys,
        user_id="u-1",
        symbol="AAPL",
        start_date="2026-01-01",
        end_date="2026-02-01",
        timeframe="1Day",
        limit=10,
    )

    assert data["success"] is True
    assert data["data"]["symbol"] == "AAPL"
    assert len(data["data"]["items"]) == 1




def test_cli_history_provider_timeout_outputs_standard_error(capsys, monkeypatch):
    class _TimeoutProvider:
        def search(self, *, keyword: str, limit: int):
            del keyword, limit
            return []

        def quote(self, *, symbol: str):
            return MarketQuote(
                symbol=symbol,
                name=f"{symbol} Inc.",
                price=1.0,
                previous_close=1.0,
                open_price=1.0,
                high_price=1.0,
                low_price=1.0,
                volume=1.0,
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
            raise TimeoutError("provider timeout")

    service = MarketDataService(provider=_TimeoutProvider())
    monkeypatch.setattr(cli, "_service", service)

    payload = _run(
        cli._cmd_history,
        capsys=capsys,
        user_id="u-1",
        symbol="AAPL",
        start_date="2026-01-01",
        end_date="2026-02-01",
        timeframe="1Day",
        limit=10,
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "UPSTREAM_TIMEOUT"
    assert payload["error"]["retryable"] is True
