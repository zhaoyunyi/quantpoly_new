"""交易分析与运维能力 CLI 测试。"""

from __future__ import annotations

import argparse
import json

from trading_account import cli
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import TradingAccountService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _setup(monkeypatch) -> TradingAccountService:
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)
    return service


def test_cli_risk_metrics_and_account_aggregate(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")
    service.deposit(user_id="u-1", account_id=account.id, amount=1000)

    risk = _run(cli._cmd_risk_metrics, capsys=capsys, user_id="u-1", account_id=account.id)
    assert risk["success"] is True
    assert risk["data"]["accountId"] == account.id

    aggregate = _run(cli._cmd_account_aggregate, capsys=capsys, user_id="u-1")
    assert aggregate["success"] is True
    assert aggregate["data"]["accountCount"] == 1


def test_cli_pending_orders_requires_admin(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="primary")
    service.submit_order(
        user_id="u-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )

    denied = _run(
        cli._cmd_pending_orders,
        capsys=capsys,
        user_id="u-1",
        is_admin=False,
        account_id=None,
    )

    assert denied["success"] is False
    assert denied["error"]["code"] == "ADMIN_REQUIRED"


def test_cli_refresh_prices_supports_idempotency_conflict(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.upsert_position(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )

    first = _run(
        cli._cmd_refresh_prices,
        capsys=capsys,
        user_id="admin-1",
        is_admin=True,
        price_updates='{"AAPL": 130}',
        idempotency_key="refresh-1",
        confirmation_token=None,
    )
    assert first["success"] is True
    assert first["data"]["idempotent"] is False

    conflict = _run(
        cli._cmd_refresh_prices,
        capsys=capsys,
        user_id="admin-1",
        is_admin=True,
        price_updates='{"AAPL": 131}',
        idempotency_key="refresh-1",
        confirmation_token=None,
    )

    assert conflict["success"] is False
    assert conflict["error"]["code"] == "IDEMPOTENCY_CONFLICT"
