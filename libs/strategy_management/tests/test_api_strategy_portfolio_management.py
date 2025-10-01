"""strategy_management 策略组合管理 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService
    from strategy_management.api import create_router
    from strategy_management.repository import InMemoryStrategyRepository
    from strategy_management.service import StrategyService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    strategy_repo = InMemoryStrategyRepository()
    signal_repo = InMemorySignalRepository()
    signal_service = SignalExecutionService(
        repository=signal_repo,
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    job_service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )
    strategy_service = StrategyService(
        repository=strategy_repo,
        count_active_backtests=lambda _user_id, _strategy_id: 0,
    )

    app = FastAPI()
    app.include_router(
        create_router(
            service=strategy_service,
            get_current_user=_get_current_user,
            job_service=job_service,
            signal_service=signal_service,
        )
    )
    return app, strategy_service


def _create_strategy(service, *, user_id: str, name: str) -> str:
    strategy = service.create_strategy_from_template(
        user_id=user_id,
        name=name,
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )
    return strategy.id


def test_api_should_create_portfolio_and_add_owned_members():
    app, strategy_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    s1 = _create_strategy(strategy_service, user_id="u-1", name="s1")
    s2 = _create_strategy(strategy_service, user_id="u-1", name="s2")

    created = client.post(
        "/portfolios",
        json={"name": "core", "constraints": {"maxTotalWeight": 1.0, "maxSingleWeight": 0.7}},
    )
    assert created.status_code == 200
    portfolio_id = created.json()["data"]["id"]

    add1 = client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": s1, "weight": 0.6})
    assert add1.status_code == 200

    add2 = client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": s2, "weight": 0.4})
    assert add2.status_code == 200

    queried = client.get(f"/portfolios/{portfolio_id}")
    assert queried.status_code == 200
    payload = queried.json()["data"]
    assert payload["id"] == portfolio_id
    assert payload["version"] >= 3
    assert len(payload["members"]) == 2
    assert abs(payload["totalWeight"] - 1.0) < 1e-9


def test_api_should_reject_non_owned_member_strategy():
    app, strategy_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    foreign_strategy = _create_strategy(strategy_service, user_id="u-2", name="foreign")

    created = client.post("/portfolios", json={"name": "acl-test"})
    portfolio_id = created.json()["data"]["id"]

    denied = client.post(
        f"/portfolios/{portfolio_id}/members",
        json={"strategyId": foreign_strategy, "weight": 0.2},
    )

    assert denied.status_code == 403
    payload = denied.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_ACCESS_DENIED"


def test_api_should_reject_invalid_weight_constraints_update():
    app, strategy_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    s1 = _create_strategy(strategy_service, user_id="u-1", name="s1")
    s2 = _create_strategy(strategy_service, user_id="u-1", name="s2")

    created = client.post(
        "/portfolios",
        json={"name": "risk", "constraints": {"maxTotalWeight": 1.0, "maxSingleWeight": 0.6}},
    )
    portfolio_id = created.json()["data"]["id"]

    over_single = client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": s1, "weight": 0.7})
    assert over_single.status_code == 422
    assert over_single.json()["error"]["code"] == "PORTFOLIO_INVALID_WEIGHTS"

    ok = client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": s1, "weight": 0.6})
    assert ok.status_code == 200

    over_total = client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": s2, "weight": 0.5})
    assert over_total.status_code == 422
    assert over_total.json()["error"]["code"] == "PORTFOLIO_INVALID_WEIGHTS"


def test_api_should_submit_portfolio_rebalance_task_with_risk_summary():
    app, strategy_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    s1 = _create_strategy(strategy_service, user_id="u-1", name="s1")
    s2 = _create_strategy(strategy_service, user_id="u-1", name="s2")

    created = client.post("/portfolios", json={"name": "rb"})
    portfolio_id = created.json()["data"]["id"]

    assert client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": s1, "weight": 0.5}).status_code == 200
    assert client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": s2, "weight": 0.5}).status_code == 200

    submitted = client.post(
        f"/portfolios/{portfolio_id}/rebalance-task",
        json={"idempotencyKey": "portfolio-rb-1"},
    )

    assert submitted.status_code == 200
    data = submitted.json()["data"]
    assert data["taskId"]
    assert data["taskType"] == "portfolio_rebalance"
    result = data["result"]
    assert result["portfolioId"] == portfolio_id
    assert result["riskSummary"]
    assert len(result["adjustments"]) >= 1


def test_api_should_query_portfolio_read_model():
    app, strategy_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    s1 = _create_strategy(strategy_service, user_id="u-1", name="s1")

    created = client.post("/portfolios", json={"name": "read-model"})
    portfolio_id = created.json()["data"]["id"]
    assert client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": s1, "weight": 1.0}).status_code == 200

    queried = client.get(f"/portfolios/{portfolio_id}/read-model")

    assert queried.status_code == 200
    payload = queried.json()["data"]
    assert payload["portfolioId"] == portfolio_id
    assert "performanceSummary" in payload
    assert "correlationSummary" in payload


def test_api_should_isolate_portfolio_access_between_users():
    owner_app, owner_service = _build_app(current_user_id="u-1")
    owner_client = TestClient(owner_app)

    owner_strategy = _create_strategy(owner_service, user_id="u-1", name="owner")

    created = owner_client.post("/portfolios", json={"name": "owner-only"})
    portfolio_id = created.json()["data"]["id"]
    assert owner_client.post(f"/portfolios/{portfolio_id}/members", json={"strategyId": owner_strategy, "weight": 1.0}).status_code == 200

    outsider_app, _ = _build_app(current_user_id="u-2")
    outsider_client = TestClient(outsider_app)

    denied = outsider_client.get(f"/portfolios/{portfolio_id}")

    assert denied.status_code == 403
    payload = denied.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "PORTFOLIO_ACCESS_DENIED"
