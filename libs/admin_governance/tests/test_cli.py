"""admin_governance CLI 测试。"""

from __future__ import annotations

import argparse
import json

from admin_governance import cli
from admin_governance.audit import InMemoryAuditLog
from admin_governance.catalog import default_action_catalog
from admin_governance.policy import GovernancePolicyEngine
from admin_governance.token import InMemoryConfirmationTokenStore


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_issue_token_and_check_action(capsys, monkeypatch):
    token_store = InMemoryConfirmationTokenStore()
    audit_log = InMemoryAuditLog()
    engine = GovernancePolicyEngine(
        action_catalog=default_action_catalog(),
        token_store=token_store,
        audit_log=audit_log,
    )

    monkeypatch.setattr(cli, "_token_store", token_store)
    monkeypatch.setattr(cli, "_audit_log", audit_log)
    monkeypatch.setattr(cli, "_engine", engine)

    issued = _run(
        cli._cmd_issue_token,
        capsys=capsys,
        actor_id="admin-1",
        action="signals.cleanup_all",
        target="signals",
        ttl=60,
    )
    token = issued["data"]["token"]

    checked = _run(
        cli._cmd_check_action,
        capsys=capsys,
        actor_id="admin-1",
        role="admin",
        level=10,
        action="signals.cleanup_all",
        target="signals",
        confirmation_token=token,
    )

    assert issued["success"] is True
    assert checked["success"] is True
    assert checked["data"]["allowed"] is True

