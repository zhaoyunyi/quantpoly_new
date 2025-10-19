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
    service = StrategyService(repository=repo, count_active_backtests=lambda user_id, strategy_id: 0)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_create_and_list_scoped(capsys):
    created_1 = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="trend-alpha",
        template="mean_reversion",
        parameters='{"window": 20, "entryZ": 1.5, "exitZ": 0.5}',
    )
    created_2 = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="trend-beta",
        template="mean_reversion",
        parameters='{"window": 21, "entryZ": 1.6, "exitZ": 0.6}',
    )
    _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="mean-gamma",
        template="mean_reversion",
        parameters='{"window": 22, "entryZ": 1.7, "exitZ": 0.7}',
    )
    _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-2",
        name="trend-foreign",
        template="mean_reversion",
        parameters='{"window": 23, "entryZ": 1.8, "exitZ": 0.8}',
    )

    _run(
        cli._cmd_activate,
        capsys=capsys,
        user_id="u-1",
        strategy_id=created_1["data"]["id"],
    )
    _run(
        cli._cmd_activate,
        capsys=capsys,
        user_id="u-1",
        strategy_id=created_2["data"]["id"],
    )

    my_list = _run(
        cli._cmd_list,
        capsys=capsys,
        user_id="u-1",
        status="active",
        search="trend",
        page=1,
        page_size=1,
    )
    page_2 = _run(
        cli._cmd_list,
        capsys=capsys,
        user_id="u-1",
        status="active",
        search="trend",
        page=2,
        page_size=1,
    )
    other_list = _run(
        cli._cmd_list,
        capsys=capsys,
        user_id="u-2",
        status=None,
        search=None,
        page=1,
        page_size=20,
    )

    assert my_list["success"] is True
    assert my_list["data"]["total"] == 2
    assert my_list["data"]["page"] == 1
    assert my_list["data"]["pageSize"] == 1
    assert len(my_list["data"]["items"]) == 1
    assert my_list["data"]["items"][0]["status"] == "active"
    assert "trend" in my_list["data"]["items"][0]["name"]

    assert page_2["success"] is True
    assert page_2["data"]["total"] == 2
    assert page_2["data"]["page"] == 2
    assert len(page_2["data"]["items"]) == 1
    assert page_2["data"]["items"][0]["id"] != my_list["data"]["items"][0]["id"]

    assert other_list["success"] is True
    assert other_list["data"]["total"] == 1


def test_cli_delete_returns_strategy_in_use_code(capsys, monkeypatch):
    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda user_id, strategy_id: 1)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    created = _run(
        cli._cmd_create,
        capsys=capsys,
        user_id="u-1",
        name="mean-reversion-1",
        template="mean_reversion",
        parameters='{"window": 20, "entryZ": 1.5, "exitZ": 0.5}',
    )

    deleted = _run(
        cli._cmd_delete,
        capsys=capsys,
        user_id="u-1",
        strategy_id=created["data"]["id"],
    )

    assert deleted["success"] is False
    assert deleted["error"]["code"] == "STRATEGY_IN_USE"
