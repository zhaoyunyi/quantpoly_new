"""signal_execution 批处理与维护 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str, is_admin: bool = False):
    from signal_execution.api import create_router
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    class _User:
        def __init__(self, user_id: str, admin: bool):
            self.id = user_id
            self.is_admin = admin

    def _get_current_user():
        return _User(current_user_id, is_admin)

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_batch_execute_endpoint_supports_idempotency_and_conflict():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-s1",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    s2 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-s1",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )

    first = client.post(
        "/signals/batch/execute",
        json={"signalIds": [s1.id, s2.id], "idempotencyKey": "idem-1"},
    )
    assert first.status_code == 200
    assert first.json()["data"]["executed"] == 2

    second = client.post(
        "/signals/batch/execute",
        json={"signalIds": [s1.id], "idempotencyKey": "idem-1"},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_execution_history_and_performance_endpoints():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-s1",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    service.execute_signal(
        user_id="u-1",
        signal_id=s1.id,
        execution_metrics={"pnl": 12.3, "latencyMs": 80},
    )

    history = client.get("/signals/executions")
    assert history.status_code == 200
    assert len(history.json()["data"]) == 1

    perf = client.get("/signals/executions/performance")
    assert perf.status_code == 200
    assert perf.json()["data"]["totalExecutions"] == 1
