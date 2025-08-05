"""risk_control 规则生命周期 API 测试。"""

from __future__ import annotations

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


def test_rule_lifecycle_and_assessment_endpoints():
    app, _service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    create_resp = client.post(
        "/risk/rules",
        json={
            "accountId": "u-1-account",
            "strategyId": "s-1",
            "ruleName": "strategy-drawdown",
            "threshold": 0.2,
        },
    )
    assert create_resp.status_code == 200
    rule_id = create_resp.json()["data"]["id"]

    list_resp = client.get("/risk/rules", params={"accountId": "u-1-account"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1

    toggle_resp = client.patch(f"/risk/rules/{rule_id}/toggle", json={"isActive": False})
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["data"]["isActive"] is False

    applicable_resp = client.get(
        "/risk/rules/applicable/u-1-account",
        params={"strategyId": "s-1"},
    )
    assert applicable_resp.status_code == 200
    assert applicable_resp.json()["data"] == []

    assess_resp = client.post("/risk/check/account/u-1-account")
    assert assess_resp.status_code == 200
    assert assess_resp.json()["data"]["accountId"] == "u-1-account"

    dashboard_resp = client.get("/risk/dashboard/u-1-account")
    assert dashboard_resp.status_code == 200
    assert dashboard_resp.json()["data"]["accountId"] == "u-1-account"


def test_rule_create_rejects_foreign_account_with_403():
    app, _service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    resp = client.post(
        "/risk/rules",
        json={
            "accountId": "u-2-account",
            "ruleName": "max-loss",
            "threshold": 0.1,
        },
    )

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "RULE_ACCESS_DENIED"
