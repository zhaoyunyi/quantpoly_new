"""risk_control 快捷查询 API 对齐测试。"""

from __future__ import annotations

from datetime import timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from risk_control.api import create_router
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import RiskControlService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_api_should_return_rule_statistics_scoped_by_user():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    active = service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-loss",
        threshold=0.2,
    )
    inactive = service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-drawdown",
        threshold=0.3,
    )
    service.toggle_rule_status(user_id="u-1", rule_id=inactive.id, is_active=False)

    service.create_rule(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="foreign",
        threshold=0.4,
    )

    resp = client.get("/risk/rules/statistics")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 2
    assert payload["data"]["active"] == 1
    assert payload["data"]["inactive"] == 1
    assert payload["data"]["byState"] == {"active": 1, "inactive": 1}

    assert active.id != inactive.id


def test_api_should_return_recent_and_unresolved_alerts_with_acl_guard():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    a1 = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="rule-1",
        severity="high",
        message="m1",
    )
    a2 = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="rule-2",
        severity="high",
        message="m2",
    )
    a3 = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="rule-3",
        severity="high",
        message="m3",
    )
    a3.created_at = a3.created_at + timedelta(seconds=10)
    service.resolve_alert(user_id="u-1", alert_id=a2.id)

    service.create_alert(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="foreign",
        severity="low",
        message="fx",
    )

    recent = client.get("/risk/alerts/recent", params={"limit": 2})
    assert recent.status_code == 200
    recent_payload = recent.json()
    assert recent_payload["success"] is True
    assert [item["id"] for item in recent_payload["data"]] == [a3.id, a2.id]

    unresolved = client.get("/risk/alerts/unresolved")
    assert unresolved.status_code == 200
    unresolved_payload = unresolved.json()
    assert unresolved_payload["success"] is True
    unresolved_ids = {item["id"] for item in unresolved_payload["data"]}
    assert a1.id in unresolved_ids
    assert a2.id not in unresolved_ids

    denied = client.get("/risk/alerts/unresolved", params={"accountId": "u-2-account"})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "ALERT_ACCESS_DENIED"
