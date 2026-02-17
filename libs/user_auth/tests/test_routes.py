"""FastAPI 鉴权路由测试。

BDD Scenarios:
- 浏览器用户注册
- CLI 用户登录
- 获取当前用户信息
- 登出撤销会话
- 同一鉴权依赖对 Bearer/Cookie 一致生效
- 认证失败日志不泄漏明文 token
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from user_auth.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestRegister:
    """Test用户注册路由。"""

    def test_register_success(self, client):
        resp = client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_register_weak_password(self, client):
        resp = client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "password"},
        )
        assert resp.status_code in (400, 422)

    def test_register_duplicate_email(self, client):
        client.post(
            "/auth/register",
            json={"email": "dup@example.com", "password": "StrongPass123!"},
        )
        resp = client.post(
            "/auth/register",
            json={"email": "dup@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 409


class TestLogin:
    """Test用户登录路由。"""

    def _register(self, client):
        client.post(
            "/auth/register",
            json={"email": "login@example.com", "password": "StrongPass123!"},
        )
        client.post(
            "/auth/verify-email",
            json={"email": "login@example.com"},
        )

    def test_login_success_returns_token(self, client):
        self._register(client)
        resp = client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "token" in data["data"]

    def test_login_sets_session_cookie_for_browser(self, client):
        self._register(client)
        resp = client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 200
        assert resp.cookies.get("session_token")

    def test_login_wrong_password(self, client):
        self._register(client)
        resp = client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "WrongPassword1!"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 401

    def test_login_rejects_unverified_email(self, client):
        client.post(
            "/auth/register",
            json={"email": "unverified@example.com", "password": "StrongPass123!"},
        )
        resp = client.post(
            "/auth/login",
            json={"email": "unverified@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 403
        payload = resp.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "EMAIL_NOT_VERIFIED"

    def test_login_allows_after_email_verification(self, client):
        client.post(
            "/auth/register",
            json={"email": "verified@example.com", "password": "StrongPass123!"},
        )
        verify_resp = client.post(
            "/auth/verify-email",
            json={"email": "verified@example.com"},
        )
        assert verify_resp.status_code == 200

        login = client.post(
            "/auth/login",
            json={"email": "verified@example.com", "password": "StrongPass123!"},
        )
        assert login.status_code == 200


def _register_and_login(client):
    """辅助：注册并登录，返回 token。"""

    client.post(
        "/auth/register",
        json={"email": "auth@example.com", "password": "StrongPass123!"},
    )
    client.post(
        "/auth/verify-email",
        json={"email": "auth@example.com"},
    )
    resp = client.post(
        "/auth/login",
        json={"email": "auth@example.com", "password": "StrongPass123!"},
    )
    return resp.json()["data"]["token"]


class TestMe:
    """Test获取当前用户信息。"""

    def test_me_with_bearer_token(self, client):
        token = _register_and_login(client)
        resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "auth@example.com"

    def test_me_with_cookie_token(self, client):
        token = _register_and_login(client)
        client.cookies.set("session_token", token)
        resp = client.get("/users/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "auth@example.com"

    def test_me_prefers_bearer_over_cookie(self, client):
        valid_token = _register_and_login(client)
        client.cookies.set("session_token", valid_token)
        resp = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401

    def test_me_without_token(self, client):
        resp = client.get("/users/me")
        assert resp.status_code == 401
        payload = resp.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "MISSING_TOKEN"

    def test_me_with_invalid_token(self, client):
        resp = client.get("/users/me", headers={"Authorization": "Bearer invalid-token"})
        assert resp.status_code == 401

    def test_me_invalid_token_log_is_masked(self, client, caplog):
        raw_token = "very-secret-token-123456"
        with caplog.at_level("WARNING", logger="user_auth.auth"):
            resp = client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {raw_token}"},
            )

        assert resp.status_code == 401
        assert raw_token not in caplog.text
        assert raw_token[:4] in caplog.text


class TestLogout:
    """Test登出撤销会话。"""

    def test_logout_invalidates_token(self, client):
        token = _register_and_login(client)
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        me_resp = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 401


class TestRouteNormalization:
    def test_auth_me_is_removed_in_breaking_change(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 410
        payload = resp.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "ROUTE_REMOVED"


class TestPasswordReset:
    """Test密码找回与重置流程。"""

    def test_reset_password_flow_invalidates_old_password(self):
        app = create_app(password_reset_test_mode=True)
        client = TestClient(app)

        client.post(
            "/auth/register",
            json={"email": "reset@example.com", "password": "StrongPass123!"},
        )
        client.post(
            "/auth/verify-email",
            json={"email": "reset@example.com"},
        )

        issue = client.post(
            "/auth/password-reset/request",
            json={"email": "reset@example.com"},
        )
        assert issue.status_code == 200
        payload = issue.json()
        assert payload["success"] is True
        assert payload.get("data", {}).get("resetToken")
        reset_token = payload["data"]["resetToken"]

        reset = client.post(
            "/auth/password-reset/confirm",
            json={"token": reset_token, "newPassword": "NewStrongPass123!"},
        )
        assert reset.status_code == 200

        old_login = client.post(
            "/auth/login",
            json={"email": "reset@example.com", "password": "StrongPass123!"},
        )
        assert old_login.status_code == 401

        new_login = client.post(
            "/auth/login",
            json={"email": "reset@example.com", "password": "NewStrongPass123!"},
        )
        assert new_login.status_code == 200

    def test_reset_token_single_use(self):
        app = create_app(password_reset_test_mode=True)
        client = TestClient(app)

        client.post(
            "/auth/register",
            json={"email": "singleuse@example.com", "password": "StrongPass123!"},
        )
        client.post(
            "/auth/verify-email",
            json={"email": "singleuse@example.com"},
        )

        issue = client.post(
            "/auth/password-reset/request",
            json={"email": "singleuse@example.com"},
        )
        token = issue.json()["data"]["resetToken"]

        first = client.post(
            "/auth/password-reset/confirm",
            json={"token": token, "newPassword": "NewStrongPass123!"},
        )
        assert first.status_code == 200

        second = client.post(
            "/auth/password-reset/confirm",
            json={"token": token, "newPassword": "AnotherStrongPass123!"},
        )
        assert second.status_code == 400

    def test_password_reset_request_uses_enumeration_safe_response(self, client):
        existing = client.post(
            "/auth/password-reset/request",
            json={"email": "exists@example.com"},
        )
        missing = client.post(
            "/auth/password-reset/request",
            json={"email": "missing@example.com"},
        )

        assert existing.status_code == 200
        assert missing.status_code == 200
        assert existing.json()["message"] == missing.json()["message"]
        assert "data" not in existing.json() or "resetToken" not in existing.json().get("data", {})
        assert "data" not in missing.json() or "resetToken" not in missing.json().get("data", {})

