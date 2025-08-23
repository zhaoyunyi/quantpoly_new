"""job_orchestration 领域任务编排 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


class _User:
    def __init__(self, user_id: str):
        self.id = user_id


def _build_app(*, current_user_id: str):
    from job_orchestration.api import create_router
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService

    def _get_current_user():
        return _User(current_user_id)

    service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_submit_and_poll_job_for_domain_task_type():
    app, _service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    submitted = client.post(
        "/jobs",
        json={
            "taskType": "signal_batch_execute",
            "payload": {"signalIds": ["s-1", "s-2"]},
            "idempotencyKey": "job-k-1",
        },
    )

    assert submitted.status_code == 200
    payload = submitted.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "signal_batch_execute"
    assert payload["data"]["status"] == "queued"

    job_id = payload["data"]["id"]
    polled = client.get(f"/jobs/{job_id}")

    assert polled.status_code == 200
    polled_payload = polled.json()
    assert polled_payload["success"] is True
    assert polled_payload["data"]["id"] == job_id


def test_list_jobs_supports_status_and_task_type_filters():
    app, _service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    first = client.post(
        "/jobs",
        json={
            "taskType": "backtest_run",
            "payload": {"strategyId": "s-1"},
            "idempotencyKey": "job-k-2",
        },
    )
    assert first.status_code == 200
    first_id = first.json()["data"]["id"]

    second = client.post(
        "/jobs",
        json={
            "taskType": "trading_refresh_prices",
            "payload": {"priceUpdates": {"AAPL": 130}},
            "idempotencyKey": "job-k-3",
        },
    )
    assert second.status_code == 200

    transition = client.post(f"/jobs/{first_id}/transition", json={"toStatus": "running"})
    assert transition.status_code == 200

    by_type = client.get("/jobs", params={"taskType": "trading_refresh_prices"})
    assert by_type.status_code == 200
    assert len(by_type.json()["data"]) == 1
    assert by_type.json()["data"][0]["taskType"] == "trading_refresh_prices"

    by_status = client.get("/jobs", params={"status": "running"})
    assert by_status.status_code == 200
    assert len(by_status.json()["data"]) == 1
    assert by_status.json()["data"][0]["id"] == first_id


def test_foreign_user_cannot_read_or_transition_job():
    app_owner, service = _build_app(current_user_id="u-1")
    client_owner = TestClient(app_owner)

    submitted = client_owner.post(
        "/jobs",
        json={
            "taskType": "risk_account_evaluate",
            "payload": {"accountId": "u-1-account"},
            "idempotencyKey": "job-k-4",
        },
    )
    assert submitted.status_code == 200
    job_id = submitted.json()["data"]["id"]

    from job_orchestration.api import create_router

    def _foreign_user():
        return _User("u-2")

    app_foreign = FastAPI()
    app_foreign.include_router(create_router(service=service, get_current_user=_foreign_user))
    client_foreign = TestClient(app_foreign)

    read_resp = client_foreign.get(f"/jobs/{job_id}")
    assert read_resp.status_code == 403
    assert read_resp.json()["error"]["code"] == "JOB_ACCESS_DENIED"

    transition_resp = client_foreign.post(f"/jobs/{job_id}/transition", json={"toStatus": "running"})
    assert transition_resp.status_code == 403
    assert transition_resp.json()["error"]["code"] == "JOB_ACCESS_DENIED"


def test_task_types_endpoint_returns_registry_metadata():
    app, _service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    response = client.get("/jobs/task-types")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True

    rows = payload["data"]
    strategy_item = next(item for item in rows if item["taskType"] == "strategy_batch_execute")
    assert strategy_item["domain"] == "strategy"
    assert strategy_item["schedulable"] is True
    assert "strategy.batch_execute_strategies" in strategy_item["legacyNames"]


def test_schedule_query_and_stop_are_isolated_by_user_namespace():
    app_owner, service = _build_app(current_user_id="u-1")
    client_owner = TestClient(app_owner)

    created = client_owner.post(
        "/jobs/schedules/interval",
        json={
            "taskType": "market_data_sync",
            "everySeconds": 60,
        },
    )

    assert created.status_code == 200
    payload = created.json()
    schedule_id = payload["data"]["id"]

    assert payload["data"]["namespace"] == "user:u-1"
    assert payload["data"]["status"] == "active"
    assert payload["data"]["createdAt"]

    fetched = client_owner.get(f"/jobs/schedules/{schedule_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == schedule_id

    from job_orchestration.api import create_router

    def _foreign_user():
        return _User("u-2")

    app_foreign = FastAPI()
    app_foreign.include_router(create_router(service=service, get_current_user=_foreign_user))
    client_foreign = TestClient(app_foreign)

    foreign_read = client_foreign.get(f"/jobs/schedules/{schedule_id}")
    assert foreign_read.status_code == 403
    assert foreign_read.json()["error"]["code"] == "SCHEDULE_ACCESS_DENIED"

    foreign_stop = client_foreign.post(f"/jobs/schedules/{schedule_id}/stop")
    assert foreign_stop.status_code == 403
    assert foreign_stop.json()["error"]["code"] == "SCHEDULE_ACCESS_DENIED"

    stopped = client_owner.post(f"/jobs/schedules/{schedule_id}/stop")
    assert stopped.status_code == 200
    assert stopped.json()["data"]["status"] == "stopped"
