"""backtest_runner 回测管理读模型 API 合同测试。"""

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


def test_rename_backtest_task_updates_display_name():
    app, service = _build_app(current_user_id="u-1")
    task = service.create_task(user_id="u-1", strategy_id="s-1", config={"symbol": "AAPL"})

    client = TestClient(app)
    resp = client.patch(f"/backtests/{task.id}/name", json={"displayName": "MA 回测实验 #1"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["displayName"] == "MA 回测实验 #1"


def test_rename_backtest_task_returns_403_for_non_owner():
    app, service = _build_app(current_user_id="u-1")
    task = service.create_task(user_id="u-2", strategy_id="s-1", config={"symbol": "AAPL"})

    client = TestClient(app)
    resp = client.patch(f"/backtests/{task.id}/name", json={"displayName": "other"})

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "BACKTEST_ACCESS_DENIED"


def test_get_related_backtests_returns_same_strategy_excluding_current_and_supports_status_filter():
    app, service = _build_app(current_user_id="u-1")

    anchor = service.create_task(user_id="u-1", strategy_id="s-anchor", config={"symbol": "AAPL"})
    related_pending = service.create_task(user_id="u-1", strategy_id="s-anchor", config={"symbol": "AAPL"})
    related_completed = service.create_task(user_id="u-1", strategy_id="s-anchor", config={"symbol": "AAPL"})
    service.transition(user_id="u-1", task_id=related_completed.id, to_status="running")
    service.transition(user_id="u-1", task_id=related_completed.id, to_status="completed", metrics={"returnRate": 0.12})

    service.create_task(user_id="u-1", strategy_id="other-strategy", config={"symbol": "AAPL"})
    service.create_task(user_id="u-2", strategy_id="s-anchor", config={"symbol": "AAPL"})

    client = TestClient(app)
    resp = client.get(
        f"/backtests/{anchor.id}/related",
        params={"limit": 10, "status": "completed"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    items = payload["data"]
    assert len(items) == 1
    assert items[0]["id"] == related_completed.id
    assert items[0]["status"] == "completed"
    assert items[0]["strategyId"] == "s-anchor"


