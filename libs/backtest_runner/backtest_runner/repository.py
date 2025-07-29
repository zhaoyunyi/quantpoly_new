"""回测任务仓储实现。"""

from __future__ import annotations

from backtest_runner.domain import BacktestTask


class InMemoryBacktestRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, BacktestTask] = {}

    def save(self, task: BacktestTask) -> None:
        self._tasks[task.id] = task

    def get_by_id(self, task_id: str, *, user_id: str) -> BacktestTask | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        if task.user_id != user_id:
            return None
        return task

    def list_by_user(self, *, user_id: str) -> list[BacktestTask]:
        return [task for task in self._tasks.values() if task.user_id == user_id]
