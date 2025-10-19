"""strategy_management 模板目录能力对齐 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


class _User:
    def __init__(self, user_id: str):
        self.id = user_id


def _build_client(*, current_user_id: str = "u-1") -> TestClient:
    from strategy_management.api import create_router
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    def _get_current_user():
        return _User(current_user_id)

    service = StrategyService(
        repository=InMemoryStrategyRepository(),
        count_active_backtests=lambda user_id, strategy_id: 0,
    )
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return TestClient(app)


def test_api_template_list_covers_core_templates_with_schema_fields():
    client = _build_client()

    resp = client.get("/strategies/templates")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    templates = payload["data"]
    template_ids = {item["templateId"] for item in templates}
    assert {
        "moving_average",
        "bollinger_bands",
        "rsi",
        "macd",
        "mean_reversion",
        "momentum",
    }.issubset(template_ids)

    for item in templates:
        assert "requiredParameters" in item
        assert "defaults" in item


def test_api_create_from_template_rejects_invalid_macd_parameter_relationship():
    client = _build_client()

    resp = client.post(
        "/strategies/from-template",
        json={
            "name": "macd-invalid",
            "templateId": "macd",
            "parameters": {"fast": 30, "slow": 10, "signal": 9},
        },
    )

    assert resp.status_code == 422
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_INVALID_PARAMETERS"
    assert "fast" in payload["error"]["message"].lower()


def test_api_create_and_update_strategy_follow_template_schema_validation():
    client = _build_client()

    created = client.post(
        "/strategies/from-template",
        json={
            "name": "ma-valid",
            "templateId": "moving_average",
            "parameters": {"shortWindow": 5, "longWindow": 20},
        },
    )

    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["success"] is True
    strategy_id = created_payload["data"]["id"]

    updated = client.put(
        f"/strategies/{strategy_id}",
        json={
            "parameters": {"shortWindow": 20, "longWindow": 10},
        },
    )

    assert updated.status_code == 422
    update_payload = updated.json()
    assert update_payload["success"] is False
    assert update_payload["error"]["code"] == "STRATEGY_INVALID_PARAMETERS"
    assert "longwindow" in update_payload["error"]["message"].lower()
