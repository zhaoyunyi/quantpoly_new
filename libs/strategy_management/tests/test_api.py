"""strategy_management API 路由测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str, active_count: int = 0):
    from strategy_management.api import create_router
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda _strategy_id: active_count)
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_get_strategy_returns_403_for_non_owner():
    app, service = _build_app(current_user_id="u-1")
    created = service.create_strategy(
        user_id="u-2",
        name="other-strategy",
        template="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    resp = client.get(f"/strategies/{created.id}")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_ACCESS_DENIED"


def test_delete_strategy_returns_409_when_active_backtests_exist():
    app, service = _build_app(current_user_id="u-1", active_count=2)
    created = service.create_strategy(
        user_id="u-1",
        name="my-strategy",
        template="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    resp = client.delete(f"/strategies/{created.id}")

    assert resp.status_code == 409
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_IN_USE"


def test_list_strategy_uses_envelope_and_camel_case_fields():
    app, service = _build_app(current_user_id="u-1")
    service.create_strategy(
        user_id="u-1",
        name="my-strategy",
        template="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    resp = client.get("/strategies")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert len(payload["data"]) == 1
    item = payload["data"][0]
    assert "userId" in item
    assert "createdAt" in item
    assert "updatedAt" in item

