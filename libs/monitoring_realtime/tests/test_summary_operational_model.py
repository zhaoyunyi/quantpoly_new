"""monitoring_realtime 运营摘要读模型测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from monitoring_realtime.app import create_app
from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore


def _build_auth_state(*, email: str = "summary-operational@example.com") -> tuple[UserRepository, SessionStore, str, str]:
    repo = UserRepository()
    sessions = SessionStore()
    user = User.register(email=email, password="StrongPass123!")
    repo.save(user)
    session = Session.create(user_id=user.id)
    sessions.save(session)
    return repo, sessions, session.token, user.id


def test_summary_operational_model_counts_tasks_and_filters_foreign_items():
    repo, sessions, token, user_id = _build_auth_state()

    accounts = [
        {"id": "acc-1", "userId": user_id, "status": "active"},
        {"id": "acc-2", "userId": "u-foreign", "status": "active"},
    ]
    strategies = [
        {"id": "st-1", "userId": user_id, "status": "active"},
        {"id": "st-2", "userId": user_id, "status": "draft"},
        {"id": "st-x", "userId": "u-foreign", "status": "active"},
    ]
    backtests = [
        {"id": "bt-1", "userId": user_id, "status": "running"},
        {"id": "bt-2", "userId": user_id, "status": "completed"},
        {"id": "bt-x", "userId": "u-foreign", "status": "running"},
    ]
    tasks = [
        {"taskId": "job-1", "userId": user_id, "status": "running"},
        {"taskId": "job-2", "userId": user_id, "status": "failed"},
        {"taskId": "job-x", "userId": "u-foreign", "status": "running"},
    ]
    signals = [
        {"id": "sig-1", "userId": user_id, "status": "pending"},
        {"id": "sig-2", "userId": user_id, "status": "expired"},
        {"id": "sig-x", "userId": "u-foreign", "status": "pending"},
    ]
    alerts = [
        {"id": "a-1", "userId": user_id, "severity": "critical", "status": "open"},
        {"id": "a-2", "userId": user_id, "severity": "low", "status": "resolved"},
        {"id": "a-x", "userId": "u-foreign", "severity": "critical", "status": "open"},
    ]

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        account_source=lambda _uid: accounts,
        strategy_source=lambda _uid: strategies,
        backtest_source=lambda _uid: backtests,
        task_source=lambda _uid: tasks,
        signal_source=lambda _uid: signals,
        alert_source=lambda _uid: alerts,
    )
    client = TestClient(app)

    resp = client.get("/monitor/summary", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    summary = payload["data"]
    assert summary["accounts"]["total"] == 1
    assert summary["strategies"]["total"] == 2
    assert summary["backtests"]["running"] == 1
    assert summary["tasks"]["total"] == 2
    assert summary["tasks"]["running"] == 1
    assert summary["tasks"]["failed"] == 1
    assert summary["signals"]["total"] == 2
    assert summary["signals"]["pending"] == 1
    assert summary["signals"]["expired"] == 1
    assert summary["alerts"]["open"] == 1
    assert summary["alerts"]["critical"] == 1


def test_summary_operational_model_returns_stable_empty_structure():
    repo, sessions, token, _user_id = _build_auth_state(email="summary-empty@example.com")

    app = create_app(
        user_repo=repo,
        session_store=sessions,
        account_source=lambda _uid: [],
        strategy_source=lambda _uid: [],
        backtest_source=lambda _uid: [],
        task_source=lambda _uid: [],
        signal_source=lambda _uid: [],
        alert_source=lambda _uid: [],
    )
    client = TestClient(app)

    resp = client.get("/monitor/summary", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    summary = payload["data"]
    assert summary["accounts"]["total"] == 0
    assert summary["strategies"]["total"] == 0
    assert summary["backtests"]["total"] == 0
    assert summary["tasks"]["total"] == 0
    assert summary["signals"]["total"] == 0
    assert summary["alerts"]["open"] == 0
    assert summary["isEmpty"] is True
    assert summary["degraded"]["enabled"] is False
    assert summary["metadata"]["version"] == "v2"
