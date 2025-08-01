"""data_topology_boundary CLI 测试。"""

from __future__ import annotations

import argparse
import json

from data_topology_boundary import cli


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_check_model_returns_ownership_result(capsys):
    payload = _run(
        cli._cmd_check_model,
        capsys=capsys,
        model="User",
        db="user_db",
    )

    assert payload["success"] is True
    assert payload["data"]["matched"] is True
    assert payload["data"]["database"] == "user_db"


def test_cli_scan_cross_db_returns_illegal_edges(capsys):
    edges = json.dumps(
        [
            ["Strategy", "BacktestTask"],
            ["Strategy", "User"],
            ["RiskAlert", "Session"],
        ]
    )
    payload = _run(cli._cmd_scan_cross_db, capsys=capsys, edges=edges)

    assert payload["success"] is True
    assert payload["data"]["illegalCount"] == 2


def test_cli_migration_dry_run_outputs_plan(capsys):
    payload = _run(
        cli._cmd_migration_dry_run,
        capsys=capsys,
        model="Strategy",
        from_db="user_db",
        to_db="business_db",
        rows=88,
    )

    assert payload["success"] is True
    assert payload["data"]["modelName"] == "Strategy"
    assert payload["data"]["rowCount"] == 88
    assert payload["data"]["upSteps"]
    assert payload["data"]["downSteps"]


def test_cli_reconcile_outputs_mismatch_report(capsys):
    before_rows = json.dumps([{"id": "1", "name": "A"}, {"id": "2", "name": "B"}])
    after_rows = json.dumps([{"id": "2", "name": "B"}, {"id": "3", "name": "C"}])

    payload = _run(
        cli._cmd_reconcile,
        capsys=capsys,
        before=before_rows,
        after=after_rows,
        key="id",
    )

    assert payload["success"] is True
    assert payload["data"]["consistent"] is False
    assert payload["data"]["missingIds"] == ["1"]
    assert payload["data"]["extraIds"] == ["3"]

