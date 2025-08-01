"""/ws/monitor 协议与权限测试。"""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from monitoring_realtime.app import create_app
from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore


def _build_auth_state(*, email: str = "ws-protocol@example.com") -> tuple[UserRepository, SessionStore, str, str]:
    repo = UserRepository()
    sessions = SessionStore()
    user = User.register(email=email, password="StrongPass123!")
    repo.save(user)
    session = Session.create(user_id=user.id)
    sessions.save(session)
    return repo, sessions, session.token, user.id


def test_ping_returns_standard_pong_envelope():
    repo, sessions, token, _user_id = _build_auth_state()
    app = create_app(user_repo=repo, session_store=sessions)
    client = TestClient(app)

    with client.websocket_connect("/ws/monitor", headers={"Authorization": f"Bearer {token}"}) as ws:
        heartbeat = ws.receive_json()
        assert heartbeat["type"] == "monitor.heartbeat"

        ws.send_json({"type": "ping", "timestamp": 1700000000})
        pong = ws.receive_json()

        assert pong["type"] == "pong"
        assert pong["payload"]["echo"] == 1700000000
        assert isinstance(pong["timestamp"], int)


def test_unsubscribe_alerts_channel_does_not_push_risk_alert():
    repo, sessions, token, user_id = _build_auth_state()

    def _signals_source(_uid: str):
        return [{"id": "s-1", "userId": user_id, "symbol": "AAPL"}]

    def _alerts_source(_uid: str):
        return [{"id": "a-1", "userId": user_id, "severity": "high"}]

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        signal_source=_signals_source,
        alert_source=_alerts_source,
    )
    client = TestClient(app)

    with client.websocket_connect("/ws/monitor", headers={"Authorization": f"Bearer {token}"}) as ws:
        ws.receive_json()  # heartbeat

        ws.send_json({"type": "unsubscribe", "payload": {"channels": ["alerts"]}})
        unsubscribed = ws.receive_json()
        assert unsubscribed["type"] == "unsubscribed"

        ws.send_json({"type": "poll"})
        pushed = ws.receive_json()
        assert pushed["type"] == "signals_update"


def test_signals_update_filters_out_foreign_user_items():
    repo, sessions, token, user_id = _build_auth_state()

    def _signals_source(_uid: str):
        return [
            {"id": "s-1", "userId": user_id, "symbol": "AAPL"},
            {"id": "s-2", "userId": "other-user", "symbol": "MSFT"},
        ]

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        signal_source=_signals_source,
        alert_source=lambda _uid: [],
    )
    client = TestClient(app)

    with client.websocket_connect("/ws/monitor", headers={"Authorization": f"Bearer {token}"}) as ws:
        ws.receive_json()  # heartbeat

        ws.send_json({"type": "poll"})
        pushed = ws.receive_json()

        assert pushed["type"] == "signals_update"
        items = pushed["data"]["items"]
        assert len(items) == 1
        assert items[0]["userId"] == user_id


def test_auth_failure_log_masks_header_cookie_and_token(caplog):
    repo, sessions, _token, _user_id = _build_auth_state()
    app = create_app(user_repo=repo, session_store=sessions)
    client = TestClient(app)

    raw_header_token = "very-secret-header-token-123456"
    raw_cookie_token = "very-secret-cookie-token-654321"
    client.cookies.set("session_token", raw_cookie_token)

    logger_name = "monitoring_realtime.auth"
    with caplog.at_level(logging.WARNING, logger=logger_name):
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(
                "/ws/monitor",
                headers={"Authorization": f"Bearer {raw_header_token}"},
            ) as ws:
                ws.receive_json()

    assert exc.value.code == 4401
    assert raw_header_token not in caplog.text
    assert raw_cookie_token not in caplog.text
    assert "very***" in caplog.text

