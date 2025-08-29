"""market_data CLI：数据管道任务补齐测试（WaveX）。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from market_data import cli
from market_data.domain import MarketCandle
from market_data.service import MarketDataService


class _Provider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        del symbol
        raise RuntimeError("not used")

    def history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ):
        del start_date, end_date, timeframe, limit
        close_prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        base = datetime(2026, 2, 1, tzinfo=timezone.utc)
        return [
            MarketCandle(
                timestamp=base + timedelta(days=i),
                open_price=price,
                high_price=price,
                low_price=price,
                close_price=price,
                volume=1000.0,
            )
            for i, price in enumerate(close_prices)
        ]

    def list_assets(self, *, limit: int):
        del limit
        return []

    def batch_quote(self, *, symbols: list[str]):
        del symbols
        return {}

    def health(self):
        return {"provider": "fake", "healthy": True, "status": "ok", "message": ""}


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_indicators_calculate_outputs_contract(capsys, monkeypatch):
    service = MarketDataService(provider=_Provider())
    monkeypatch.setattr(cli, "_service", service)

    payload = _run(
        cli._cmd_indicators_calculate,
        capsys=capsys,
        user_id="u-1",
        symbol="AAPL",
        start_date="2026-02-01",
        end_date="2026-02-05",
        timeframe="1Day",
        indicators='[{"name":"sma","period":3}]',
    )

    assert payload["success"] is True
    assert payload["data"]["symbol"] == "AAPL"
    assert payload["data"]["indicators"][0]["name"] == "sma"
    assert payload["data"]["indicators"][0]["period"] == 3
    assert payload["data"]["indicators"][0]["value"] == 13.0


def test_cli_sync_then_boundary_check_reports_missing(capsys, monkeypatch):
    service = MarketDataService(provider=_Provider())
    monkeypatch.setattr(cli, "_service", service)

    synced = _run(
        cli._cmd_sync,
        capsys=capsys,
        user_id="u-1",
        symbols="AAPL",
        start_date="2026-02-01",
        end_date="2026-02-05",
        timeframe="1Day",
    )
    assert synced["success"] is True
    assert synced["data"]["summary"]["successCount"] == 1

    report = _run(
        cli._cmd_boundary_check,
        capsys=capsys,
        user_id="u-1",
        symbols="AAPL,MSFT",
    )
    assert report["success"] is True
    assert report["data"]["consistent"] is False
    assert report["data"]["missingIds"] == ["MSFT"]

