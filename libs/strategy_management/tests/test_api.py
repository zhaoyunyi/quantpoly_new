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


def test_list_strategy_should_support_status_search_and_pagination():
    app, service = _build_app(current_user_id="u-1")

    s1 = service.create_strategy(
        user_id="u-1",
        name="trend-alpha",
        template="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )
    s2 = service.create_strategy(
        user_id="u-1",
        name="mean-beta",
        template="mean_reversion",
        parameters={"window": 21, "entryZ": 1.6, "exitZ": 0.6},
    )
    s3 = service.create_strategy(
        user_id="u-1",
        name="trend-gamma",
        template="mean_reversion",
        parameters={"window": 22, "entryZ": 1.7, "exitZ": 0.7},
    )

    service.activate_strategy(user_id="u-1", strategy_id=s1.id)
    service.activate_strategy(user_id="u-1", strategy_id=s3.id)

    service.create_strategy(
        user_id="u-2",
        name="trend-foreign",
        template="mean_reversion",
        parameters={"window": 23, "entryZ": 1.8, "exitZ": 0.8},
    )

    client = TestClient(app)

    page1 = client.get(
        "/strategies",
        params={
            "status": "active",
            "search": "trend",
            "page": 1,
            "pageSize": 1,
        },
    )

    assert page1.status_code == 200
    payload = page1.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 2
    assert payload["data"]["page"] == 1
    assert payload["data"]["pageSize"] == 1
    assert len(payload["data"]["items"]) == 1

    item = payload["data"]["items"][0]
    assert item["status"] == "active"
    assert "trend" in item["name"]
    assert item["userId"] == "u-1"
    assert "createdAt" in item
    assert "updatedAt" in item

    page2 = client.get(
        "/strategies",
        params={
            "status": "active",
            "search": "trend",
            "page": 2,
            "pageSize": 1,
        },
    )

    assert page2.status_code == 200
    payload2 = page2.json()
    assert payload2["data"]["total"] == 2
    assert payload2["data"]["page"] == 2
    assert len(payload2["data"]["items"]) == 1
    assert payload2["data"]["items"][0]["id"] != item["id"]

    all_default = client.get("/strategies")
    assert all_default.status_code == 200
    default_payload = all_default.json()["data"]
    assert default_payload["total"] == 3
    assert default_payload["page"] == 1
    assert default_payload["pageSize"] == 20
    assert len(default_payload["items"]) == 3

    assert s2.id in {item_obj["id"] for item_obj in default_payload["items"]}
