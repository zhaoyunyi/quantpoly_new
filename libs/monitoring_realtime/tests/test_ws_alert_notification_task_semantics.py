"""monitoring_realtime 风控通知任务推送语义测试。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from monitoring_realtime.app import create_app
from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore


def _build_auth_state(*, email: str) -> tuple[UserRepository, SessionStore, str, str]:
    repo = UserRepository()
    sessions = SessionStore()
    user = User.register(email=email, password="StrongPass123!")
    repo.save(user)
    session = Session.create(user_id=user.id)
    sessions.save(session)
    return repo, sessions, session.token, user.id


def test_poll_pushes_risk_alert_as_snapshot_for_stateful_updates():
    repo, sessions, token, user_id = _build_auth_state(email="alert-snapshot@example.com")

    alerts = [
        {
            "id": "a-1",
            "userId": user_id,
            "severity": "high",
            "status": "open",
        }
    ]

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        signal_source=lambda _uid: [],
        alert_source=lambda _uid: alerts,
    )
    client = TestClient(app)

    with client.websocket_connect("/ws/monitor", headers={"Authorization": f"Bearer {token}"}) as ws:
        ws.receive_json()  # heartbeat
        ws.send_json({"type": "poll"})
        pushed = ws.receive_json()

        assert pushed["type"] == "risk_alert"
        assert pushed["payload"]["snapshot"] is True


def test_risk_alert_payload_includes_notify_task_summary_and_alert_fields():
    repo, sessions, token, user_id = _build_auth_state(email="alert-task@example.com")

    now = datetime.now(timezone.utc)
    alerts = [
        {
            "id": "a-1",
            "userId": user_id,
            "severity": "high",
            "status": "acknowledged",
            "notificationStatus": "sent",
            "notifiedBy": user_id,
            "notifiedAt": now.isoformat(),
        }
    ]

    tasks = [
        {
            "id": "task-1",
            "userId": user_id,
            "taskId": "task-1",
            "taskType": "risk_alert_notify",
            "status": "succeeded",
            "result": {
                "total": 1,
                "success": 1,
                "failed": 0,
                "auditId": "audit-1",
            },
        }
    ]

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        signal_source=lambda _uid: [],
        alert_source=lambda _uid: alerts,
        alert_task_source=lambda _uid: tasks,
    )
    client = TestClient(app)

    with client.websocket_connect("/ws/monitor", headers={"Authorization": f"Bearer {token}"}) as ws:
        ws.receive_json()  # heartbeat
        ws.send_json({"type": "poll"})
        pushed = ws.receive_json()

        assert pushed["type"] == "risk_alert"
        assert pushed["payload"]["taskSummary"]["taskType"] == "risk_alert_notify"
        assert pushed["payload"]["taskSummary"]["result"]["auditId"] == "audit-1"

        item = pushed["data"]["items"][0]
        assert item["notificationStatus"] == "sent"
        assert item["notifiedBy"] == user_id
        assert item["notifiedAt"]

