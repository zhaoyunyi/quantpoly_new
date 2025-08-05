"""回测扩展 CLI 测试。"""

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


def test_cli_list_stats_compare_and_retry(capsys, monkeypatch):
    _setup(monkeypatch)

    t1 = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        strategy_id="s-1",
        config="{}",
        idempotency_key="k-1",
    )["data"]
    t2 = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        strategy_id="s-2",
        config="{}",
        idempotency_key="k-2",
    )["data"]

    _run(cli._cmd_transition, capsys=capsys, user_id="u-1", task_id=t1["id"], to_status="running", metrics="{}")
    _run(
        cli._cmd_transition,
        capsys=capsys,
        user_id="u-1",
        task_id=t1["id"],
        to_status="completed",
        metrics='{"returnRate": 0.1, "maxDrawdown": 0.05, "winRate": 0.6}',
    )

    listed = _run(cli._cmd_list, capsys=capsys, user_id="u-1", status="pending", page=1, page_size=10)
    assert listed["success"] is True

    stats = _run(cli._cmd_statistics, capsys=capsys, user_id="u-1")
    assert stats["success"] is True
    assert stats["data"]["completedCount"] == 1

    compared = _run(cli._cmd_compare, capsys=capsys, user_id="u-1", task_ids=f"{t1['id']},{t2['id']}")
    assert compared["success"] is True
    assert len(compared["data"]["tasks"]) == 2

    _run(cli._cmd_transition, capsys=capsys, user_id="u-1", task_id=t2["id"], to_status="running", metrics="{}")
    cancelled = _run(cli._cmd_cancel, capsys=capsys, user_id="u-1", task_id=t2["id"])
    assert cancelled["data"]["status"] == "cancelled"

    retried = _run(cli._cmd_retry, capsys=capsys, user_id="u-1", task_id=t2["id"])
    assert retried["data"]["status"] == "pending"
