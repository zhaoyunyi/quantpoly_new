"""backtest_runner API 路由测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from backtest_runner.api import create_router
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    repo = InMemoryBacktestRepository()
    service = BacktestService(repository=repo)
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_create_and_poll_status_happy_path():
    app, _ = _build_app(current_user_id="u-1")
    client = TestClient(app)

    created = client.post(
        "/backtests",
        json={"strategyId": "s-1", "config": {"symbol": "AAPL"}},
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["success"] is True
    task_id = payload["data"]["id"]
    assert payload["data"]["status"] == "pending"

    running = client.post(f"/backtests/{task_id}/transition", json={"toStatus": "running"})
    assert running.status_code == 200
    assert running.json()["data"]["status"] == "running"

    polled = client.get(f"/backtests/{task_id}")
    assert polled.status_code == 200
    assert polled.json()["data"]["status"] == "running"


def test_get_backtest_returns_403_for_non_owner():
    app, service = _build_app(current_user_id="u-1")
    task = service.create_task(user_id="u-2", strategy_id="s-2", config={"symbol": "MSFT"})

    client = TestClient(app)
    resp = client.get(f"/backtests/{task.id}")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "BACKTEST_ACCESS_DENIED"


def test_get_backtest_returns_envelope_and_camel_case_fields():
    app, service = _build_app(current_user_id="u-1")
    task = service.create_task(user_id="u-1", strategy_id="s-1", config={"symbol": "AAPL"})

    client = TestClient(app)
    resp = client.get(f"/backtests/{task.id}")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    item = payload["data"]
    assert item["userId"] == "u-1"
    assert item["strategyId"] == "s-1"

