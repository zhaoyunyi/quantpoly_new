"""回测扩展 API 测试。"""

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


def test_list_statistics_compare_and_retry_endpoints():
    app, _ = _build_app(current_user_id="u-1")
    client = TestClient(app)

    t1 = client.post(
        "/backtests",
        json={"strategyId": "s-1", "config": {}, "idempotencyKey": "k-1"},
    ).json()["data"]
    t2 = client.post(
        "/backtests",
        json={"strategyId": "s-2", "config": {}, "idempotencyKey": "k-2"},
    ).json()["data"]

    client.post(f"/backtests/{t1['id']}/transition", json={"toStatus": "running"})
    client.post(
        f"/backtests/{t1['id']}/transition",
        json={"toStatus": "completed", "metrics": {"returnRate": 0.1, "maxDrawdown": 0.04, "winRate": 0.5}},
    )

    listing = client.get("/backtests", params={"status": "pending", "page": 1, "pageSize": 10})
    assert listing.status_code == 200
    assert listing.json()["success"] is True

    stats = client.get("/backtests/statistics")
    assert stats.status_code == 200
    assert stats.json()["data"]["completedCount"] == 1

    compare = client.post("/backtests/compare", json={"taskIds": [t1["id"], t2["id"]]})
    assert compare.status_code == 200
    assert len(compare.json()["data"]["tasks"]) == 2

    client.post(f"/backtests/{t2['id']}/transition", json={"toStatus": "running"})
    cancelled = client.post(f"/backtests/{t2['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"

    retried = client.post(f"/backtests/{t2['id']}/retry")
    assert retried.status_code == 200
    assert retried.json()["data"]["status"] == "pending"


def test_create_backtest_idempotency_conflict_returns_409():
    app, _ = _build_app(current_user_id="u-1")
    client = TestClient(app)

    first = client.post(
        "/backtests",
        json={"strategyId": "s-1", "config": {}, "idempotencyKey": "dup-key"},
    )
    assert first.status_code == 200

    second = client.post(
        "/backtests",
        json={"strategyId": "s-1", "config": {}, "idempotencyKey": "dup-key"},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "BACKTEST_IDEMPOTENCY_CONFLICT"
