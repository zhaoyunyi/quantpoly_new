"""回测任务仓储实现。"""

from __future__ import annotations

import copy
import threading

from backtest_runner.domain import BacktestTask


class InMemoryBacktestRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, BacktestTask] = {}
        self._idempotency: dict[tuple[str, str], str] = {}
        self._lock = threading.RLock()

    def _clone(self, task: BacktestTask) -> BacktestTask:
        return BacktestTask(
            id=task.id,
            user_id=task.user_id,
            strategy_id=task.strategy_id,
            config=copy.deepcopy(task.config),
            idempotency_key=task.idempotency_key,
            status=task.status,
            metrics=copy.deepcopy(task.metrics),
            display_name=task.display_name,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def save(self, task: BacktestTask) -> None:
        with self._lock:
            stored = self._clone(task)
            self._tasks[stored.id] = stored
            if stored.idempotency_key:
                self._idempotency[(stored.user_id, stored.idempotency_key)] = stored.id

    def save_if_absent(self, task: BacktestTask) -> bool:
        with self._lock:
            if task.idempotency_key is not None:
                key = (task.user_id, task.idempotency_key)
                if key in self._idempotency:
                    return False
            self.save(task)
            return True

    def delete(self, *, user_id: str, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.user_id != user_id:
                return False
            del self._tasks[task_id]
            if task.idempotency_key is not None:
                self._idempotency.pop((task.user_id, task.idempotency_key), None)
            return True

    def find_by_idempotency_key(self, *, user_id: str, idempotency_key: str) -> BacktestTask | None:
        with self._lock:
            task_id = self._idempotency.get((user_id, idempotency_key))
            if task_id is None:
                return None
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return self._clone(task)

    def get_by_id(self, task_id: str, *, user_id: str) -> BacktestTask | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            if task.user_id != user_id:
                return None
            return self._clone(task)

    def list_by_user(
        self,
        *,
        user_id: str,
        strategy_id: str | None = None,
        status: str | None = None,
    ) -> list[BacktestTask]:
        with self._lock:
            return [
                self._clone(task)
                for task in sorted(self._tasks.values(), key=lambda item: item.created_at)
                if task.user_id == user_id
                and (strategy_id is None or task.strategy_id == strategy_id)
                and (status is None or task.status == status)
            ]

    def list_related_by_strategy(
        self,
        *,
        user_id: str,
        strategy_id: str,
        exclude_task_id: str,
        status: str | None = None,
        limit: int = 10,
    ) -> list[BacktestTask]:
        normalized_limit = max(1, limit)
        with self._lock:
            items = [
                self._clone(task)
                for task in sorted(self._tasks.values(), key=lambda item: item.created_at)
                if task.user_id == user_id
                and task.strategy_id == strategy_id
                and task.id != exclude_task_id
                and (status is None or task.status == status)
            ]
        return items[:normalized_limit]
