"""trading_account CLI 测试。"""

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


def test_cli_account_list_scoped(capsys, monkeypatch):
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    service.create_account(user_id="u-1", account_name="primary")
    service.create_account(user_id="u-2", account_name="other")

    mine = _run(cli._cmd_account_list, capsys=capsys, user_id="u-1")
    other = _run(cli._cmd_account_list, capsys=capsys, user_id="u-2")

    assert mine["success"] is True
    assert len(mine["data"]) == 1
    assert mine["data"][0]["userId"] == "u-1"

    assert other["success"] is True
    assert len(other["data"]) == 1
    assert other["data"][0]["userId"] == "u-2"


def test_cli_position_summary(capsys, monkeypatch):
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    account = service.create_account(user_id="u-1", account_name="primary")
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )

    summary = _run(
        cli._cmd_position_summary,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )

    assert summary["success"] is True
    assert summary["data"]["positionCount"] == 1
    assert summary["data"]["totalMarketValue"] == 1100


def test_cli_trade_stats(capsys, monkeypatch):
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    account = service.create_account(user_id="u-1", account_name="primary")
    service.record_trade(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=100,
    )

    stats = _run(
        cli._cmd_trade_stats,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )

    assert stats["success"] is True
    assert stats["data"]["tradeCount"] == 1
    assert stats["data"]["turnover"] == 1000


def test_cli_returns_access_denied_code(capsys, monkeypatch):
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)

    account = service.create_account(user_id="u-2", account_name="other")

    denied = _run(
        cli._cmd_position_summary,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )

    assert denied["success"] is False
    assert denied["error"]["code"] == "ACCOUNT_ACCESS_DENIED"

