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


def _register_and_login(client):
    """辅助：注册并登录，返回 token。"""

    client.post(
        "/auth/register",
        json={"email": "auth@example.com", "password": "StrongPass123!"},
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
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "auth@example.com"

    def test_me_with_cookie_token(self, client):
        token = _register_and_login(client)
        client.cookies.set("session_token", token)
        resp = client.get("/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "auth@example.com"

    def test_me_prefers_bearer_over_cookie(self, client):
        valid_token = _register_and_login(client)
        client.cookies.set("session_token", valid_token)
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401

    def test_me_without_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert resp.status_code == 401

    def test_me_invalid_token_log_is_masked(self, client, caplog):
        raw_token = "very-secret-token-123456"
        with caplog.at_level("WARNING", logger="user_auth.auth"):
            resp = client.get(
                "/auth/me",
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
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 401
