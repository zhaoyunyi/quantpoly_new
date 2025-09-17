"""signal_execution 策略执行查询读模型 API 测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from signal_execution.domain import ExecutionRecord


def _build_app(*, current_user_id: str):
    from signal_execution.api import create_router
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id
            self.is_admin = False

    def _get_current_user():
        return _User(current_user_id)

    repo = InMemorySignalRepository()
    service = SignalExecutionService(
        repository=repo,
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return TestClient(app), repo


def test_api_should_query_templates_by_strategy_type():
    client, _repo = _build_app(current_user_id="u-1")

    resp = client.get("/signals/execution-readmodel/templates", params={"strategyType": "moving_average"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["strategyType"] == "moving_average"


def test_api_should_return_strategy_statistics_and_trend():
    client, repo = _build_app(current_user_id="u-1")
    now = datetime(2026, 2, 11, 10, 0, tzinfo=timezone.utc)

    repo.save_execution(
        ExecutionRecord(
            id="e-1",
            user_id="u-1",
            signal_id="s-1",
            strategy_id="u-1-s1",
            symbol="AAPL",
            status="executed",
            metrics={"pnl": 3.0, "latencyMs": 80},
            created_at=now - timedelta(days=1),
        )
    )
    repo.save_execution(
        ExecutionRecord(
            id="e-2",
            user_id="u-1",
            signal_id="s-2",
            strategy_id="u-1-s1",
            symbol="MSFT",
            status="cancelled",
            metrics={},
            created_at=now - timedelta(days=2),
        )
    )

    stats_resp = client.get("/signals/execution-readmodel/strategies/u-1-s1/statistics")
    trend_resp = client.get(
        "/signals/execution-readmodel/strategies/u-1-s1/trend",
        params={"days": 3},
    )

    assert stats_resp.status_code == 200
    stats_payload = stats_resp.json()["data"]
    assert stats_payload["strategyId"] == "u-1-s1"
    assert stats_payload["totalExecutions"] == 2

    assert trend_resp.status_code == 200
    trend_payload = trend_resp.json()["data"]
    assert len(trend_payload) == 2
    assert sum(item["total"] for item in trend_payload) == 2


def test_api_should_reject_foreign_strategy_readmodel_query():
    client, _repo = _build_app(current_user_id="u-1")

    resp = client.get("/signals/execution-readmodel/strategies/u-2-s1/statistics")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_ACCESS_DENIED"
