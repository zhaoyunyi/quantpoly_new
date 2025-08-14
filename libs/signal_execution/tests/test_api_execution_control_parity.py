"""signal_execution 执行控制面 API 测试。"""

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

    def _validate_parameters(_user_id: str, _strategy_id: str, parameters: dict) -> None:
        if "window" not in parameters:
            raise ValueError("missing parameter: window")

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
        strategy_parameter_validator=_validate_parameters,
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_validate_parameters_failure_returns_422_and_does_not_create_execution():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    resp = client.post(
        "/signals/validate-parameters",
        json={
            "strategyId": "u-1-strategy",
            "accountId": "u-1-account",
            "parameters": {"entryZ": 1.5},
        },
    )

    assert resp.status_code == 422
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_INVALID_PARAMETERS"
    assert service.list_executions(user_id="u-1") == []


def test_create_signal_rejects_invalid_parameters_and_keeps_records_empty():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    resp = client.post(
        "/signals",
        json={
            "strategyId": "u-1-strategy",
            "accountId": "u-1-account",
            "symbol": "AAPL",
            "side": "BUY",
            "parameters": {"entryZ": 1.5},
        },
    )

    assert resp.status_code == 422
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_INVALID_PARAMETERS"
    assert service.list_signals(user_id="u-1") == []
    assert service.list_executions(user_id="u-1") == []


def test_execution_detail_and_running_endpoints_are_user_scoped():
    app, service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    pending = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    done = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=done.id)
    my_execution = service.list_executions(user_id="u-1")[0]

    foreign_signal = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy",
        account_id="u-2-account",
        symbol="TSLA",
        side="BUY",
    )
    service.execute_signal(user_id="u-2", signal_id=foreign_signal.id)
    foreign_execution = service.list_executions(user_id="u-2")[0]

    detail = client.get(f"/signals/executions/{my_execution.id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == my_execution.id

    denied = client.get(f"/signals/executions/{foreign_execution.id}")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "SIGNAL_ACCESS_DENIED"

    running = client.get("/signals/executions/running")
    assert running.status_code == 200
    running_items = running.json()["data"]
    assert len(running_items) == 1
    assert running_items[0]["signalId"] == pending.id
    assert running_items[0]["status"] == "pending"
    assert "updatedAt" in running_items[0]

