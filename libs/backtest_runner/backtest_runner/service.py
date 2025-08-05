"""回测任务服务。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from backtest_runner.domain import BacktestTask
from backtest_runner.repository import InMemoryBacktestRepository


class BacktestIdempotencyConflictError(RuntimeError):
    """回测任务幂等键冲突。"""


class BacktestAccessDeniedError(PermissionError):
    """无权访问回测任务。"""


class BacktestDispatchError(RuntimeError):
    """回测任务提交到编排系统失败。"""


class BacktestDispatcher(Protocol):
    def submit_backtest(self, task: BacktestTask) -> str:
        """向编排系统提交回测任务并返回 job_id。"""


class BacktestService:
    def __init__(
        self,
        *,
        repository: InMemoryBacktestRepository,
        on_task_created: Callable[[BacktestTask], None] | None = None,
        dispatcher: BacktestDispatcher | None = None,
    ) -> None:
        self._repository = repository
        self._on_task_created = on_task_created
        self._dispatcher = dispatcher

    def create_task(
        self,
        *,
        user_id: str,
        strategy_id: str,
        config: dict,
        idempotency_key: str | None = None,
    ) -> BacktestTask:
        if idempotency_key:
            existing = self._repository.find_by_idempotency_key(
                user_id=user_id,
                idempotency_key=idempotency_key,
            )
            if existing is not None:
                raise BacktestIdempotencyConflictError("idempotency key already exists")

        task = BacktestTask.create(
            user_id=user_id,
            strategy_id=strategy_id,
            config=config,
            idempotency_key=idempotency_key,
        )

        created = self._repository.save_if_absent(task)
        if not created:
            raise BacktestIdempotencyConflictError("idempotency key already exists")

        try:
            if self._dispatcher:
                self._dispatcher.submit_backtest(task)

            if self._on_task_created:
                self._on_task_created(task)
        except BacktestIdempotencyConflictError:
            self._repository.delete(user_id=user_id, task_id=task.id)
            raise
        except Exception as exc:
            self._repository.delete(user_id=user_id, task_id=task.id)
            raise BacktestDispatchError("failed to dispatch backtest task") from exc

        return task

    def get_task(self, *, user_id: str, task_id: str) -> BacktestTask | None:
        return self._repository.get_by_id(task_id, user_id=user_id)

    def list_tasks(
        self,
        *,
        user_id: str,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        all_items = self._repository.list_by_user(user_id=user_id, status=status)
        total = len(all_items)
        start = max(page - 1, 0) * page_size
        end = start + page_size
        return {
            "items": all_items[start:end],
            "total": total,
            "page": page,
            "pageSize": page_size,
        }

    def transition(
        self,
        *,
        user_id: str,
        task_id: str,
        to_status: str,
        metrics: dict[str, float] | None = None,
    ) -> BacktestTask | None:
        task = self._repository.get_by_id(task_id, user_id=user_id)
        if task is None:
            return None
        task.transition_to(to_status, metrics=metrics)
        self._repository.save(task)
        return task

    def cancel_task(self, *, user_id: str, task_id: str) -> BacktestTask | None:
        return self.transition(user_id=user_id, task_id=task_id, to_status="cancelled")

    def retry_task(self, *, user_id: str, task_id: str) -> BacktestTask | None:
        return self.transition(user_id=user_id, task_id=task_id, to_status="pending")

    def statistics(self, *, user_id: str) -> dict:
        all_items = self._repository.list_by_user(user_id=user_id, status=None)
        counters = {
            "pendingCount": 0,
            "runningCount": 0,
            "completedCount": 0,
            "failedCount": 0,
            "cancelledCount": 0,
        }
        completed_returns: list[float] = []
        completed_drawdowns: list[float] = []
        completed_win_rates: list[float] = []

        for task in all_items:
            key = f"{task.status}Count"
            if key in counters:
                counters[key] += 1
            if task.status == "completed" and task.metrics:
                if "returnRate" in task.metrics:
                    completed_returns.append(float(task.metrics["returnRate"]))
                if "maxDrawdown" in task.metrics:
                    completed_drawdowns.append(float(task.metrics["maxDrawdown"]))
                if "winRate" in task.metrics:
                    completed_win_rates.append(float(task.metrics["winRate"]))

        def _avg(values: list[float]) -> float:
            if not values:
                return 0.0
            return sum(values) / len(values)

        return {
            **counters,
            "totalCount": len(all_items),
            "averageReturnRate": _avg(completed_returns),
            "averageMaxDrawdown": _avg(completed_drawdowns),
            "averageWinRate": _avg(completed_win_rates),
        }

    def compare_tasks(self, *, user_id: str, task_ids: list[str]) -> dict:
        tasks: list[dict] = []
        return_rates: list[float] = []

        for task_id in task_ids:
            task = self._repository.get_by_id(task_id, user_id=user_id)
            if task is None:
                raise BacktestAccessDeniedError("backtest task does not belong to current user")
            metrics = task.metrics or {}
            if "returnRate" in metrics:
                return_rates.append(float(metrics["returnRate"]))
            tasks.append(
                {
                    "taskId": task.id,
                    "strategyId": task.strategy_id,
                    "status": task.status,
                    "metrics": metrics,
                }
            )

        return {
            "tasks": tasks,
            "summary": {
                "bestReturnRate": max(return_rates) if return_rates else 0.0,
                "worstReturnRate": min(return_rates) if return_rates else 0.0,
            },
        }
