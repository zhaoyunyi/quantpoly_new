"""admin_governance 与 user_auth 管理员开通用户集成测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_admin_create_user_action_is_audited_and_masked():
    from admin_governance.audit import InMemoryAuditLog
    from admin_governance.catalog import default_action_catalog
    from admin_governance.policy import GovernancePolicyEngine
    from admin_governance.token import InMemoryConfirmationTokenStore
    from user_auth.app import create_app
    from user_auth.repository import UserRepository
    from user_auth.session import SessionStore

    token_store = InMemoryConfirmationTokenStore()
    audit_log = InMemoryAuditLog()
    engine = GovernancePolicyEngine(
        action_catalog=default_action_catalog(),
        token_store=token_store,
        audit_log=audit_log,
    )

    repo = UserRepository()
    sessions = SessionStore()
    app = create_app(user_repo=repo, session_store=sessions, governance_checker=engine.authorize)
    client = TestClient(app)

    client.post("/auth/register", json={"email": "admin-provision-audit@example.com", "password": "StrongPass123!"})
    client.post("/auth/verify-email", json={"email": "admin-provision-audit@example.com"})

    admin = repo.get_by_email("admin-provision-audit@example.com")
    assert admin is not None
    admin.set_role("admin")
    admin.set_level(2)
    repo.save(admin)

    admin_login = client.post(
        "/auth/login",
        json={"email": "admin-provision-audit@example.com", "password": "StrongPass123!"},
    )
    admin_token = admin_login.json()["data"]["token"]

    created = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "governed-seeded@example.com",
            "password": "GovernedPass123!",
            "displayName": "Governed",
            "role": "user",
            "level": 1,
            "isActive": True,
            "emailVerified": True,
        },
    )
    assert created.status_code == 200

    records = audit_log.list_records()
    assert records
    last = records[-1]
    assert last.action == "admin_create_user"
    assert last.actor == admin.id
    assert last.target == "governed-seeded@example.com"

    context_text = str(last.context)
    assert admin_token not in context_text
    assert "GovernedPass123!" not in context_text
    assert last.context.get("adminDecisionSource") == "role_level"
