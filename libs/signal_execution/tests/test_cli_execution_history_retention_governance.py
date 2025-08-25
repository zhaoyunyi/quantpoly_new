"""signal_execution CLI 执行历史治理测试（Wave3）。"""

from __future__ import annotations

import argparse
import json

import pytest

from signal_execution import cli
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService


@pytest.fixture(autouse=True)
def _reset_cli_state(monkeypatch):
    repo = InMemorySignalRepository()
    service = SignalExecutionService(
        repository=repo,
        strategy_owner_acl=lambda _user_id, _strategy_id: True,
        account_owner_acl=lambda _user_id, _account_id: True,
    )
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)
    return repo, service


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_cleanup_executions_requires_admin(capsys):
    payload = _run(
        cli._cmd_cleanup_executions,
        capsys=capsys,
        user_id="u-1",
        is_admin=False,
        retention_days=30,
        confirmation_token=None,
        audit_id="cli-test",
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"

