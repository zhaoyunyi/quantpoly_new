"""/ws/monitor WebSocket 鉴权测试。

要求：
- 无 token：拒绝连接（4401）
- 有 token：握手成功，且 1 秒内至少发送 1 条合法消息
- token 优先级：Authorization Bearer > Cookie session_token
"""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from monitoring_realtime.app import create_app
from user_auth.domain import User
from user_auth.session import Session, SessionStore
from user_auth.repository import UserRepository


def _build_auth_state() -> tuple[UserRepository, SessionStore, str]:
    repo = UserRepository()
    sessions = SessionStore()
    user = User.register(email="ws@example.com", password="StrongPass123!")
    repo.save(user)
    session = Session.create(user_id=user.id)
    sessions.save(session)
    return repo, sessions, session.token


class TestMonitorWebSocketAuth:
    """Test /ws/monitor 鉴权行为。"""

    def test_rejects_when_missing_token(self):
        app = create_app()
        client = TestClient(app)

        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws/monitor") as ws:
                ws.receive_json()

        assert exc.value.code == 4401

    def test_rejects_with_4401_when_invalid_token(self):
        app = create_app()
        client = TestClient(app)

        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(
                "/ws/monitor",
                headers={"Authorization": "Bearer invalid-token"},
            ) as ws:
                ws.receive_json()

        assert exc.value.code == 4401

    def test_accepts_with_cookie_token_and_sends_message(self):
        repo, sessions, token = _build_auth_state()
        app = create_app(user_repo=repo, session_store=sessions)
        client = TestClient(app)
        client.cookies.set("session_token", token)

        with client.websocket_connect("/ws/monitor") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "monitor.heartbeat"
            assert isinstance(msg["ts"], int)

    def test_accepts_with_bearer_token(self):
        repo, sessions, token = _build_auth_state()
        app = create_app(user_repo=repo, session_store=sessions)
        client = TestClient(app)

        with client.websocket_connect(
            "/ws/monitor",
            headers={"Authorization": f"Bearer {token}"},
        ) as ws:
            msg = ws.receive_json()
            assert msg["type"] == "monitor.heartbeat"

    def test_prefers_bearer_over_cookie(self):
        repo, sessions, valid_token = _build_auth_state()
        app = create_app(user_repo=repo, session_store=sessions)
        client = TestClient(app)
        client.cookies.set("session_token", valid_token)

        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(
                "/ws/monitor",
                headers={"Authorization": "Bearer invalid-token"},
            ) as ws:
                ws.receive_json()

        assert exc.value.code == 4401

    def test_accepts_legacy_secure_cookie_token_signature(self):
        repo, sessions, token = _build_auth_state()
        app = create_app(user_repo=repo, session_store=sessions)
        client = TestClient(app)
        client.cookies.set("__Secure-better-auth.session_token", f"{token}.signature")

        with client.websocket_connect("/ws/monitor") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "monitor.heartbeat"

    def test_accepts_legacy_better_auth_cookie_token_signature(self):
        repo, sessions, token = _build_auth_state()
        app = create_app(user_repo=repo, session_store=sessions)
        client = TestClient(app)
        client.cookies.set("better-auth.session_token", f"{token}.signature")

        with client.websocket_connect("/ws/monitor") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "monitor.heartbeat"
