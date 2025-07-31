"""risk_control CLI 测试。"""

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


def test_cli_stats_outputs_current_user_counts(capsys, monkeypatch):
    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)

    service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )
    service.create_alert(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )

    payload = _run(cli._cmd_stats, capsys=capsys, user_id="u-1", account_id=None)

    assert payload["success"] is True
    assert payload["data"]["total"] == 1


def test_cli_batch_acknowledge_returns_access_denied(capsys, monkeypatch):
    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    monkeypatch.setattr(cli, "_service", service)

    mine = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )
    other = service.create_alert(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )

    payload = _run(
        cli._cmd_batch_acknowledge,
        capsys=capsys,
        user_id="u-1",
        alert_ids=f"{mine.id},{other.id}",
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "ALERT_ACCESS_DENIED"

