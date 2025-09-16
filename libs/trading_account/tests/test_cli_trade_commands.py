"""交易命令（buy/sell）CLI 测试。"""

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


def test_cli_buy_success(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")
    service.deposit(user_id="u-1", account_id=account.id, amount=2000)

    result = _run(
        cli._cmd_buy,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        price=100,
    )

    assert result["success"] is True
    assert result["data"]["order"]["status"] == "filled"


def test_cli_sell_insufficient_position(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")

    result = _run(
        cli._cmd_sell,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        symbol="TSLA",
        quantity=1,
        price=200,
    )

    assert result["success"] is False
    assert result["error"]["code"] == "INSUFFICIENT_POSITION"
