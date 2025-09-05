"""signal_execution 策略驱动生成 CLI 合同测试。"""

from __future__ import annotations

import argparse
import json

from signal_execution import cli
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _build_service(*, strategies: dict[str, dict], histories: dict[str, list[float]]) -> SignalExecutionService:
    def _strategy_reader(*, user_id: str, strategy_id: str):
        strategy = strategies.get(strategy_id)
        if strategy is None:
            return None
        if strategy.get("userId") != user_id:
            return None
        return strategy

    def _market_history_reader(*, user_id: str, symbol: str, timeframe: str, limit: int | None = None):
        del user_id, timeframe, limit
        closes = histories.get(symbol.upper(), [])
        return [{"close": item} for item in closes]

    return SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
        strategy_reader=_strategy_reader,
        market_history_reader=_market_history_reader,
    )


def test_cli_generate_by_strategy_outputs_structured_json(capsys, monkeypatch):
    service = _build_service(
        strategies={
            "u-1-ma": {
                "id": "u-1-ma",
                "userId": "u-1",
                "status": "active",
                "template": "moving_average",
                "parameters": {"shortWindow": 2, "longWindow": 3},
            }
        },
        histories={"AAPL": [10.0, 11.0, 12.0, 13.0]},
    )
    monkeypatch.setattr(cli, "_service", service)

    payload = _run(
        cli._cmd_generate_by_strategy,
        capsys=capsys,
        user_id="u-1",
        strategy_id="u-1-ma",
        account_id="u-1-account-1",
        symbols="AAPL",
        timeframe="1Day",
    )

    assert payload["success"] is True
    assert len(payload["data"]["signals"]) == 1
    signal = payload["data"]["signals"][0]
    assert signal["symbol"] == "AAPL"
    assert signal["side"] == "BUY"
    assert signal["metadata"]["triggered_indicator"] == "moving_average"


def test_cli_generate_by_strategy_reports_skip_reason(capsys, monkeypatch):
    service = _build_service(
        strategies={
            "u-1-ma": {
                "id": "u-1-ma",
                "userId": "u-1",
                "status": "active",
                "template": "moving_average",
                "parameters": {"shortWindow": 3, "longWindow": 5},
            }
        },
        histories={"MSFT": [10.0, 11.0, 12.0]},
    )
    monkeypatch.setattr(cli, "_service", service)

    payload = _run(
        cli._cmd_generate_by_strategy,
        capsys=capsys,
        user_id="u-1",
        strategy_id="u-1-ma",
        account_id="u-1-account-1",
        symbols="MSFT",
        timeframe="1Day",
    )

    assert payload["success"] is True
    assert payload["data"]["signals"] == []
    assert payload["data"]["skipped"][0]["reason"] == "insufficient_data"
