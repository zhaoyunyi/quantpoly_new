"""market_data CLI 指标套件能力对齐测试。"""

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
        del symbol, start_date, end_date, timeframe, limit
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


def _as_indicator_map(payload: dict) -> dict[str, dict]:
    return {item["name"]: item for item in payload["data"]["indicators"]}


def test_cli_indicators_calculate_outputs_unified_json_contract(capsys, monkeypatch):
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
        indicators='[{"name":"ema","period":3},{"name":"rsi","period":3},{"name":"macd","fast":3,"slow":5,"signal":2},{"name":"bollinger","period":3,"stdDev":2}]',
    )

    assert payload["success"] is True
    indicators = _as_indicator_map(payload)

    for name in ["ema", "rsi", "macd", "bollinger"]:
        assert indicators[name]["status"] == "ok"
        assert "value" in indicators[name]
        assert "metadata" in indicators[name]


def test_cli_indicators_calculate_outputs_unsupported_and_insufficient(capsys, monkeypatch):
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
        indicators='[{"name":"foo","period":3},{"name":"rsi","period":14}]',
    )

    assert payload["success"] is True
    indicators = _as_indicator_map(payload)

    assert indicators["foo"]["status"] == "unsupported"
    assert "value" not in indicators["foo"]

    assert indicators["rsi"]["status"] == "insufficient_data"
    assert "value" not in indicators["rsi"]
    assert indicators["rsi"]["metadata"]["requiredDataPoints"] == 15
