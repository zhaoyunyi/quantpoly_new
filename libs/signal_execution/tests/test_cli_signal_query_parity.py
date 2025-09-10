"""signal_execution 手动过期与账户统计 CLI 对齐测试。"""

from __future__ import annotations

import argparse
import json

from signal_execution import cli
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def _setup(monkeypatch):
    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)
    return service


def test_cli_should_support_expire_and_account_statistics(capsys, monkeypatch):
    service = _setup(monkeypatch)

    pending = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    executed = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=executed.id)

    expired = _run(
        cli._cmd_expire,
        capsys=capsys,
        user_id="u-1",
        signal_id=pending.id,
    )
    assert expired["success"] is True
    assert expired["data"]["status"] == "expired"

    stats = _run(
        cli._cmd_account_statistics,
        capsys=capsys,
        user_id="u-1",
        account_id="u-1-account",
    )
    assert stats["success"] is True
    assert stats["data"]["accountId"] == "u-1-account"
    assert stats["data"]["expired"] == 1


def test_cli_account_statistics_should_enforce_acl(capsys, monkeypatch):
    _setup(monkeypatch)

    denied = _run(
        cli._cmd_account_statistics,
        capsys=capsys,
        user_id="u-1",
        account_id="u-2-account",
    )
    assert denied["success"] is False
    assert denied["error"]["code"] == "SIGNAL_ACCESS_DENIED"
