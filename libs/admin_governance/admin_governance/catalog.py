"""管理员动作目录。"""

from __future__ import annotations

from admin_governance.domain import ActionPolicy


def default_action_catalog() -> dict[str, ActionPolicy]:
    return {
        "signals.cleanup_execution_history": ActionPolicy(
            action="signals.cleanup_execution_history",
            min_role="admin",
            min_level=5,
            requires_confirmation=False,
            high_risk=False,
        ),
        "signals.cleanup_all": ActionPolicy(
            action="signals.cleanup_all",
            min_role="admin",
            min_level=5,
            requires_confirmation=True,
            high_risk=True,
        ),
        "jobs.cleanup_all": ActionPolicy(
            action="jobs.cleanup_all",
            min_role="admin",
            min_level=5,
            requires_confirmation=True,
            high_risk=True,
        ),
        "risk.batch_maintain": ActionPolicy(
            action="risk.batch_maintain",
            min_role="admin",
            min_level=3,
            requires_confirmation=False,
            high_risk=False,
        ),
        "trading.refresh_prices": ActionPolicy(
            action="trading.refresh_prices",
            min_role="admin",
            min_level=5,
            requires_confirmation=True,
            high_risk=True,
        ),
        "trading.process_pending": ActionPolicy(
            action="trading.process_pending",
            min_role="admin",
            min_level=5,
            requires_confirmation=True,
            high_risk=True,
        ),
        "trading.calculate_daily_stats": ActionPolicy(
            action="trading.calculate_daily_stats",
            min_role="admin",
            min_level=4,
            requires_confirmation=False,
            high_risk=False,
        ),
        "trading.batch_execute": ActionPolicy(
            action="trading.batch_execute",
            min_role="admin",
            min_level=5,
            requires_confirmation=True,
            high_risk=True,
        ),
        "trading.risk_monitor": ActionPolicy(
            action="trading.risk_monitor",
            min_role="admin",
            min_level=4,
            requires_confirmation=False,
            high_risk=False,
        ),
        "trading.account_cleanup": ActionPolicy(
            action="trading.account_cleanup",
            min_role="admin",
            min_level=5,
            requires_confirmation=True,
            high_risk=True,
        ),
        "admin_create_user": ActionPolicy(
            action="admin_create_user",
            min_role="admin",
            min_level=2,
            requires_confirmation=False,
            high_risk=False,
        ),
        "users.read_all": ActionPolicy(
            action="users.read_all",
            min_role="admin",
            min_level=2,
            requires_confirmation=False,
            high_risk=False,
        ),
        "users.update": ActionPolicy(
            action="users.update",
            min_role="admin",
            min_level=2,
            requires_confirmation=False,
            high_risk=False,
        ),
        "users.delete": ActionPolicy(
            action="users.delete",
            min_role="admin",
            min_level=2,
            requires_confirmation=False,
            high_risk=False,
        ),
    }
