"""monitoring_realtime 监控摘要信号语义一致性测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from monitoring_realtime.app import create_app
from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore


def _build_auth_state() -> tuple[UserRepository, SessionStore, str, str]:
    repo = UserRepository()
    sessions = SessionStore()
    user = User.register(email="summary-signal@example.com", password="StrongPass123!")
    repo.save(user)
    session = Session.create(user_id=user.id)
    sessions.save(session)
    return repo, sessions, session.token, user.id


def test_summary_signal_pending_and_expired_match_signal_center_semantics():
    repo, sessions, token, user_id = _build_auth_state()

    signals = [
        {"id": "s-1", "userId": user_id, "status": "pending", "symbol": "AAPL"},
        {"id": "s-2", "userId": user_id, "status": "expired", "symbol": "TSLA"},
        {"id": "s-3", "userId": user_id, "status": "executed", "symbol": "MSFT"},
        {"id": "s-4", "userId": "u-foreign", "status": "pending", "symbol": "NVDA"},
    ]

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        signal_source=lambda _uid: signals,
        alert_source=lambda _uid: [],
    )
    client = TestClient(app)

    resp = client.get("/monitor/summary", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    summary = payload["data"]["signals"]
    assert summary["total"] == 3
    assert summary["pending"] == 1
    assert summary["expired"] == 1
