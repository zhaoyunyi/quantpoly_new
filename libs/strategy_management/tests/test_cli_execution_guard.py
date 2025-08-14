"""strategy_management 执行前校验 CLI 测试。"""

from __future__ import annotations

import argparse
import json

from strategy_management import cli
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import StrategyService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_validate_execution_returns_validation_error(capsys, monkeypatch):
    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda _strategy_id: 0)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    payload = _run(
        cli._cmd_validate_execution,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy.id,
        parameters='{"window": 20, "entryZ": 1.5}',
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_INVALID_PARAMETERS"


def test_cli_validate_execution_returns_success_for_valid_input(capsys, monkeypatch):
    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda _strategy_id: 0)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    payload = _run(
        cli._cmd_validate_execution,
        capsys=capsys,
        user_id="u-1",
        strategy_id=strategy.id,
        parameters='{"window": 25, "entryZ": 1.8, "exitZ": 0.6}',
    )

    assert payload["success"] is True
    assert payload["data"]["valid"] is True
    assert payload["data"]["strategyId"] == strategy.id
