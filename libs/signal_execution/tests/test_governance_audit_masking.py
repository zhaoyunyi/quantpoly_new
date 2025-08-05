"""signal_execution 治理审计脱敏测试。"""

from __future__ import annotations


def test_cleanup_all_audit_masks_confirmation_token():
    from admin_governance.audit import InMemoryAuditLog
    from admin_governance.catalog import default_action_catalog
    from admin_governance.policy import GovernancePolicyEngine
    from admin_governance.token import InMemoryConfirmationTokenStore
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

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
        strategy_id="admin-1-s1",
        account_id="admin-1-account",
        symbol="AAPL",
        side="BUY",
    )

    confirmation_token = token_store.issue(
        actor_id="admin-1",
        action="signals.cleanup_all",
        target="signals",
        ttl_seconds=30,
    )

    deleted = service.cleanup_all_signals(
        user_id="admin-1",
        is_admin=True,
        confirmation_token=confirmation_token,
    )

    assert deleted == 1

    records = audit_log.list_records()
    assert records
    latest = records[-1]
    assert latest.result == "allowed"
    assert latest.context["token"] != confirmation_token
    assert latest.context["token"].endswith("***")
