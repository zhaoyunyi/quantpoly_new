"""backtest_runner 回测管理读模型 CLI 合同测试。"""

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


def _setup(monkeypatch):
    repo = InMemoryBacktestRepository()
    service = BacktestService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)
    return service


def test_cli_rename_and_related_commands(capsys, monkeypatch):
    service = _setup(monkeypatch)

    anchor = service.create_task(user_id="u-1", strategy_id="s-1", config={"symbol": "AAPL"})
    related = service.create_task(user_id="u-1", strategy_id="s-1", config={"symbol": "AAPL"})
    service.transition(user_id="u-1", task_id=related.id, to_status="running")
    service.transition(user_id="u-1", task_id=related.id, to_status="completed", metrics={"returnRate": 0.1})

    renamed = _run(
        cli._cmd_rename,
        capsys=capsys,
        user_id="u-1",
        task_id=anchor.id,
        display_name="策略A-回测基线",
    )
    assert renamed["success"] is True
    assert renamed["data"]["displayName"] == "策略A-回测基线"

    related_resp = _run(
        cli._cmd_related,
        capsys=capsys,
        user_id="u-1",
        task_id=anchor.id,
        status="completed",
        limit=20,
    )
    assert related_resp["success"] is True
    assert len(related_resp["data"]) == 1
    assert related_resp["data"][0]["id"] == related.id


