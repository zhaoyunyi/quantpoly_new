"""signal_execution 批处理 CLI 测试。"""

from __future__ import annotations

import argparse
import json

from signal_execution import cli
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def test_cli_batch_execute_and_performance(capsys, monkeypatch):
    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-s1",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )

    batch = _run(
        cli._cmd_batch_execute,
        capsys=capsys,
        user_id="u-1",
        signal_ids=s1.id,
        idempotency_key="idem-1",
    )
    assert batch["success"] is True
    assert batch["data"]["executed"] == 1

    perf = _run(cli._cmd_performance, capsys=capsys, user_id="u-1", strategy_id=None, symbol=None)
    assert perf["success"] is True
    assert perf["data"]["totalExecutions"] == 1
