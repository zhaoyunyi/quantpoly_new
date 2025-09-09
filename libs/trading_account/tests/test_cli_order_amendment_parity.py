"""订单改撤与快捷查询 CLI 合同测试。"""

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


def test_cli_should_support_order_update_delete_and_pending_query(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")
    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )

    updated = _run(
        cli._cmd_order_update,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        order_id=order.id,
        quantity=2,
        price=120,
    )
    assert updated["success"] is True
    assert updated["data"]["quantity"] == 2

    pending = _run(
        cli._cmd_trade_pending,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )
    assert pending["success"] is True
    assert [item["id"] for item in pending["data"]] == [order.id]

    deleted = _run(
        cli._cmd_order_delete,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        order_id=order.id,
    )
    assert deleted["success"] is True
    assert deleted["data"]["status"] == "cancelled"


def test_cli_should_support_position_by_symbol_and_state_guard(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")
    service.upsert_position(
        user_id="u-1",
        account_id=account.id,
        symbol="TSLA",
        quantity=3,
        avg_price=200,
        last_price=210,
    )
    order = service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="TSLA",
        side="BUY",
        quantity=1,
        price=210,
    )
    service.fill_order(user_id="u-1", account_id=account.id, order_id=order.id)

    position = _run(
        cli._cmd_position_get,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        symbol="TSLA",
    )
    assert position["success"] is True
    assert position["data"]["symbol"] == "TSLA"

    denied = _run(
        cli._cmd_order_update,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
        order_id=order.id,
        quantity=2,
        price=None,
    )
    assert denied["success"] is False
    assert denied["error"]["code"] == "ORDER_INVALID_TRANSITION"
