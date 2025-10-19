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
    service = StrategyService(repository=repo, count_active_backtests=lambda user_id, strategy_id: 0)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)
    monkeypatch.setattr(cli, "_job_service", JobOrchestrationService(repository=InMemoryJobRepository(), scheduler=InMemoryScheduler()))


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def _create_mean_reversion_strategy(*, capsys):
    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="mr",
        template="mean_reversion",
        parameters='{"window": 20, "entryZ": 1.5, "exitZ": 0.5}',
    )
    assert created["success"] is True
    return created["data"]["id"]


def test_cli_research_optimization_rejects_invalid_parameter_space(capsys):
    strategy_id = _create_mean_reversion_strategy(capsys=capsys)

    task = _run(
        cli._cmd_research_optimization_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        idempotency_key="idem-invalid",
        method="grid",
        objective_json='{"metric":"averagePnl","direction":"maximize"}',
        parameter_space_json='{"window":{"min":40,"max":10,"step":5}}',
        constraints_json='{}',
        budget_json='{"maxTrials":3}',
    )

    assert task["success"] is False
    assert task["error"]["code"] == "RESEARCH_INVALID_PARAMETER_SPACE"


def test_cli_research_optimization_supports_method_budget_and_summary(capsys):
    strategy_id = _create_mean_reversion_strategy(capsys=capsys)

    submitted = _run(
        cli._cmd_research_optimization_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        idempotency_key="idem-bayes",
        method="bayesian",
        objective_json='{"metric":"averagePnl","direction":"maximize"}',
        parameter_space_json='{"window":{"min":10,"max":40,"step":5}}',
        constraints_json='{"maxDrawdown":0.2}',
        budget_json='{"maxTrials":4,"maxDurationSeconds":30}',
    )
    assert submitted["success"] is True

    result = submitted["data"]["result"]["optimizationResult"]
    assert result["method"] == "bayesian"
    assert 1 <= len(result["trials"]) <= 4
    assert result["budget"]["maxTrials"] == 4
    assert result["budgetUsage"]["usedTrials"] == len(result["trials"])
    assert result["convergence"]["earlyStopReason"]


def test_cli_research_results_lists_completed_runs(capsys):
    strategy_id = _create_mean_reversion_strategy(capsys=capsys)

    submitted = _run(
        cli._cmd_research_optimization_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        idempotency_key="idem-ok",
        method="grid",
        objective_json='{"metric":"averagePnl","direction":"maximize"}',
        parameter_space_json='{"window":{"min":10,"max":40,"step":5}}',
        constraints_json='{}',
        budget_json='{"maxTrials":2}',
    )
    assert submitted["success"] is True

    listed = _run(
        cli._cmd_research_results,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        status="succeeded",
        method=None,
        version=None,
        limit=20,
    )

    assert listed["success"] is True
    assert listed["data"]["total"] >= 1
    assert listed["data"]["items"][0]["taskId"] == submitted["data"]["taskId"]


def test_cli_research_results_supports_method_and_version_filters(capsys):
    strategy_id = _create_mean_reversion_strategy(capsys=capsys)

    grid_result = _run(
        cli._cmd_research_optimization_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        idempotency_key="idem-grid",
        method="grid",
        objective_json='{"metric":"averagePnl","direction":"maximize"}',
        parameter_space_json='{"window":{"min":10,"max":25,"step":5}}',
        constraints_json='{}',
        budget_json='{"maxTrials":2}',
    )
    assert grid_result["success"] is True

    bayes_result = _run(
        cli._cmd_research_optimization_task,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        idempotency_key="idem-bayes-filter",
        method="bayesian",
        objective_json='{"metric":"averagePnl","direction":"maximize"}',
        parameter_space_json='{"window":{"min":10,"max":25,"step":5}}',
        constraints_json='{}',
        budget_json='{"maxTrials":3}',
    )
    assert bayes_result["success"] is True

    listed = _run(
        cli._cmd_research_results,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy_id,
        status="succeeded",
        method="bayesian",
        version="v3",
        limit=20,
    )

    assert listed["success"] is True
    assert listed["data"]["total"] == 1
    item = listed["data"]["items"][0]
    assert item["method"] == "bayesian"
    assert item["optimizationResult"]["version"] == "v3"
