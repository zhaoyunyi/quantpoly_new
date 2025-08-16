"""策略更新与回测联动测试。"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from backtest_runner.repository import InMemoryBacktestRepository
    from backtest_runner.service import BacktestService
    from strategy_management.api import create_router
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    strategy_repo = InMemoryStrategyRepository()
    backtest_service = BacktestService(
        repository=InMemoryBacktestRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
    )

    strategy_service = StrategyService(
        repository=strategy_repo,
        count_active_backtests=lambda user_id, strategy_id: backtest_service.count_active_backtests(
            user_id=user_id,
            strategy_id=strategy_id,
        ),
        create_backtest_for_strategy=lambda user_id, strategy_id, config, idempotency_key: backtest_service.create_task(
            user_id=user_id,
            strategy_id=strategy_id,
            config=config,
            idempotency_key=idempotency_key,
        ),
        list_backtests_for_strategy=lambda user_id, strategy_id, status, page, page_size: backtest_service.list_tasks(
            user_id=user_id,
            strategy_id=strategy_id,
            status=status,
            page=page,
            page_size=page_size,
        ),
        stats_backtests_for_strategy=lambda user_id, strategy_id: backtest_service.statistics(
            user_id=user_id,
            strategy_id=strategy_id,
        ),
    )

    app = FastAPI()
    app.include_router(create_router(service=strategy_service, get_current_user=_get_current_user))
    return app, strategy_service


def test_update_strategy_revalidates_template_parameters():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)

    invalid = client.put(
        f"/strategies/{strategy.id}",
        json={"parameters": {"window": 20, "entryZ": 0.5, "exitZ": 1.5}},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "STRATEGY_INVALID_PARAMETERS"

    updated = client.put(
        f"/strategies/{strategy.id}",
        json={
            "name": "mr-updated",
            "parameters": {"window": 30, "entryZ": 1.8, "exitZ": 0.6},
        },
    )
    assert updated.status_code == 200
    payload = updated.json()["data"]
    assert payload["name"] == "mr-updated"
    assert payload["parameters"]["window"] == 30


def test_strategy_backtest_linkage_routes_cover_trigger_list_and_stats():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)

    created = client.post(
        f"/strategies/{strategy.id}/backtests",
        json={"config": {"symbol": "AAPL"}, "idempotencyKey": "s1-b1"},
    )
    assert created.status_code == 200
    task = created.json()["data"]
    assert task["strategyId"] == strategy.id

    listing = client.get(f"/strategies/{strategy.id}/backtests")
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] == 1

    stats = client.get(f"/strategies/{strategy.id}/backtest-stats")
    assert stats.status_code == 200
    assert stats.json()["data"]["totalCount"] == 1


def test_strategy_delete_checks_active_backtests_by_user_scope():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    client.post(
        f"/strategies/{strategy.id}/backtests",
        json={"config": {"symbol": "AAPL"}, "idempotencyKey": "s1-b1"},
    )

    deleting = client.delete(f"/strategies/{strategy.id}")
    assert deleting.status_code == 409
    assert deleting.json()["error"]["code"] == "STRATEGY_IN_USE"


def test_strategy_backtest_linkage_rejects_non_owner():
    app, service = _build_app(current_user_id="u-1")
    strategy = service.create_strategy_from_template(
        user_id="u-2",
        name="foreign",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    client = TestClient(app)
    denied = client.post(
        f"/strategies/{strategy.id}/backtests",
        json={"config": {"symbol": "AAPL"}},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "STRATEGY_ACCESS_DENIED"
