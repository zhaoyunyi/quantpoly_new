"""backtest_runner CLI 测试。"""

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


def test_cli_create_and_status(capsys, monkeypatch):
    repo = InMemoryBacktestRepository()
    service = BacktestService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        strategy_id="s-1",
        config='{"symbol": "AAPL"}',
    )
    assert created["success"] is True
    assert created["data"]["status"] == "pending"

    fetched = _run(
        cli._cmd_status,
        capsys=capsys,
        user_id="u-1",
        task_id=created["data"]["id"],
    )
    assert fetched["success"] is True
    assert fetched["data"]["status"] == "pending"


def test_cli_transition_invalid_returns_error_code(capsys, monkeypatch):
    repo = InMemoryBacktestRepository()
    service = BacktestService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        strategy_id="s-1",
        config='{}',
    )

    transitioned = _run(
        cli._cmd_transition,
        capsys=capsys,
        user_id="u-1",
        task_id=created["data"]["id"],
        to_status="completed",
    )

    assert transitioned["success"] is False
    assert transitioned["error"]["code"] == "INVALID_TRANSITION"
