"""monitoring_realtime 摘要 REST 测试。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from monitoring_realtime.app import create_app
from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore


def _build_auth_state() -> tuple[UserRepository, SessionStore, str, str]:
    repo = UserRepository()
    sessions = SessionStore()
    user = User.register(email="summary@example.com", password="StrongPass123!")
    repo.save(user)
    session = Session.create(user_id=user.id)
    sessions.save(session)
    return repo, sessions, session.token, user.id


def test_summary_rest_endpoint_returns_user_scoped_data():
    repo, sessions, token, user_id = _build_auth_state()

    def _summary_source(input_user_id: str):
        assert input_user_id == user_id
        return {
            "type": "monitor.summary",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "signals": {"total": 2, "pending": 1},
            "alerts": {"open": 1, "critical": 1},
            "tasks": {"running": 3},
        }

    app = create_app(user_repo=repo, session_store=sessions, summary_source=_summary_source)
    client = TestClient(app)

    resp = client.get("/monitor/summary", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["type"] == "monitor.summary"
    assert payload["data"]["signals"]["pending"] == 1
    assert payload["data"]["alerts"]["open"] == 1


def test_summary_rest_endpoint_rejects_missing_token():
    app = create_app()
    client = TestClient(app)

    resp = client.get("/monitor/summary")

    assert resp.status_code == 401
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UNAUTHORIZED"
