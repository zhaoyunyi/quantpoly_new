"""strategy_management CLI 组合管理测试。"""

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


def _create_strategy(*, capsys, user_id: str, name: str) -> str:
    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id=user_id,
        name=name,
        template="mean_reversion",
        parameters='{"window": 20, "entryZ": 1.5, "exitZ": 0.5}',
    )
    assert created["success"] is True
    return created["data"]["id"]


def test_cli_should_create_portfolio_add_members_and_list(capsys):
    s1 = _create_strategy(capsys=capsys, user_id="u-1", name="s1")
    s2 = _create_strategy(capsys=capsys, user_id="u-1", name="s2")

    created = _run(
        cli._cmd_portfolio_create,
        capsys=capsys,
        user_id="u-1",
        name="core",
        constraints_json='{"maxTotalWeight":1.0,"maxSingleWeight":0.8}',
    )
    assert created["success"] is True
    portfolio_id = created["data"]["id"]

    add1 = _run(
        cli._cmd_portfolio_add_member,
        capsys=capsys,
        user_id="u-1",
        portfolio_id=portfolio_id,
        strategy_id=s1,
        weight=0.6,
    )
    assert add1["success"] is True

    add2 = _run(
        cli._cmd_portfolio_add_member,
        capsys=capsys,
        user_id="u-1",
        portfolio_id=portfolio_id,
        strategy_id=s2,
        weight=0.4,
    )
    assert add2["success"] is True

    listed = _run(cli._cmd_portfolio_list, capsys=capsys, user_id="u-1")
    assert listed["success"] is True
    assert listed["data"][0]["id"] == portfolio_id
    assert len(listed["data"][0]["members"]) == 2


def test_cli_should_reject_invalid_portfolio_weight_constraints(capsys):
    s1 = _create_strategy(capsys=capsys, user_id="u-1", name="s1")

    created = _run(
        cli._cmd_portfolio_create,
        capsys=capsys,
        user_id="u-1",
        name="risk",
        constraints_json='{"maxTotalWeight":1.0,"maxSingleWeight":0.5}',
    )
    portfolio_id = created["data"]["id"]

    rejected = _run(
        cli._cmd_portfolio_add_member,
        capsys=capsys,
        user_id="u-1",
        portfolio_id=portfolio_id,
        strategy_id=s1,
        weight=0.8,
    )

    assert rejected["success"] is False
    assert rejected["error"]["code"] == "PORTFOLIO_INVALID_WEIGHTS"


def test_cli_should_submit_portfolio_rebalance_task(capsys):
    s1 = _create_strategy(capsys=capsys, user_id="u-1", name="s1")

    created = _run(
        cli._cmd_portfolio_create,
        capsys=capsys,
        user_id="u-1",
        name="rb",
        constraints_json='{"maxTotalWeight":1.0,"maxSingleWeight":1.0}',
    )
    portfolio_id = created["data"]["id"]

    assert _run(
        cli._cmd_portfolio_add_member,
        capsys=capsys,
        user_id="u-1",
        portfolio_id=portfolio_id,
        strategy_id=s1,
        weight=1.0,
    )["success"] is True

    submitted = _run(
        cli._cmd_portfolio_rebalance_task,
        capsys=capsys,
        user_id="u-1",
        portfolio_id=portfolio_id,
        idempotency_key="rb-1",
        target_weights_json='{}',
    )

    assert submitted["success"] is True
    assert submitted["data"]["taskType"] == "portfolio_rebalance"
    assert submitted["data"]["result"]["riskSummary"]


def test_cli_should_query_portfolio_read_model(capsys):
    s1 = _create_strategy(capsys=capsys, user_id="u-1", name="s1")

    created = _run(
        cli._cmd_portfolio_create,
        capsys=capsys,
        user_id="u-1",
        name="read",
        constraints_json='{"maxTotalWeight":1.0,"maxSingleWeight":1.0}',
    )
    portfolio_id = created["data"]["id"]

    assert _run(
        cli._cmd_portfolio_add_member,
        capsys=capsys,
        user_id="u-1",
        portfolio_id=portfolio_id,
        strategy_id=s1,
        weight=1.0,
    )["success"] is True

    read_model = _run(
        cli._cmd_portfolio_read_model,
        capsys=capsys,
        user_id="u-1",
        portfolio_id=portfolio_id,
    )

    assert read_model["success"] is True
    assert read_model["data"]["portfolioId"] == portfolio_id
    assert "performanceSummary" in read_model["data"]
