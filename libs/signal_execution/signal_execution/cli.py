"""signal_execution CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import AdminRequiredError, SignalAccessDeniedError, SignalExecutionService

_repo = InMemorySignalRepository()
_service = SignalExecutionService(
    repository=_repo,
    strategy_owner_acl=lambda _user_id, _strategy_id: True,
    account_owner_acl=lambda _user_id, _account_id: True,
)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _cmd_trend(args: argparse.Namespace) -> None:
    _output({"success": True, "data": _service.execution_trend(user_id=args.user_id)})


def _cmd_cleanup_all(args: argparse.Namespace) -> None:
    try:
        deleted = _service.cleanup_all_signals(user_id=args.user_id, is_admin=args.is_admin)
    except AdminRequiredError:
        _output({"success": False, "error": {"code": "ADMIN_REQUIRED", "message": "admin role required"}})
        return

    _output({"success": True, "data": {"deleted": deleted}})


def _cmd_execute(args: argparse.Namespace) -> None:
    try:
        signal = _service.execute_signal(user_id=args.user_id, signal_id=args.signal_id)
    except SignalAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "SIGNAL_ACCESS_DENIED",
                    "message": "signal does not belong to current user",
                },
            }
        )
        return

    _output({"success": True, "data": {"id": signal.id, "status": signal.status}})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="signal-execution", description="QuantPoly 信号执行 CLI")
    sub = parser.add_subparsers(dest="command")

    trend = sub.add_parser("trend", help="查询执行趋势")
    trend.add_argument("--user-id", required=True)

    cleanup_all = sub.add_parser("cleanup-all", help="全局清理（管理员）")
    cleanup_all.add_argument("--user-id", required=True)
    cleanup_all.add_argument("--is-admin", action="store_true")

    execute = sub.add_parser("execute", help="执行信号")
    execute.add_argument("--user-id", required=True)
    execute.add_argument("--signal-id", required=True)

    return parser


_COMMANDS = {
    "trend": _cmd_trend,
    "cleanup-all": _cmd_cleanup_all,
    "execute": _cmd_execute,
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
