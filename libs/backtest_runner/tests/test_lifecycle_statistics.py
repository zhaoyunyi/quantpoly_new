"""回测生命周期、统计与对比测试。"""

from __future__ import annotations

import pytest

from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.service import BacktestIdempotencyConflictError, BacktestService


def _service() -> BacktestService:
    return BacktestService(repository=InMemoryBacktestRepository())


def test_list_tasks_supports_pagination_and_status_filter():
    service = _service()

    created = [
        service.create_task(user_id="u-1", strategy_id=f"s-{idx}", config={}, idempotency_key=f"k-{idx}")
        for idx in range(4)
    ]
    service.transition(user_id="u-1", task_id=created[0].id, to_status="running")

    filtered = service.list_tasks(user_id="u-1", status="pending", page=1, page_size=2)
    assert filtered["total"] == 3
    assert len(filtered["items"]) == 2


def test_statistics_and_compare_completed_tasks():
    service = _service()

    t1 = service.create_task(user_id="u-1", strategy_id="s-1", config={}, idempotency_key="k-1")
    t2 = service.create_task(user_id="u-1", strategy_id="s-2", config={}, idempotency_key="k-2")

    service.transition(user_id="u-1", task_id=t1.id, to_status="running")
    service.transition(
        user_id="u-1",
        task_id=t1.id,
        to_status="completed",
        metrics={"returnRate": 0.12, "maxDrawdown": 0.05, "winRate": 0.6},
    )
    service.transition(user_id="u-1", task_id=t2.id, to_status="running")
    service.transition(
        user_id="u-1",
        task_id=t2.id,
        to_status="completed",
        metrics={"returnRate": 0.08, "maxDrawdown": 0.03, "winRate": 0.55},
    )

    stats = service.statistics(user_id="u-1")
    assert stats["completedCount"] == 2
    assert stats["averageReturnRate"] == pytest.approx(0.10)

    compared = service.compare_tasks(user_id="u-1", task_ids=[t1.id, t2.id])
    assert len(compared["tasks"]) == 2
    assert compared["summary"]["bestReturnRate"] == pytest.approx(0.12)


def test_cancel_and_retry_task_lifecycle():
    service = _service()
    task = service.create_task(user_id="u-1", strategy_id="s-1", config={}, idempotency_key="k-1")

    service.transition(user_id="u-1", task_id=task.id, to_status="running")
    cancelled = service.cancel_task(user_id="u-1", task_id=task.id)
    assert cancelled is not None
    assert cancelled.status == "cancelled"

    retried = service.retry_task(user_id="u-1", task_id=task.id)
    assert retried is not None
    assert retried.status == "pending"


def test_idempotency_conflict_is_reported():
    service = _service()

    service.create_task(user_id="u-1", strategy_id="s-1", config={}, idempotency_key="dup")
    with pytest.raises(BacktestIdempotencyConflictError):
        service.create_task(user_id="u-1", strategy_id="s-1", config={}, idempotency_key="dup")
