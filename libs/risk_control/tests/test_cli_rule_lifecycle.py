"""risk_control 规则生命周期 CLI 测试。"""

from __future__ import annotations

import argparse
import json

from risk_control import cli
from risk_control.repository import InMemoryRiskRepository
from risk_control.service import RiskControlService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def test_cli_applicable_rules_and_dashboard(capsys, monkeypatch):
    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)

    service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        strategy_id="s-1",
        rule_name="strategy-drawdown",
        threshold=0.2,
    )

    payload = _run(
        cli._cmd_applicable_rules,
        capsys=capsys,
        user_id="u-1",
        account_id="u-1-account",
        strategy_id="s-1",
    )
    assert payload["success"] is True
    assert len(payload["data"]) == 1

    dashboard = _run(cli._cmd_dashboard, capsys=capsys, user_id="u-1", account_id="u-1-account")
    assert dashboard["success"] is True
    assert dashboard["data"]["accountId"] == "u-1-account"
