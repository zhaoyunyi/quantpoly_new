from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from strategy_health.api import create_router
from strategy_health.repository import InMemoryHealthReportRepository
from strategy_health.service import StrategyHealthService


class _User:
    def __init__(self, user_id: str) -> None:
        self.id = user_id


def _build_client(
    *,
    market_history_reader=None,
    current_user_id: str = "u-1",
):
    repository = InMemoryHealthReportRepository()
    service = StrategyHealthService(
        repository=repository,
        market_history_reader=market_history_reader,
    )

    def _get_current_user():
        return _User(current_user_id)

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return TestClient(app), repository


def test_api_should_return_422_for_unsupported_templates():
    client, repository = _build_client()

    response = client.post(
        "/strategy-health",
        json={
            "template": "macd",
            "parameters": {"fast": 12, "slow": 26, "signal": 9},
            "symbol": "AAPL",
            "startDate": "2026-01-01",
            "endDate": "2026-01-31",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UNSUPPORTED_TEMPLATE"

    reports = repository.list_by_user(user_id="u-1")
    assert len(reports) == 1
    assert reports[0].status == "failed"


def test_api_should_return_422_and_persist_failed_status_when_market_history_reader_raises():
    def _market_history_reader(**_: object):
        raise RuntimeError("provider timeout")

    client, repository = _build_client(market_history_reader=_market_history_reader)

    response = client.post(
        "/strategy-health",
        json={
            "template": "moving_average",
            "parameters": {"shortWindow": 2, "longWindow": 3},
            "symbol": "AAPL",
            "startDate": "2026-01-01",
            "endDate": "2026-01-31",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "MARKET_DATA_UNAVAILABLE"

    reports = repository.list_by_user(user_id="u-1")
    assert len(reports) == 1
    assert reports[0].status == "failed"
    assert reports[0].report == {"error": "provider timeout"}
