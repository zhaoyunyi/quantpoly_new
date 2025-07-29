"""strategy_management CLI 测试。"""

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


def test_cli_create_and_list_scoped(capsys):
    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="mean-reversion-1",
        template="mean_reversion",
        parameters='{"window": 20}',
    )
    assert created["success"] is True
    strategy_id = created["data"]["id"]

    my_list = _run(cli._cmd_list, capsys=capsys, user_id="u-1")
    other_list = _run(cli._cmd_list, capsys=capsys, user_id="u-2")

    assert len(my_list["data"]) == 1
    assert my_list["data"][0]["id"] == strategy_id
    assert other_list["data"] == []


def test_cli_delete_returns_strategy_in_use_code(capsys, monkeypatch):
    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda _strategy_id: 1)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="mean-reversion-1",
        template="mean_reversion",
        parameters='{"window": 20}',
    )

    deleted = _run(
        cli._cmd_delete,
        capsys=capsys,
        user_id="u-1",
        strategy_id=created["data"]["id"],
    )

    assert deleted["success"] is False
    assert deleted["error"]["code"] == "STRATEGY_IN_USE"
