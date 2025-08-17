"""risk_control 账户评估快照与 evaluate CLI 测试。"""

from __future__ import annotations

import argparse
import json

from risk_control import cli
from risk_control.repository import InMemoryRiskRepository
from risk_control.service import RiskControlService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _setup(monkeypatch) -> RiskControlService:
    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)
    return service


def test_cli_snapshot_and_evaluate_happy_path(capsys, monkeypatch):
    _setup(monkeypatch)

    missing = _run(cli._cmd_assessment_snapshot, capsys=capsys, user_id="u-1", account_id="u-1-account")
    assert missing["success"] is False
    assert missing["error"]["code"] == "ASSESSMENT_NOT_FOUND"

    evaluated = _run(cli._cmd_assessment_evaluate, capsys=capsys, user_id="u-1", account_id="u-1-account")
    assert evaluated["success"] is True
    assert evaluated["data"]["accountId"] == "u-1-account"

    snapshot = _run(cli._cmd_assessment_snapshot, capsys=capsys, user_id="u-1", account_id="u-1-account")
    assert snapshot["success"] is True
    assert snapshot["data"]["accountId"] == "u-1-account"


def test_cli_snapshot_and_evaluate_reject_foreign_account(capsys, monkeypatch):
    _setup(monkeypatch)

    denied_snapshot = _run(
        cli._cmd_assessment_snapshot,
        capsys=capsys,
        user_id="u-1",
        account_id="u-2-account",
    )
    assert denied_snapshot["success"] is False
    assert denied_snapshot["error"]["code"] == "RULE_ACCESS_DENIED"

    denied_evaluate = _run(
        cli._cmd_assessment_evaluate,
        capsys=capsys,
        user_id="u-1",
        account_id="u-2-account",
    )
    assert denied_evaluate["success"] is False
    assert denied_evaluate["error"]["code"] == "RULE_ACCESS_DENIED"
