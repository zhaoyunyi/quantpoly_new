"""订单与账本 CLI 测试。"""

from __future__ import annotations

import argparse
import json

from trading_account import cli
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import TradingAccountService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def _setup(monkeypatch):
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)
    return service


def test_cli_order_create_list_and_fill(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")

    created = _run(
        cli._cmd_order_create,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )
    order_id = created["data"]["id"]

    listed = _run(
        cli._cmd_order_list,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )
    assert listed["success"] is True
    assert len(listed["data"]) == 1

    filled = _run(
        cli._cmd_order_fill,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        order_id=order_id,
    )
    assert filled["success"] is True
    assert filled["data"]["status"] == "filled"


def test_cli_withdraw_insufficient_funds_returns_stable_error(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")

    denied = _run(
        cli._cmd_withdraw,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        amount=1,
    )

    assert denied["success"] is False
    assert denied["error"]["code"] == "INSUFFICIENT_FUNDS"


def test_cli_account_overview(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")

    service.deposit(user_id="u-1", account_id=account.id, amount=1000)

    overview = _run(
        cli._cmd_account_overview,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )

    assert overview["success"] is True
    assert overview["data"]["cashBalance"] == 1000
