"""backtest_runner 与 job_orchestration 适配层。"""

from __future__ import annotations

from backtest_runner.domain import BacktestTask
from backtest_runner.service import BacktestIdempotencyConflictError
from job_orchestration.service import IdempotencyConflictError, JobOrchestrationService


class JobOrchestrationBacktestDispatcher:
    """将回测任务提交桥接到 job_orchestration。"""

    def __init__(self, *, job_service: JobOrchestrationService) -> None:
        self._job_service = job_service

    def submit_backtest(self, task: BacktestTask) -> str:
        idempotency_key = task.idempotency_key or f"backtest-task:{task.id}"
        payload = {
            "strategyId": task.strategy_id,
            "backtestTaskId": task.id,
            "config": task.config,
        }

        try:
            job = self._job_service.submit_job(
                user_id=task.user_id,
                task_type="backtest_run",
                payload=payload,
                idempotency_key=idempotency_key,
            )
        except IdempotencyConflictError as exc:
            raise BacktestIdempotencyConflictError("idempotency key already exists") from exc

        return job.id
