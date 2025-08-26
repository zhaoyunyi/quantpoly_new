"""signal_execution 策略维度绩效统计接口测试（Wave3）。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


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

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_strategy_performance_stats_endpoint_aggregates_by_strategy():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy-1",
        account_id="u-1-account-1",
        symbol="AAPL",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=s1.id, execution_metrics={"pnl": 1.0})

    s2 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy-2",
        account_id="u-1-account-1",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=s2.id, execution_metrics={"pnl": 2.0})

    foreign = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy-1",
        account_id="u-2-account-1",
        symbol="TSLA",
        side="BUY",
    )
    service.execute_signal(user_id="u-2", signal_id=foreign.id, execution_metrics={"pnl": 99.0})

    resp = client.get("/signals/executions/performance/by-strategy")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    items = payload["data"]
    assert len(items) == 2
    assert {item["strategyId"] for item in items} == {"u-1-strategy-1", "u-1-strategy-2"}
    assert sum(item["totalExecutions"] for item in items) == 2

