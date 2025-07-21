"""FastAPI 鉴权路由测试 — Red 阶段（第一部分：注册与登录）。

BDD Scenarios:
- 浏览器用户注册
- CLI 用户登录
- 弱口令注册被拒绝
"""
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
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "StrongPass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_register_weak_password(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "password",
        })
        assert resp.status_code in (400, 422)

    def test_register_duplicate_email(self, client):
        client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "StrongPass123!",
        })
        resp = client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "StrongPass123!",
        })
        assert resp.status_code == 409


class TestLogin:
    """Test用户登录路由。"""

    def _register(self, client):
        client.post("/auth/register", json={
            "email": "login@example.com",
            "password": "StrongPass123!",
        })

    def test_login_success_returns_token(self, client):
        self._register(client)
        resp = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "StrongPass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "token" in data["data"]

    def test_login_wrong_password(self, client):
        self._register(client)
        resp = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "WrongPassword1!",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "StrongPass123!",
        })
        assert resp.status_code == 401


def _register_and_login(client):
    """辅助：注册并登录，返回 token。"""
    client.post("/auth/register", json={
        "email": "auth@example.com",
        "password": "StrongPass123!",
    })
    resp = client.post("/auth/login", json={
        "email": "auth@example.com",
        "password": "StrongPass123!",
    })
    return resp.json()["data"]["token"]


class TestMe:
    """Test获取当前用户信息。"""

    def test_me_with_bearer_token(self, client):
        token = _register_and_login(client)
        resp = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "auth@example.com"

    def test_me_without_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token(self, client):
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401


class TestLogout:
    """Test登出撤销会话。"""

    def test_logout_invalidates_token(self, client):
        token = _register_and_login(client)
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        # 登出后 token 应失效
        me_resp = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 401
