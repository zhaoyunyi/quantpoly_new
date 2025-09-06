"""backtest_runner 回测引擎 API 合同测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import JobOrchestrationService

from backtest_runner.api import create_router
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.service import BacktestService


def _build_service(*, prices: list[float], template: str = "moving_average") -> BacktestService:
    def _strategy_reader(*, user_id: str, strategy_id: str):
        return {
            "id": strategy_id,
            "userId": user_id,
            "status": "active",
            "template": template,
            "parameters": {"shortWindow": 3, "longWindow": 5},
        }

    def _market_history_reader(
        *,
        user_id: str,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
        timeframe: str,
        limit: int | None,
    ):
        del user_id, symbol, start_date, end_date, timeframe, limit
        return [{"close": value} for value in prices]

    return BacktestService(
        repository=InMemoryBacktestRepository(),
        strategy_reader=_strategy_reader,
        market_history_reader=_market_history_reader,
    )


def _build_app(*, current_user_id: str, service: BacktestService, job_service: JobOrchestrationService):
    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    app = FastAPI()
    app.include_router(
        create_router(
            service=service,
            get_current_user=_get_current_user,
            job_service=job_service,
        )
    )
    return app


def _build_job_service() -> JobOrchestrationService:
    return JobOrchestrationService(repository=InMemoryJobRepository(), scheduler=InMemoryScheduler())


def test_submit_task_succeeds_and_result_endpoint_returns_structured_payload():
    service = _build_service(
        prices=[10, 10, 10, 10, 10, 11, 12, 13, 12, 11, 10, 9, 8, 9, 10, 11, 12],
    )
    app = _build_app(current_user_id="u-1", service=service, job_service=_build_job_service())
    client = TestClient(app)

    submitted = client.post(
        "/backtests/tasks",
        json={
            "strategyId": "s-1",
            "idempotencyKey": "backtest-engine-happy-path",
            "config": {
                "symbol": "AAPL",
                "startDate": "2024-01-01",
                "endDate": "2024-12-31",
            },
        },
    )

    assert submitted.status_code == 200
    payload = submitted.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "backtest_run"
    assert payload["data"]["status"] == "succeeded"

    task_payload = payload["data"]["backtestTask"]
    assert task_payload["status"] == "completed"
    assert "returnRate" in task_payload["metrics"]

    task_id = task_payload["id"]
    result_resp = client.get(f"/backtests/{task_id}/result")

    assert result_resp.status_code == 200
    result_payload = result_resp.json()
    assert result_payload["success"] is True
    assert result_payload["data"]["taskId"] == task_id
    assert isinstance(result_payload["data"]["equityCurve"], list)
    assert isinstance(result_payload["data"]["trades"], list)


def test_result_endpoint_returns_403_for_non_owner_without_leakage():
    shared_service = _build_service(
        prices=[10, 10, 10, 10, 10, 11, 12, 13, 12, 11, 10, 9, 8, 9, 10, 11, 12],
    )
    shared_job_service = _build_job_service()

    owner_client = TestClient(_build_app(current_user_id="u-1", service=shared_service, job_service=shared_job_service))
    submit_resp = owner_client.post(
        "/backtests/tasks",
        json={
            "strategyId": "s-1",
            "idempotencyKey": "backtest-engine-owner-only",
            "config": {
                "symbol": "AAPL",
                "startDate": "2024-01-01",
                "endDate": "2024-12-31",
            },
        },
    )
    assert submit_resp.status_code == 200
    task_id = submit_resp.json()["data"]["backtestTask"]["id"]

    non_owner_client = TestClient(_build_app(current_user_id="u-2", service=shared_service, job_service=shared_job_service))
    denied = non_owner_client.get(f"/backtests/{task_id}/result")

    assert denied.status_code == 403
    denied_payload = denied.json()
    assert denied_payload["success"] is False
    assert denied_payload["error"]["code"] == "BACKTEST_ACCESS_DENIED"


def test_submit_task_marks_job_failed_when_template_not_supported():
    service = _build_service(prices=[10, 11, 12, 13, 14, 15, 16], template="unsupported_template")
    app = _build_app(current_user_id="u-1", service=service, job_service=_build_job_service())
    client = TestClient(app)

    submitted = client.post(
        "/backtests/tasks",
        json={
            "strategyId": "s-1",
            "idempotencyKey": "backtest-engine-template-invalid",
            "config": {"symbol": "AAPL"},
        },
    )

    assert submitted.status_code == 200
    payload = submitted.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "failed"
    assert payload["data"]["error"]["code"] == "BACKTEST_UNSUPPORTED_TEMPLATE"
    assert payload["data"]["backtestTask"]["status"] == "failed"
