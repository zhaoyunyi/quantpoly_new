"""backtest_runner 回测引擎 CLI 合同测试。"""

from __future__ import annotations

import argparse
import json

from backtest_runner import cli
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.service import BacktestService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def _setup_service(monkeypatch, *, prices: list[float], template: str = "moving_average") -> None:
    def _strategy_reader(*, user_id: str, strategy_id: str):
        return {
            "id": strategy_id,
            "userId": user_id,
            "status": "active",
            "template": template,
            "parameters": {"shortWindow": 3, "longWindow": 5},
        }

    def _market_history_reader(
        *,
        user_id: str,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
        timeframe: str,
        limit: int | None,
    ):
        del user_id, symbol, start_date, end_date, timeframe, limit
        return [{"close": value} for value in prices]

    repo = InMemoryBacktestRepository()
    service = BacktestService(
        repository=repo,
        strategy_reader=_strategy_reader,
        market_history_reader=_market_history_reader,
    )
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)


def test_cli_run_task_and_result_commands_return_structured_json(capsys, monkeypatch):
    _setup_service(
        monkeypatch,
        prices=[10, 10, 10, 10, 10, 11, 12, 13, 12, 11, 10, 9, 8, 9, 10, 11, 12],
    )

    run_payload = _run(
        cli._cmd_run_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id="s-1",
        idempotency_key="cli-backtest-engine-happy-path",
        config='{"symbol": "AAPL", "startDate": "2024-01-01", "endDate": "2024-12-31"}',
    )

    assert run_payload["success"] is True
    task_payload = run_payload["data"]["task"]
    assert task_payload["status"] == "completed"
    assert "returnRate" in task_payload["metrics"]

    task_id = task_payload["id"]
    result_payload = _run(cli._cmd_result, capsys=capsys, user_id="u-1", task_id=task_id)

    assert result_payload["success"] is True
    assert result_payload["data"]["taskId"] == task_id
    assert isinstance(result_payload["data"]["equityCurve"], list)
    assert isinstance(result_payload["data"]["trades"], list)


def test_cli_run_task_returns_failure_when_engine_rejects_template(capsys, monkeypatch):
    _setup_service(monkeypatch, prices=[10, 11, 12, 13, 14, 15, 16], template="unsupported_template")

    run_payload = _run(
        cli._cmd_run_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id="s-1",
        idempotency_key="cli-backtest-engine-template-invalid",
        config='{"symbol": "AAPL"}',
    )

    assert run_payload["success"] is False
    assert run_payload["error"]["code"] == "BACKTEST_UNSUPPORTED_TEMPLATE"
    assert run_payload["data"]["status"] == "failed"
