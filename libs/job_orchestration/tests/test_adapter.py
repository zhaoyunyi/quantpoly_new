"""job_orchestration 适配器测试。"""

from __future__ import annotations


def test_celery_adapter_dispatch_contract():
    from job_orchestration.celery_adapter import CeleryJobAdapter

    calls: list[tuple[str, dict]] = []

    def _dispatch(task_type: str, payload: dict):
        calls.append((task_type, payload))
        return "task-123"

    adapter = CeleryJobAdapter(dispatcher=_dispatch)

    task_id = adapter.dispatch(task_type="backtest_run", payload={"strategyId": "s-1"})

    assert task_id == "task-123"
    assert calls == [("backtest_run", {"strategyId": "s-1"})]


def test_scheduler_supports_interval_and_cron_registration():
    from job_orchestration.scheduler import InMemoryScheduler

    scheduler = InMemoryScheduler()
    scheduler.register_interval(job_type="market_data_sync", every_seconds=60)
    scheduler.register_cron(job_type="backtest_run", cron_expr="*/5 * * * *")
    scheduler.start()

    items = scheduler.list_schedules()
    assert len(items) == 2
    assert scheduler.running is True

    scheduler.stop()
    assert scheduler.running is False

