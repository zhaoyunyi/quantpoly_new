"""risk_control CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from risk_control.repository import InMemoryRiskRepository
from risk_control.service import AccountAccessDeniedError, RiskControlService

_repo = InMemoryRiskRepository()
_service = RiskControlService(repository=_repo, account_owner_acl=lambda _user_id, _account_id: True)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _cmd_stats(args: argparse.Namespace) -> None:
    try:
        stats = _service.alert_stats(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "ALERT_ACCESS_DENIED",
                    "message": "alert does not belong to current user",
                },
            }
        )
        return

    _output(
        {
            "success": True,
            "data": {
                "total": stats.total,
                "open": stats.open,
                "acknowledged": stats.acknowledged,
                "resolved": stats.resolved,
                "bySeverity": stats.by_severity,
            },
        }
    )


def _cmd_batch_acknowledge(args: argparse.Namespace) -> None:
    alert_ids = [item.strip() for item in args.alert_ids.split(",") if item.strip()]
    try:
        affected = _service.batch_acknowledge(user_id=args.user_id, alert_ids=alert_ids)
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "ALERT_ACCESS_DENIED",
                    "message": "alert does not belong to current user",
                },
            }
        )
        return

    _output({"success": True, "data": {"affected": affected}})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="risk-control", description="QuantPoly 风控 CLI")
    sub = parser.add_subparsers(dest="command")

    stats = sub.add_parser("stats", help="统计告警")
    stats.add_argument("--user-id", required=True)
    stats.add_argument("--account-id", default=None)

    batch = sub.add_parser("batch-acknowledge", help="批量确认告警")
    batch.add_argument("--user-id", required=True)
    batch.add_argument("--alert-ids", required=True)

    return parser


_COMMANDS = {
    "stats": _cmd_stats,
    "batch-acknowledge": _cmd_batch_acknowledge,
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
