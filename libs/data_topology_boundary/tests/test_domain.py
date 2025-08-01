"""data_topology_boundary 领域测试。"""

from __future__ import annotations


def test_default_catalog_model_ownership():
    from data_topology_boundary.catalog import default_catalog

    catalog = default_catalog()

    assert catalog.model_database("User") == "user_db"
    assert catalog.model_database("Session") == "user_db"
    assert catalog.model_database("Strategy") == "business_db"
    assert catalog.model_database("BacktestTask") == "business_db"


def test_illegal_cross_db_dependency_detection():
    from data_topology_boundary.catalog import default_catalog
    from data_topology_boundary.policy import CrossDbPolicy, detect_illegal_dependencies

    catalog = default_catalog()
    policy = CrossDbPolicy(catalog=catalog)

    edges = [
        ("Strategy", "BacktestTask"),
        ("Strategy", "User"),
        ("RiskAlert", "Session"),
    ]

    illegal = detect_illegal_dependencies(edges=edges, policy=policy)

    assert len(illegal) == 2
    assert ("Strategy", "User") in illegal
    assert ("RiskAlert", "Session") in illegal


def test_migration_dry_run_and_rollback_drill():
    from data_topology_boundary.migration import MigrationPlanner

    planner = MigrationPlanner()
    plan = planner.dry_run(
        model_name="Strategy",
        from_db="user_db",
        to_db="business_db",
        row_count=120,
    )

    assert plan.model_name == "Strategy"
    assert plan.row_count == 120
    assert plan.up_steps
    assert plan.down_steps
    assert plan.backfill_steps

    drill = planner.rollback_drill(plan)
    assert drill["success"] is True
    assert drill["executedDownSteps"] == len(plan.down_steps)


def test_reconciliation_report_detects_missing_and_extra_rows():
    from data_topology_boundary.reconciliation import reconcile_by_key

    before_rows = [
        {"id": "1", "name": "A"},
        {"id": "2", "name": "B"},
        {"id": "3", "name": "C"},
    ]
    after_rows = [
        {"id": "2", "name": "B"},
        {"id": "3", "name": "C"},
        {"id": "4", "name": "D"},
    ]

    report = reconcile_by_key(before_rows=before_rows, after_rows=after_rows, key="id")

    assert report.consistent is False
    assert report.missing_ids == ["1"]
    assert report.extra_ids == ["4"]

