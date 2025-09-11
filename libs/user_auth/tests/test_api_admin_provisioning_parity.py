"""user_auth 管理员创建用户 API 对齐测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from user_auth.app import create_app
from user_auth.repository import UserRepository
from user_auth.session import SessionStore


def _register_verify_login(client: TestClient, *, email: str, password: str) -> str:
    reg = client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    verify = client.post("/auth/verify-email", json={"email": email})
    assert verify.status_code == 200
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["data"]["token"]


def test_admin_can_create_user_with_initial_role_level_and_status():
    repo = UserRepository()
    sessions = SessionStore()
    client = TestClient(create_app(user_repo=repo, session_store=sessions))

    _register_verify_login(client, email="admin-provision@example.com", password="StrongPass123!")
    admin = repo.get_by_email("admin-provision@example.com")
    assert admin is not None
    admin.set_role("admin")
    admin.set_level(2)
    repo.save(admin)

    admin_login = client.post(
        "/auth/login",
        json={"email": "admin-provision@example.com", "password": "StrongPass123!"},
    )
    admin_token = admin_login.json()["data"]["token"]

    created = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "seeded-user@example.com",
            "password": "SeededPass123!",
            "displayName": "Seeded",
            "role": "admin",
            "level": 2,
            "isActive": False,
            "emailVerified": True,
        },
    )

    assert created.status_code == 200
    payload = created.json()
    assert payload["success"] is True
    assert payload["data"]["email"] == "seeded-user@example.com"
    assert payload["data"]["displayName"] == "Seeded"
    assert payload["data"]["role"] == "admin"
    assert payload["data"]["level"] == 2
    assert payload["data"]["isActive"] is False
    assert payload["data"]["emailVerified"] is True

    disabled_login = client.post(
        "/auth/login",
        json={"email": "seeded-user@example.com", "password": "SeededPass123!"},
    )
    assert disabled_login.status_code == 403
    assert disabled_login.json()["detail"] == "USER_DISABLED"


def test_non_admin_cannot_create_user_and_repo_keeps_clean():
    repo = UserRepository()
    sessions = SessionStore()
    client = TestClient(create_app(user_repo=repo, session_store=sessions))

    normal_token = _register_verify_login(client, email="normal-provision@example.com", password="StrongPass123!")

    denied = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {normal_token}"},
        json={
            "email": "denied-user@example.com",
            "password": "DeniedPass123!",
            "displayName": "Denied",
        },
    )

    assert denied.status_code == 403
    payload = denied.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"
    assert repo.get_by_email("denied-user@example.com") is None
