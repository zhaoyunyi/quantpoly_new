"""job_orchestration 调度抽象（in-memory）。"""

from __future__ import annotations

from job_orchestration.domain import ScheduleConfig


class InMemoryScheduler:
    def __init__(self) -> None:
        self._schedules: list[ScheduleConfig] = []
        self.running = False

    def register_interval(
        self,
        *,
        job_type: str,
        every_seconds: int,
        user_id: str = "system",
        namespace: str = "system",
    ) -> ScheduleConfig:
        schedule = ScheduleConfig.create(
            user_id=user_id,
            namespace=namespace,
            job_type=job_type,
            schedule_type="interval",
            expression=str(every_seconds),
        )
        self._schedules.append(schedule)
        return schedule

    def register_cron(
        self,
        *,
        job_type: str,
        cron_expr: str,
        user_id: str = "system",
        namespace: str = "system",
    ) -> ScheduleConfig:
        schedule = ScheduleConfig.create(
            user_id=user_id,
            namespace=namespace,
            job_type=job_type,
            schedule_type="cron",
            expression=cron_expr,
        )
        self._schedules.append(schedule)
        return schedule

    def list_schedules(
        self,
        *,
        user_id: str | None = None,
        namespace: str | None = None,
    ) -> list[ScheduleConfig]:
        items = list(self._schedules)
        if user_id is not None:
            items = [item for item in items if item.user_id == user_id]
        if namespace is not None:
            items = [item for item in items if item.namespace == namespace]
        return items

    def get_schedule(self, *, schedule_id: str) -> ScheduleConfig | None:
        for schedule in self._schedules:
            if schedule.id == schedule_id:
                return schedule
        return None

    def stop_schedule(self, *, schedule_id: str) -> ScheduleConfig | None:
        schedule = self.get_schedule(schedule_id=schedule_id)
        if schedule is None:
            return None
        schedule.stop()
        return schedule

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False
