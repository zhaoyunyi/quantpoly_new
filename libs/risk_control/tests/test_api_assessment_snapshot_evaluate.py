"""risk_control 账户评估快照与 evaluate API 测试。"""

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


def test_assessment_snapshot_and_evaluate_endpoints_work_for_owner():
    app, _service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    missing = client.get("/risk/accounts/u-1-account/snapshot")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ASSESSMENT_NOT_FOUND"

    evaluated = client.post("/risk/accounts/u-1-account/evaluate")
    assert evaluated.status_code == 200
    assert evaluated.json()["data"]["accountId"] == "u-1-account"

    snapshot = client.get("/risk/accounts/u-1-account/snapshot")
    assert snapshot.status_code == 200
    assert snapshot.json()["data"]["accountId"] == "u-1-account"


def test_assessment_snapshot_and_evaluate_reject_foreign_account():
    app, _service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    denied_snapshot = client.get("/risk/accounts/u-2-account/snapshot")
    assert denied_snapshot.status_code == 403
    assert denied_snapshot.json()["error"]["code"] == "RULE_ACCESS_DENIED"

    denied_evaluate = client.post("/risk/accounts/u-2-account/evaluate")
    assert denied_evaluate.status_code == 403
    assert denied_evaluate.json()["error"]["code"] == "RULE_ACCESS_DENIED"
