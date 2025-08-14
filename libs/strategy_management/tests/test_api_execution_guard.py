"""strategy_management 执行前校验 API 测试。"""

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


def test_validate_execution_rejects_missing_required_parameters():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    resp = client.post(
        f"/strategies/{strategy.id}/validate-execution",
        json={"parameters": {"window": 20, "entryZ": 1.5}},
    )

    assert resp.status_code == 422
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_INVALID_PARAMETERS"


def test_validate_execution_rejects_non_owner_access():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-2",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    resp = client.post(
        f"/strategies/{strategy.id}/validate-execution",
        json={"parameters": {"window": 20, "entryZ": 1.5, "exitZ": 0.5}},
    )

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_ACCESS_DENIED"


def test_validate_execution_passes_for_valid_owner_parameters():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    resp = client.post(
        f"/strategies/{strategy.id}/validate-execution",
        json={"parameters": {"window": 30, "entryZ": 1.8, "exitZ": 0.6}},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["valid"] is True
    assert payload["data"]["strategyId"] == strategy.id
