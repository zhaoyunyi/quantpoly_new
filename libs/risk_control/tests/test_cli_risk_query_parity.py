"""risk_control 快捷查询 CLI 对齐测试。"""

from __future__ import annotations

import argparse
import json

from risk_control import cli
from risk_control.repository import InMemoryRiskRepository
from risk_control.service import RiskControlService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def _setup(monkeypatch):
    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)
    return service


def test_cli_rule_statistics_and_recent_alerts(capsys, monkeypatch):
    service = _setup(monkeypatch)

    service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-loss",
        threshold=0.2,
    )
    inactive = service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-drawdown",
        threshold=0.3,
    )
    service.toggle_rule_status(user_id="u-1", rule_id=inactive.id, is_active=False)

    service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="rule-1",
        severity="high",
        message="m1",
    )
    service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="rule-2",
        severity="high",
        message="m2",
    )

    stats = _run(
        cli._cmd_rule_statistics,
        capsys=capsys,
        user_id="u-1",
        account_id=None,
    )
    assert stats["success"] is True
    assert stats["data"]["total"] == 2
    assert stats["data"]["inactive"] == 1

    recent = _run(
        cli._cmd_recent_alerts,
        capsys=capsys,
        user_id="u-1",
        account_id=None,
        limit=1,
    )
    assert recent["success"] is True
    assert len(recent["data"]) == 1


def test_cli_unresolved_alerts_honors_account_acl(capsys, monkeypatch):
    service = _setup(monkeypatch)
    service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="r1",
        severity="high",
        message="m1",
    )

    denied = _run(
        cli._cmd_unresolved_alerts,
        capsys=capsys,
        user_id="u-1",
        account_id="u-2-account",
        limit=20,
    )
    assert denied["success"] is False
    assert denied["error"]["code"] == "ALERT_ACCESS_DENIED"
