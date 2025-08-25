"""signal_execution 执行历史保留与治理清理测试（Wave3）。

覆盖变更：update-strategy-signal-automation-parity / 执行历史治理。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str, is_admin: bool):
    from admin_governance.audit import InMemoryAuditLog
    from admin_governance.catalog import default_action_catalog
    from admin_governance.policy import GovernancePolicyEngine
    from admin_governance.token import InMemoryConfirmationTokenStore
    from signal_execution.api import create_router
    from signal_execution.domain import ExecutionRecord
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    class _User:
        def __init__(self, user_id: str, admin: bool):
            self.id = user_id
            self.is_admin = admin

    def _get_current_user():
        return _User(current_user_id, is_admin)

    token_store = InMemoryConfirmationTokenStore()
    audit_log = InMemoryAuditLog()
    engine = GovernancePolicyEngine(
        action_catalog=default_action_catalog(),
        token_store=token_store,
        audit_log=audit_log,
    )

    repo = InMemorySignalRepository()
    service = SignalExecutionService(
        repository=repo,
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
        governance_checker=engine.authorize,
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service, repo, ExecutionRecord, audit_log


def test_cleanup_executions_endpoint_respects_retention_days_and_audits():
    app, service, repo, ExecutionRecord, audit_log = _build_app(current_user_id="admin-1", is_admin=True)
    client = TestClient(app)

    now = datetime.now(timezone.utc)

    repo.save_execution(
        ExecutionRecord(
            id="e-old",
            user_id="u-1",
            signal_id="s-1",
            strategy_id="u-1-strategy",
            symbol="AAPL",
            status="executed",
            metrics={"pnl": 1.0},
            created_at=now - timedelta(days=10),
        )
    )
    repo.save_execution(
        ExecutionRecord(
            id="e-new",
            user_id="u-1",
            signal_id="s-2",
            strategy_id="u-1-strategy",
            symbol="MSFT",
            status="executed",
            metrics={"pnl": 2.0},
            created_at=now - timedelta(days=1),
        )
    )

    resp = client.post(
        "/signals/maintenance/cleanup-executions",
        json={"retentionDays": 3},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["deleted"] == 1
    assert payload["data"]["retentionDays"] == 3
    assert payload["data"]["auditId"]

    remaining = service.list_executions(user_id="u-1")
    assert len(remaining) == 1
    assert remaining[0].id == "e-new"

    records = audit_log.list_records()
    assert records
    latest = records[-1]
    assert latest.action == "signals.cleanup_execution_history"
    assert latest.result == "allowed"
    assert latest.context.get("auditId") == payload["data"]["auditId"]
    assert latest.context.get("retentionDays") == 3


def test_cleanup_executions_endpoint_requires_admin():
    app, _service, _repo, _ExecutionRecord, _audit_log = _build_app(current_user_id="u-1", is_admin=False)
    client = TestClient(app)

    resp = client.post(
        "/signals/maintenance/cleanup-executions",
        json={"retentionDays": 30},
    )

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"

