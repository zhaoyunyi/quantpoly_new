"""strategy_management CLI 策略研究自动化任务化能力测试（Wave3）。"""

from __future__ import annotations

import argparse
import json

import pytest

from strategy_management import cli
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import StrategyService


@pytest.fixture(autouse=True)
def _reset_cli_state(monkeypatch):
    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda _strategy_id: 0)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_research_performance_task_returns_task_id(capsys):
    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="mr",
        template="mean_reversion",
        parameters='{"window": 20, "entryZ": 1.5, "exitZ": 0.5}',
    )
    strategy_id = created["data"]["id"]

    task = _run(
        cli._cmd_research_performance_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        analysis_period_days=30,
        idempotency_key="idem-1",
    )

    assert task["success"] is True
    assert task["data"]["taskId"]
    assert task["data"]["taskType"] == "strategy_performance_analyze"


def test_cli_research_optimization_task_returns_task_id(capsys):
    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="mr",
        template="mean_reversion",
        parameters='{"window": 20, "entryZ": 1.5, "exitZ": 0.5}',
    )
    strategy_id = created["data"]["id"]

    task = _run(
        cli._cmd_research_optimization_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        idempotency_key="idem-2",
    )

    assert task["success"] is True
    assert task["data"]["taskId"]
    assert task["data"]["taskType"] == "strategy_optimization_suggest"

