"""strategy_management 策略研究优化深度接口测试。"""

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
        count_active_backtests=lambda user_id, strategy_id: 0,
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
    return app, strategy_service, job_service


def _valid_request(*, idem: str, method: str = "grid", budget: dict | None = None) -> dict:
    payload = {
        "idempotencyKey": idem,
        "method": method,
        "objective": {
            "metric": "averagePnl",
            "direction": "maximize",
        },
        "parameterSpace": {
            "window": {"min": 10, "max": 40, "step": 5},
            "entryZ": {"min": 1.0, "max": 2.5, "step": 0.1},
        },
        "constraints": {
            "maxDrawdown": 0.2,
        },
    }
    if budget is not None:
        payload["budget"] = budget
    return payload


def test_submit_strategy_optimization_task_rejects_invalid_parameter_space():
    app, strategy_service, job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    resp = client.post(
        f"/strategies/{strategy.id}/research/optimization-task",
        json={
            "idempotencyKey": "idem-invalid",
            "method": "grid",
            "objective": {"metric": "averagePnl", "direction": "maximize"},
            "parameterSpace": {
                "window": {"min": 40, "max": 10, "step": 5},
            },
        },
    )

    assert resp.status_code == 422
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "RESEARCH_INVALID_PARAMETER_SPACE"
    assert job_service.list_jobs(user_id="u-1") == []


def test_submit_strategy_optimization_task_persists_and_query_results():
    app, strategy_service, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    submitted = client.post(
        f"/strategies/{strategy.id}/research/optimization-task",
        json=_valid_request(idem="idem-persist"),
    )
    assert submitted.status_code == 200
    task_id = submitted.json()["data"]["taskId"]

    queried = client.get(
        f"/strategies/{strategy.id}/research/results",
        params={"status": "succeeded"},
    )

    assert queried.status_code == 200
    payload = queried.json()
    assert payload["success"] is True
    assert payload["data"]["total"] >= 1

    first = payload["data"]["items"][0]
    assert first["taskId"] == task_id
    assert first["status"] == "succeeded"
    assert first["method"] == "grid"
    assert first["optimizationResult"]["objective"]["metric"] == "averagePnl"


def test_submit_strategy_optimization_task_returns_grid_trials_and_budget_usage():
    app, strategy_service, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="mr-grid",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.6, "exitZ": 0.6},
    )

    submitted = client.post(
        f"/strategies/{strategy.id}/research/optimization-task",
        json=_valid_request(
            idem="idem-grid-budget",
            method="grid",
            budget={"maxTrials": 3, "maxDurationSeconds": 60},
        ),
    )

    assert submitted.status_code == 200
    payload = submitted.json()["data"]
    optimization_result = payload["result"]["optimizationResult"]

    assert optimization_result["method"] == "grid"
    assert optimization_result["budget"]["maxTrials"] == 3
    assert 1 <= len(optimization_result["trials"]) <= 3
    assert optimization_result["budgetUsage"]["usedTrials"] == len(optimization_result["trials"])
    assert optimization_result["bestCandidate"]["trialId"]
    assert optimization_result["convergence"]["earlyStopReason"] in {
        "max_trials_reached",
        "max_duration_reached",
        "parameter_space_exhausted",
        "early_stop_score_reached",
    }


def test_submit_strategy_optimization_task_supports_bayesian_method():
    app, strategy_service, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="mr-bayes",
        template_id="mean_reversion",
        parameters={"window": 24, "entryZ": 1.7, "exitZ": 0.6},
    )

    submitted = client.post(
        f"/strategies/{strategy.id}/research/optimization-task",
        json=_valid_request(
            idem="idem-bayes",
            method="bayesian",
            budget={"maxTrials": 4, "maxDurationSeconds": 60},
        ),
    )

    assert submitted.status_code == 200
    optimization_result = submitted.json()["data"]["result"]["optimizationResult"]

    assert optimization_result["method"] == "bayesian"
    assert 1 <= len(optimization_result["trials"]) <= 4
    assert optimization_result["bestCandidate"]["score"] >= optimization_result["score"]


def test_research_results_query_supports_failed_and_cancelled_statuses():
    app, strategy_service, job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    failed = job_service.submit_job(
        user_id="u-1",
        task_type="strategy_optimization_suggest",
        payload={"strategyId": strategy.id, "method": "grid"},
        idempotency_key="idem-failed",
    )
    job_service.start_job(user_id="u-1", job_id=failed.id)
    job_service.fail_job(
        user_id="u-1",
        job_id=failed.id,
        error_code="RESEARCH_FAILED",
        error_message="boom",
    )

    cancelled = job_service.submit_job(
        user_id="u-1",
        task_type="strategy_optimization_suggest",
        payload={"strategyId": strategy.id, "method": "grid"},
        idempotency_key="idem-cancelled",
    )
    job_service.cancel_job(user_id="u-1", job_id=cancelled.id)

    failed_resp = client.get(
        f"/strategies/{strategy.id}/research/results",
        params={"status": "failed"},
    )
    assert failed_resp.status_code == 200
    failed_items = failed_resp.json()["data"]["items"]
    assert len(failed_items) == 1
    assert failed_items[0]["status"] == "failed"

    cancelled_resp = client.get(
        f"/strategies/{strategy.id}/research/results",
        params={"status": "cancelled"},
    )
    assert cancelled_resp.status_code == 200
    cancelled_items = cancelled_resp.json()["data"]["items"]
    assert len(cancelled_items) == 1
    assert cancelled_items[0]["status"] == "cancelled"


def test_research_results_query_supports_method_and_version_filters():
    app, strategy_service, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="mr-filter",
        template_id="mean_reversion",
        parameters={"window": 28, "entryZ": 1.8, "exitZ": 0.7},
    )

    resp_grid = client.post(
        f"/strategies/{strategy.id}/research/optimization-task",
        json=_valid_request(idem="idem-filter-grid", method="grid", budget={"maxTrials": 2}),
    )
    assert resp_grid.status_code == 200

    resp_bayes = client.post(
        f"/strategies/{strategy.id}/research/optimization-task",
        json=_valid_request(idem="idem-filter-bayes", method="bayesian", budget={"maxTrials": 3}),
    )
    assert resp_bayes.status_code == 200

    queried = client.get(
        f"/strategies/{strategy.id}/research/results",
        params={
            "status": "succeeded",
            "method": "bayesian",
            "version": "v3",
        },
    )

    assert queried.status_code == 200
    payload = queried.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 1
    item = payload["data"]["items"][0]
    assert item["method"] == "bayesian"
    assert item["optimizationResult"]["version"] == "v3"


def test_non_owner_cannot_query_strategy_research_results():
    app, strategy_service, _job_service = _build_app(current_user_id="u-2")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="foreign",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    resp = client.get(f"/strategies/{strategy.id}/research/results")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_ACCESS_DENIED"
