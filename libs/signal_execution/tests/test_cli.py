"""signal_execution CLI 测试。"""

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


def test_cli_trend_outputs_scoped_result(capsys, monkeypatch):
    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=s1.id)

    service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy",
        account_id="u-2-account",
        symbol="MSFT",
        side="BUY",
    )

    payload = _run(cli._cmd_trend, capsys=capsys, user_id="u-1")

    assert payload["success"] is True
    assert payload["data"]["total"] == 1


def test_cli_cleanup_all_requires_admin(capsys, monkeypatch):
    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)

    service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )

    payload = _run(cli._cmd_cleanup_all, capsys=capsys, user_id="u-1", is_admin=False)

    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"

