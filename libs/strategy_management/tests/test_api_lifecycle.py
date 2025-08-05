"""策略生命周期 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from strategy_management.api import create_router
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda _strategy_id: 0)
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_templates_endpoint_and_create_from_template():
    app, _ = _build_app(current_user_id="u-1")
    client = TestClient(app)

    templates = client.get("/strategies/templates")
    assert templates.status_code == 200
    assert templates.json()["success"] is True

    created = client.post(
        "/strategies/from-template",
        json={
            "name": "mr-api",
            "templateId": "mean_reversion",
            "parameters": {"window": 20, "entryZ": 1.5, "exitZ": 0.5},
        },
    )
    assert created.status_code == 200
    assert created.json()["data"]["status"] == "draft"


def test_activate_endpoint_changes_status_to_active():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    activated = client.post(f"/strategies/{strategy.id}/activate")

    assert activated.status_code == 200
    assert activated.json()["data"]["status"] == "active"


def test_activate_archived_strategy_returns_409():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )
    service.archive_strategy(user_id="u-1", strategy_id=strategy.id)

    client = TestClient(app)
    denied = client.post(f"/strategies/{strategy.id}/activate")

    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "STRATEGY_INVALID_TRANSITION"
