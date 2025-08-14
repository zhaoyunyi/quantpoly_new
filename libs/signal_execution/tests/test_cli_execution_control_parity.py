"""signal_execution 执行控制面 CLI 测试。"""

from __future__ import annotations

import argparse
import json

from signal_execution import cli
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _build_service() -> SignalExecutionService:
    def _validate_parameters(_user_id: str, _strategy_id: str, parameters: dict) -> None:
        if "window" not in parameters:
            raise ValueError("missing parameter: window")

    return SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
        strategy_parameter_validator=_validate_parameters,
    )


def test_cli_validate_parameters_outputs_error_code(capsys, monkeypatch):
    service = _build_service()
    monkeypatch.setattr(cli, "_service", service)

    payload = _run(
        cli._cmd_validate_parameters,
        capsys=capsys,
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        parameters='{"entryZ": 1.2}',
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_INVALID_PARAMETERS"


def test_cli_execution_detail_and_running(capsys, monkeypatch):
    service = _build_service()
    monkeypatch.setattr(cli, "_service", service)

    pending = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    done = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=done.id)
    my_execution = service.list_executions(user_id="u-1")[0]

    detail = _run(
        cli._cmd_execution_detail,
        capsys=capsys,
        user_id="u-1",
        execution_id=my_execution.id,
    )
    assert detail["success"] is True
    assert detail["data"]["id"] == my_execution.id

    running = _run(cli._cmd_running, capsys=capsys, user_id="u-1")
    assert running["success"] is True
    assert len(running["data"]) == 1
    assert running["data"][0]["signalId"] == pending.id
    assert running["data"][0]["status"] == "pending"
