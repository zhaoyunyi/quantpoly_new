"""user_auth 用户治理路由测试。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from user_auth.app import create_app
from user_auth.repository import UserRepository
from user_auth.session import SessionStore


@pytest.fixture
def client():
    return TestClient(create_app())


def _register_verify_login(client: TestClient, *, email: str, password: str) -> str:
    reg = client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    verify = client.post("/auth/verify-email", json={"email": email})
    assert verify.status_code == 200
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["data"]["token"]


def test_patch_users_me_updates_profile(client: TestClient):
    token = _register_verify_login(client, email="self-update@example.com", password="StrongPass123!")

    resp = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"displayName": "Alice"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["displayName"] == "Alice"


def test_patch_users_me_password_invalidates_old_session(client: TestClient):
    token = _register_verify_login(client, email="pwd-update@example.com", password="StrongPass123!")

    change = client.patch(
        "/users/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "currentPassword": "StrongPass123!",
            "newPassword": "NewStrongPass123!",
        },
    )
    assert change.status_code == 200

    me_with_old = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_with_old.status_code == 401

    login_new = client.post(
        "/auth/login",
        json={"email": "pwd-update@example.com", "password": "NewStrongPass123!"},
    )
    assert login_new.status_code == 200


def test_non_admin_access_admin_users_returns_403(client: TestClient):
    token = _register_verify_login(client, email="normal@example.com", password="StrongPass123!")

    resp = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"


def test_delete_users_me_revokes_sessions_and_removes_user(client: TestClient):
    token = _register_verify_login(client, email="self-delete@example.com", password="StrongPass123!")

    deleted = client.delete("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert deleted.status_code == 200
    assert deleted.json()["success"] is True

    me_after_delete = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after_delete.status_code == 401

    re_register = client.post(
        "/auth/register",
        json={"email": "self-delete@example.com", "password": "StrongPass123!"},
    )
    assert re_register.status_code == 200


def test_admin_can_list_and_update_user():
    repo = UserRepository()
    sessions = SessionStore()
    client = TestClient(create_app(user_repo=repo, session_store=sessions))

    _register_verify_login(client, email="admin@example.com", password="StrongPass123!")
    admin = repo.get_by_email("admin@example.com")
    assert admin is not None
    admin.set_role("admin")
    admin.set_level(2)
    repo.save(admin)

    admin_login = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "StrongPass123!"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["data"]["token"]

    _register_verify_login(client, email="target@example.com", password="StrongPass123!")

    list_resp = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_resp.status_code == 200
    users = list_resp.json()["data"]["items"]
    assert any(item["email"] == "target@example.com" for item in users)

    target = repo.get_by_email("target@example.com")
    assert target is not None
    disable = client.patch(
        f"/admin/users/{target.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"isActive": False, "level": 2},
    )

    assert disable.status_code == 200
    result = disable.json()["data"]
    assert result["isActive"] is False
    assert result["level"] == 2


def test_admin_can_get_and_delete_target_user():
    repo = UserRepository()
    sessions = SessionStore()
    client = TestClient(create_app(user_repo=repo, session_store=sessions))

    _register_verify_login(client, email="admin-delete@example.com", password="StrongPass123!")
    admin = repo.get_by_email("admin-delete@example.com")
    assert admin is not None
    admin.set_role("admin")
    admin.set_level(2)
    repo.save(admin)

    admin_login = client.post(
        "/auth/login",
        json={"email": "admin-delete@example.com", "password": "StrongPass123!"},
    )
    admin_token = admin_login.json()["data"]["token"]

    _register_verify_login(client, email="target-delete@example.com", password="StrongPass123!")
    target = repo.get_by_email("target-delete@example.com")
    assert target is not None

    got = client.get(
        f"/admin/users/{target.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert got.status_code == 200
    assert got.json()["data"]["email"] == "target-delete@example.com"

    deleted = client.delete(
        f"/admin/users/{target.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert deleted.status_code == 200

    not_found = client.get(
        f"/admin/users/{target.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert not_found.status_code == 404


def test_non_admin_cannot_delete_admin_target(client: TestClient):
    token = _register_verify_login(client, email="normal-delete@example.com", password="StrongPass123!")

    denied = client.delete(
        "/admin/users/any-user-id",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert denied.status_code == 403
    payload = denied.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"
