"""job_orchestration 调度抽象（in-memory）。"""

from __future__ import annotations

from job_orchestration.domain import ScheduleConfig


class InMemoryScheduler:
    def __init__(self) -> None:
        self._schedules: list[ScheduleConfig] = []
        self.running = False

    def register_interval(self, *, job_type: str, every_seconds: int) -> None:
        self._schedules.append(
            ScheduleConfig(
                job_type=job_type,
                schedule_type="interval",
                expression=str(every_seconds),
            )
        )

    def register_cron(self, *, job_type: str, cron_expr: str) -> None:
        self._schedules.append(
            ScheduleConfig(
                job_type=job_type,
                schedule_type="cron",
                expression=cron_expr,
            )
        )

    def list_schedules(self) -> list[ScheduleConfig]:
        return list(self._schedules)

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False
