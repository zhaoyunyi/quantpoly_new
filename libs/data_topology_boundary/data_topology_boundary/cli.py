"""data_topology_boundary CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from data_topology_boundary.catalog import default_catalog
from data_topology_boundary.migration import MigrationPlanner
from data_topology_boundary.policy import CrossDbPolicy, detect_illegal_dependencies
from data_topology_boundary.reconciliation import reconcile_by_key


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _cmd_check_model(args: argparse.Namespace) -> None:
    catalog = default_catalog()
    database = catalog.model_database(args.model)
    matched = database == args.db
    _output(
        {
            "success": True,
            "data": {
                "model": args.model,
                "database": database,
                "expected": args.db,
                "matched": matched,
            },
        }
    )


def _parse_edges(raw: str) -> list[tuple[str, str]]:
    values = json.loads(raw) if raw else []
    edges: list[tuple[str, str]] = []
    for item in values:
        if not isinstance(item, list | tuple) or len(item) != 2:
            continue
        edges.append((str(item[0]), str(item[1])))
    return edges


def _cmd_scan_cross_db(args: argparse.Namespace) -> None:
    catalog = default_catalog()
    policy = CrossDbPolicy(catalog=catalog)
    edges = _parse_edges(args.edges)
    illegal = detect_illegal_dependencies(edges=edges, policy=policy)

    _output(
        {
            "success": True,
            "data": {
                "illegalCount": len(illegal),
                "illegalEdges": [{"from": x[0], "to": x[1]} for x in illegal],
            },
        }
    )


def _cmd_migration_dry_run(args: argparse.Namespace) -> None:
    planner = MigrationPlanner()
    plan = planner.dry_run(
        model_name=args.model,
        from_db=args.from_db,
        to_db=args.to_db,
        row_count=args.rows,
    )

    _output(
        {
            "success": True,
            "data": {
                "modelName": plan.model_name,
                "fromDb": plan.from_db,
                "toDb": plan.to_db,
                "rowCount": plan.row_count,
                "upSteps": plan.up_steps,
                "downSteps": plan.down_steps,
                "backfillSteps": plan.backfill_steps,
                "compensation": plan.compensation,
            },
        }
    )


def _cmd_reconcile(args: argparse.Namespace) -> None:
    before_rows = json.loads(args.before)
    after_rows = json.loads(args.after)
    report = reconcile_by_key(before_rows=before_rows, after_rows=after_rows, key=args.key)

    _output(
        {
            "success": True,
            "data": {
                "consistent": report.consistent,
                "missingIds": report.missing_ids,
                "extraIds": report.extra_ids,
                "mismatchCount": report.mismatch_count,
                "beforeCount": report.before_count,
                "afterCount": report.after_count,
            },
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data-topology-boundary",
        description="QuantPoly 数据拓扑边界治理 CLI",
    )
    sub = parser.add_subparsers(dest="command")

    check = sub.add_parser("check-model", help="校验模型归属")
    check.add_argument("--model", required=True)
    check.add_argument("--db", required=True)

    scan = sub.add_parser("scan-cross-db", help="检测非法跨库依赖")
    scan.add_argument("--edges", required=True, help='JSON: [["From","To"], ...]')

    dry_run = sub.add_parser("migration-dry-run", help="迁移 dry-run")
    dry_run.add_argument("--model", required=True)
    dry_run.add_argument("--from-db", required=True)
    dry_run.add_argument("--to-db", required=True)
    dry_run.add_argument("--rows", type=int, required=True)

    reconcile = sub.add_parser("reconcile", help="迁移前后对账")
    reconcile.add_argument("--before", required=True, help="迁移前 JSON rows")
    reconcile.add_argument("--after", required=True, help="迁移后 JSON rows")
    reconcile.add_argument("--key", default="id")

    return parser


_COMMANDS: dict[str, Any] = {
    "check-model": _cmd_check_model,
    "scan-cross-db": _cmd_scan_cross_db,
    "migration-dry-run": _cmd_migration_dry_run,
    "reconcile": _cmd_reconcile,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
