"""monitoring_realtime WS/REST 摘要语义一致性测试。"""

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
    user = User.register(email="summary-ws@example.com", password="StrongPass123!")
    repo.save(user)
    session = Session.create(user_id=user.id)
    sessions.save(session)
    return repo, sessions, session.token, user.id


def test_ws_alert_count_semantics_match_summary():
    repo, sessions, token, user_id = _build_auth_state()

    alerts = [
        {"id": "a-1", "userId": user_id, "severity": "high", "status": "open"},
        {"id": "a-2", "userId": user_id, "severity": "critical", "status": "open"},
    ]

    def _summary_source(_uid: str):
        return {
            "type": "monitor.summary",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "signals": {"total": 0, "pending": 0},
            "alerts": {"open": 2, "critical": 1},
            "tasks": {"running": 0},
        }

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        signal_source=lambda _uid: [],
        alert_source=lambda _uid: alerts,
        summary_source=_summary_source,
    )
    client = TestClient(app)

    rest = client.get("/monitor/summary", headers={"Authorization": f"Bearer {token}"})
    assert rest.status_code == 200
    expected_open_alerts = rest.json()["data"]["alerts"]["open"]

    with client.websocket_connect("/ws/monitor", headers={"Authorization": f"Bearer {token}"}) as ws:
        ws.receive_json()  # heartbeat
        ws.send_json({"type": "poll"})
        pushed = ws.receive_json()

        assert pushed["type"] == "risk_alert"
        assert pushed["payload"]["counts"]["openAlerts"] == expected_open_alerts
        assert pushed["payload"]["counts"]["openAlerts"] == len(pushed["data"]["items"])



def test_ws_alert_counts_align_with_summary_operational_metrics():
    repo, sessions, token, user_id = _build_auth_state()

    alerts = [
        {"id": "a-1", "userId": user_id, "severity": "high", "status": "open"},
        {"id": "a-2", "userId": user_id, "severity": "critical", "status": "open"},
    ]
    tasks = [
        {"taskId": "job-1", "userId": user_id, "status": "running"},
        {"taskId": "job-2", "userId": user_id, "status": "failed"},
    ]

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        signal_source=lambda _uid: [],
        alert_source=lambda _uid: alerts,
        task_source=lambda _uid: tasks,
    )
    client = TestClient(app)

    summary_resp = client.get('/monitor/summary', headers={'Authorization': f'Bearer {token}'})
    assert summary_resp.status_code == 200
    summary = summary_resp.json()['data']

    with client.websocket_connect('/ws/monitor', headers={'Authorization': f'Bearer {token}'}) as ws:
        ws.receive_json()  # heartbeat
        ws.send_json({'type': 'poll'})
        pushed = ws.receive_json()

        assert pushed['type'] == 'risk_alert'
        counts = pushed['payload']['counts']
        assert counts['openAlerts'] == summary['alerts']['open']
        assert counts['criticalAlerts'] == summary['alerts']['critical']
        assert counts['tasksRunning'] == summary['tasks']['running']
