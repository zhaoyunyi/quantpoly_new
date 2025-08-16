"""admin_governance 与 signal_execution 集成测试。"""

from __future__ import annotations

import pytest


def test_signal_cleanup_all_uses_governance_checker():
    from admin_governance.audit import InMemoryAuditLog
    from admin_governance.catalog import default_action_catalog
    from admin_governance.policy import GovernancePolicyEngine
    from admin_governance.token import InMemoryConfirmationTokenStore
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import AdminRequiredError, SignalExecutionService

    token_store = InMemoryConfirmationTokenStore()
    audit_log = InMemoryAuditLog()
    engine = GovernancePolicyEngine(
        action_catalog=default_action_catalog(),
        token_store=token_store,
        audit_log=audit_log,
    )

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
        governance_checker=engine.authorize,
    )

    service.create_signal(
        user_id="admin-1",
        strategy_id="admin-1-strategy",
        account_id="admin-1-account",
        symbol="AAPL",
        side="BUY",
    )

    with pytest.raises(AdminRequiredError):
        service.cleanup_all_signals(user_id="u-1", is_admin=False, admin_decision_source="none")

    token = token_store.issue(
        actor_id="admin-1",
        action="signals.cleanup_all",
        target="signals",
        ttl_seconds=60,
    )

    deleted = service.cleanup_all_signals(
        user_id="admin-1",
        is_admin=True,
        admin_decision_source="role",
        confirmation_token=token,
    )

    assert deleted == 1
    records = audit_log.list_records()
    assert any(item.action == "signals.cleanup_all" and item.result == "allowed" for item in records)

    last = records[-1]
    assert last.context.get("adminDecisionSource") == "role"
    assert token not in str(last.context)
