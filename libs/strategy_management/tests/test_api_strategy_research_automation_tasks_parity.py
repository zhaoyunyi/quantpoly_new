"""strategy_management 策略研究自动化任务化接口测试（Wave3）。

覆盖变更：update-strategy-signal-automation-parity / 策略研究自动化。
"""

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
    return app, strategy_service, job_service


def test_submit_strategy_performance_analysis_task_returns_task_id():
    app, strategy_service, job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    resp = client.post(
        f"/strategies/{strategy.id}/research/performance-task",
        json={"analysisPeriodDays": 30, "idempotencyKey": "idem-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskId"]
    assert payload["data"]["taskType"] == "strategy_performance_analyze"

    job = job_service.get_job(user_id="u-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.executor_name is not None
    assert job.dispatch_id is not None


def test_submit_strategy_optimization_suggestion_task_returns_task_id():
    app, strategy_service, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    strategy = strategy_service.create_strategy_from_template(
        user_id="u-1",
        name="mr",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )

    resp = client.post(
        f"/strategies/{strategy.id}/research/optimization-task",
        json={"idempotencyKey": "idem-2"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskId"]
    assert payload["data"]["taskType"] == "strategy_optimization_suggest"

