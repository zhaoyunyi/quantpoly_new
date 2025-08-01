"""跨库迁移 dry-run 与回滚演练。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MigrationPlan:
    model_name: str
    from_db: str
    to_db: str
    row_count: int
    up_steps: list[str] = field(default_factory=list)
    down_steps: list[str] = field(default_factory=list)
    backfill_steps: list[str] = field(default_factory=list)
    compensation: dict[str, str] = field(default_factory=dict)


class MigrationPlanner:
    def dry_run(
        self,
        *,
        model_name: str,
        from_db: str,
        to_db: str,
        row_count: int,
    ) -> MigrationPlan:
        up_steps = [
            f"create_target_table model={model_name} db={to_db}",
            f"copy_rows model={model_name} from={from_db} to={to_db} rows={row_count}",
            f"switch_writes model={model_name} to={to_db}",
        ]
        down_steps = [
            f"switch_writes model={model_name} to={from_db}",
            f"cleanup_target_rows model={model_name} db={to_db}",
        ]
        backfill_steps = [
            f"backfill_recent_changes model={model_name} from={from_db} to={to_db}",
            f"reconcile_counts model={model_name}",
        ]

        compensation = {
            "retryPolicy": "exponential_backoff_max_5",
            "reconcileCommand": f"reconcile --model {model_name}",
            "alertChannel": "ops-data-topology",
        }

        return MigrationPlan(
            model_name=model_name,
            from_db=from_db,
            to_db=to_db,
            row_count=row_count,
            up_steps=up_steps,
            down_steps=down_steps,
            backfill_steps=backfill_steps,
            compensation=compensation,
        )

    def rollback_drill(self, plan: MigrationPlan) -> dict:
        executed = list(plan.down_steps)
        return {
            "success": True,
            "executedDownSteps": len(executed),
            "steps": executed,
        }
