"""回测任务服务。"""

from __future__ import annotations

from backtest_runner.domain import BacktestTask
from backtest_runner.repository import InMemoryBacktestRepository


class BacktestService:
    def __init__(self, *, repository: InMemoryBacktestRepository) -> None:
        self._repository = repository

    def create_task(self, *, user_id: str, strategy_id: str, config: dict) -> BacktestTask:
        task = BacktestTask.create(user_id=user_id, strategy_id=strategy_id, config=config)
        self._repository.save(task)
        return task

    def get_task(self, *, user_id: str, task_id: str) -> BacktestTask | None:
        return self._repository.get_by_id(task_id, user_id=user_id)

    def list_tasks(self, *, user_id: str) -> list[BacktestTask]:
        return self._repository.list_by_user(user_id=user_id)

    def transition(self, *, user_id: str, task_id: str, to_status: str) -> BacktestTask | None:
        task = self._repository.get_by_id(task_id, user_id=user_id)
        if task is None:
            return None
        task.transition_to(to_status)
        self._repository.save(task)
        return task
