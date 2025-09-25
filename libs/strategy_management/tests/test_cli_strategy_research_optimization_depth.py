"""strategy_management CLI 策略研究优化深度测试。"""

from __future__ import annotations

import argparse
import json

import pytest

from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import JobOrchestrationService
from strategy_management import cli
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import StrategyService


@pytest.fixture(autouse=True)
def _reset_cli_state(monkeypatch):
    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda _strategy_id: 0)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)
    monkeypatch.setattr(cli, "_job_service", JobOrchestrationService(repository=InMemoryJobRepository(), scheduler=InMemoryScheduler()))


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_research_optimization_rejects_invalid_parameter_space(capsys):
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
        idempotency_key="idem-invalid",
        objective_json='{"metric":"averagePnl","direction":"maximize"}',
        parameter_space_json='{"window":{"min":40,"max":10,"step":5}}',
        constraints_json='{}',
    )

    assert task["success"] is False
    assert task["error"]["code"] == "RESEARCH_INVALID_PARAMETER_SPACE"


def test_cli_research_results_lists_completed_runs(capsys):
    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="mr",
        template="mean_reversion",
        parameters='{"window": 20, "entryZ": 1.5, "exitZ": 0.5}',
    )
    strategy_id = created["data"]["id"]

    submitted = _run(
        cli._cmd_research_optimization_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        idempotency_key="idem-ok",
        objective_json='{"metric":"averagePnl","direction":"maximize"}',
        parameter_space_json='{"window":{"min":10,"max":40,"step":5}}',
        constraints_json='{}',
    )
    assert submitted["success"] is True

    listed = _run(
        cli._cmd_research_results,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        status="succeeded",
        limit=20,
    )

    assert listed["success"] is True
    assert listed["data"]["total"] >= 1
    assert listed["data"]["items"][0]["taskId"] == submitted["data"]["taskId"]
