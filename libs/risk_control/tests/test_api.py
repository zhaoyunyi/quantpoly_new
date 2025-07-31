"""risk_control API 路由测试。"""

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


def test_batch_acknowledge_returns_403_when_contains_foreign_alert():
    app, service = _build_app(current_user_id="u-1")

    mine = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )
    other = service.create_alert(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )

    client = TestClient(app)
    resp = client.post(
        "/risk/alerts/batch-acknowledge",
        json={"alertIds": [mine.id, other.id]},
    )

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ALERT_ACCESS_DENIED"

    mine_after = service.get_alert(user_id="u-1", alert_id=mine.id)
    assert mine_after is not None
    assert mine_after.status == "open"


def test_stats_returns_403_for_foreign_account_scope():
    app, service = _build_app(current_user_id="u-1")

    service.create_alert(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )

    client = TestClient(app)
    resp = client.get("/risk/alerts/stats", params={"accountId": "u-2-account"})

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ALERT_ACCESS_DENIED"

