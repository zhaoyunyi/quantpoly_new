"""回测与策略联动、删除闭环测试。"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_create_task_rejects_non_owner_strategy():
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestAccessDeniedError, BacktestService

    service = BacktestService(
        repository=InMemoryBacktestRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
    )

    with pytest.raises(BacktestAccessDeniedError):
        service.create_task(
            user_id="u-1",
            strategy_id="u-2-strategy",
            config={"symbol": "AAPL"},
        )


def test_delete_task_requires_terminal_status():
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestDeleteInvalidStateError, BacktestService

    service = BacktestService(repository=InMemoryBacktestRepository())

    task = service.create_task(
        user_id="u-1",
        strategy_id="u-1-strategy",
        config={"symbol": "AAPL"},
    )

    with pytest.raises(BacktestDeleteInvalidStateError):
        service.delete_task(user_id="u-1", task_id=task.id)

    service.transition(user_id="u-1", task_id=task.id, to_status="running")
    with pytest.raises(BacktestDeleteInvalidStateError):
        service.delete_task(user_id="u-1", task_id=task.id)

    service.transition(
        user_id="u-1",
        task_id=task.id,
        to_status="completed",
        metrics={"returnRate": 0.1},
    )
    deleted = service.delete_task(user_id="u-1", task_id=task.id)
    assert deleted is True


def test_backtest_api_create_denies_foreign_strategy_and_delete_respects_state_machine():
    from backtest_runner.api import create_router
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User("u-1")

    service = BacktestService(
        repository=InMemoryBacktestRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
    )
    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    client = TestClient(app)

    denied = client.post(
        "/backtests",
        json={"strategyId": "u-2-strategy", "config": {"symbol": "AAPL"}},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "BACKTEST_ACCESS_DENIED"

    created = client.post(
        "/backtests",
        json={"strategyId": "u-1-strategy", "config": {"symbol": "AAPL"}},
    )
    assert created.status_code == 200
    task_id = created.json()["data"]["id"]

    deleting_pending = client.delete(f"/backtests/{task_id}")
    assert deleting_pending.status_code == 409
    assert deleting_pending.json()["error"]["code"] == "BACKTEST_DELETE_INVALID_STATE"

    transitioned = client.post(
        f"/backtests/{task_id}/transition",
        json={"toStatus": "running"},
    )
    assert transitioned.status_code == 200
    completed = client.post(
        f"/backtests/{task_id}/transition",
        json={"toStatus": "completed", "metrics": {"returnRate": 0.12}},
    )
    assert completed.status_code == 200

    deleting_completed = client.delete(f"/backtests/{task_id}")
    assert deleting_completed.status_code == 200
    assert deleting_completed.json()["data"]["deleted"] is True
