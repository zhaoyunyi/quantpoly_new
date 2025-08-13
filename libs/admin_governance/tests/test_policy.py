"""admin_governance 策略与审计测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


def test_normal_user_denied_for_high_risk_action():
    from admin_governance.audit import InMemoryAuditLog
    from admin_governance.catalog import default_action_catalog
    from admin_governance.policy import GovernanceAccessDeniedError, GovernancePolicyEngine
    from admin_governance.token import InMemoryConfirmationTokenStore

    engine = GovernancePolicyEngine(
        action_catalog=default_action_catalog(),
        token_store=InMemoryConfirmationTokenStore(),
        audit_log=InMemoryAuditLog(),
    )

    with pytest.raises(GovernanceAccessDeniedError):
        engine.authorize(
            actor_id="u-1",
            role="user",
            level=1,
            action="signals.cleanup_all",
            target="signals",
        )


def test_confirmation_token_single_use_and_ttl():
    from admin_governance.audit import InMemoryAuditLog
    from admin_governance.catalog import default_action_catalog
    from admin_governance.policy import ConfirmationRequiredError, GovernancePolicyEngine
    from admin_governance.token import InMemoryConfirmationTokenStore

    now = datetime(2026, 2, 8, tzinfo=timezone.utc)
    state = {"now": now}

    def _clock():
        return state["now"]

    token_store = InMemoryConfirmationTokenStore(clock=_clock)
    engine = GovernancePolicyEngine(
        action_catalog=default_action_catalog(),
        token_store=token_store,
        audit_log=InMemoryAuditLog(),
    )

    token = token_store.issue(
        actor_id="admin-1",
        action="signals.cleanup_all",
        target="signals",
        ttl_seconds=60,
    )

    allowed = engine.authorize(
        actor_id="admin-1",
        role="admin",
        level=10,
        action="signals.cleanup_all",
        target="signals",
        confirmation_token=token,
    )
    assert allowed.allowed is True

    with pytest.raises(ConfirmationRequiredError):
        engine.authorize(
            actor_id="admin-1",
            role="admin",
            level=10,
            action="signals.cleanup_all",
            target="signals",
            confirmation_token=token,
        )

    expired = token_store.issue(
        actor_id="admin-1",
        action="signals.cleanup_all",
        target="signals",
        ttl_seconds=10,
    )
    state["now"] = now + timedelta(seconds=11)

    with pytest.raises(ConfirmationRequiredError):
        engine.authorize(
            actor_id="admin-1",
            role="admin",
            level=10,
            action="signals.cleanup_all",
            target="signals",
            confirmation_token=expired,
        )


def test_audit_log_masks_sensitive_fields():
    from admin_governance.audit import InMemoryAuditLog
    from admin_governance.catalog import default_action_catalog
    from admin_governance.policy import GovernancePolicyEngine
    from admin_governance.token import InMemoryConfirmationTokenStore

    audit_log = InMemoryAuditLog()
    token_store = InMemoryConfirmationTokenStore()
    engine = GovernancePolicyEngine(
        action_catalog=default_action_catalog(),
        token_store=token_store,
        audit_log=audit_log,
    )

    token = token_store.issue(
        actor_id="admin-1",
        action="signals.cleanup_all",
        target="signals",
        ttl_seconds=60,
    )

    engine.authorize(
        actor_id="admin-1",
        role="admin",
        level=10,
        action="signals.cleanup_all",
        target="signals",
        confirmation_token=token,
        context={"token": "very-secret-token", "cookie": "session_cookie_secret", "password": "StrongPass123!"},
    )

    records = audit_log.list_records()
    assert len(records) >= 1
    text = str(records[-1].context)
    assert "very-secret-token" not in text
    assert "session_cookie_secret" not in text
    assert "StrongPass123!" not in text


def test_catalog_contains_users_delete_action():
    from admin_governance.catalog import default_action_catalog

    catalog = default_action_catalog()

    assert "users.delete" in catalog
    policy = catalog["users.delete"]
    assert policy.min_role == "admin"
    assert policy.min_level == 2
