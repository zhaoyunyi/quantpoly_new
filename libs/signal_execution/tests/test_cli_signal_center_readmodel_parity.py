"""signal_execution 信号中心读模型 CLI 测试。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from signal_execution import cli
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _build_service() -> SignalExecutionService:
    return SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )


def test_cli_signal_get_and_pending_expired(capsys, monkeypatch):
    service = _build_service()
    monkeypatch.setattr(cli, "_service", service)

    pending = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-mean-revert",
        account_id="u-1-account-a",
        symbol="AAPL",
        side="BUY",
    )
    expired = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-mean-revert",
        account_id="u-1-account-a",
        symbol="TSLA",
        side="SELL",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    service.update_expired_signals(user_id="u-1")

    detail_payload = _run(
        cli._cmd_signal_get,
        capsys=capsys,
        user_id="u-1",
        signal_id=pending.id,
    )
    assert detail_payload["success"] is True
    assert detail_payload["data"]["id"] == pending.id

    pending_payload = _run(cli._cmd_pending, capsys=capsys, user_id="u-1")
    assert pending_payload["success"] is True
    assert [item["id"] for item in pending_payload["data"]] == [pending.id]

    expired_payload = _run(cli._cmd_expired, capsys=capsys, user_id="u-1")
    assert expired_payload["success"] is True
    assert [item["id"] for item in expired_payload["data"]] == [expired.id]


def test_cli_search_and_dashboard_are_scoped(capsys, monkeypatch):
    service = _build_service()
    monkeypatch.setattr(cli, "_service", service)

    account_a = "u-1-account-a"
    account_b = "u-1-account-b"

    pending_a = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-mean-revert",
        account_id=account_a,
        symbol="AAPL",
        side="BUY",
    )
    expired_a = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-mean-revert",
        account_id=account_a,
        symbol="TSLA",
        side="SELL",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    executed_b = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-breakout",
        account_id=account_b,
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=executed_b.id)
    service.update_expired_signals(user_id="u-1")

    service.create_signal(
        user_id="u-2",
        strategy_id="u-2-mean-revert",
        account_id="u-2-account-a",
        symbol="AAPL",
        side="BUY",
    )

    search_payload = _run(
        cli._cmd_search,
        capsys=capsys,
        user_id="u-1",
        keyword="mean",
        strategy_id=None,
        account_id=account_a,
        symbol=None,
        status=None,
    )
    assert search_payload["success"] is True
    assert [item["id"] for item in search_payload["data"]] == [pending_a.id, expired_a.id]

    dashboard_payload = _run(
        cli._cmd_dashboard,
        capsys=capsys,
        user_id="u-1",
        keyword=None,
        strategy_id=None,
        account_id=account_a,
        symbol=None,
    )
    assert dashboard_payload["success"] is True

    dashboard = dashboard_payload["data"]
    assert dashboard["total"] == 2
    assert dashboard["pending"] == 1
    assert dashboard["expired"] == 1
    assert dashboard["executed"] == 0


def test_cli_signal_get_rejects_foreign_signal(capsys, monkeypatch):
    service = _build_service()
    monkeypatch.setattr(cli, "_service", service)

    foreign = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-mean-revert",
        account_id="u-2-account-a",
        symbol="AAPL",
        side="BUY",
    )

    payload = _run(
        cli._cmd_signal_get,
        capsys=capsys,
        user_id="u-1",
        signal_id=foreign.id,
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_ACCESS_DENIED"
