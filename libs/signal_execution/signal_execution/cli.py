"""signal_execution CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import (
    AdminRequiredError,
    BatchIdempotencyConflictError,
    SignalAccessDeniedError,
    SignalExecutionService,
)

_repo = InMemorySignalRepository()
_service = SignalExecutionService(
    repository=_repo,
    strategy_owner_acl=lambda _user_id, _strategy_id: True,
    account_owner_acl=lambda _user_id, _account_id: True,
)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _parse_csv(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def _cmd_trend(args: argparse.Namespace) -> None:
    _output({"success": True, "data": _service.execution_trend(user_id=args.user_id)})


def _cmd_cleanup_all(args: argparse.Namespace) -> None:
    try:
        deleted = _service.cleanup_all_signals(
            user_id=args.user_id,
            is_admin=args.is_admin,
            confirmation_token=getattr(args, "confirmation_token", None),
        )
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


def _cmd_batch_execute(args: argparse.Namespace) -> None:
    try:
        result = _service.batch_execute_signals(
            user_id=args.user_id,
            signal_ids=_parse_csv(args.signal_ids),
            idempotency_key=args.idempotency_key,
        )
    except BatchIdempotencyConflictError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "IDEMPOTENCY_CONFLICT",
                    "message": "idempotency key already exists",
                },
            }
        )
        return

    _output({"success": True, "data": result})


def _cmd_batch_cancel(args: argparse.Namespace) -> None:
    try:
        result = _service.batch_cancel_signals(
            user_id=args.user_id,
            signal_ids=_parse_csv(args.signal_ids),
            idempotency_key=args.idempotency_key,
        )
    except BatchIdempotencyConflictError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "IDEMPOTENCY_CONFLICT",
                    "message": "idempotency key already exists",
                },
            }
        )
        return

    _output({"success": True, "data": result})


def _cmd_performance(args: argparse.Namespace) -> None:
    data = _service.performance_statistics(
        user_id=args.user_id,
        strategy_id=args.strategy_id,
        symbol=args.symbol,
    )
    _output({"success": True, "data": data})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="signal-execution", description="QuantPoly 信号执行 CLI")
    sub = parser.add_subparsers(dest="command")

    trend = sub.add_parser("trend", help="查询执行趋势")
    trend.add_argument("--user-id", required=True)

    cleanup_all = sub.add_parser("cleanup-all", help="全局清理（管理员）")
    cleanup_all.add_argument("--user-id", required=True)
    cleanup_all.add_argument("--is-admin", action="store_true")
    cleanup_all.add_argument("--confirmation-token", default=None)

    execute = sub.add_parser("execute", help="执行信号")
    execute.add_argument("--user-id", required=True)
    execute.add_argument("--signal-id", required=True)

    batch_execute = sub.add_parser("batch-execute", help="批量执行信号")
    batch_execute.add_argument("--user-id", required=True)
    batch_execute.add_argument("--signal-ids", required=True)
    batch_execute.add_argument("--idempotency-key", default=None)

    batch_cancel = sub.add_parser("batch-cancel", help="批量取消信号")
    batch_cancel.add_argument("--user-id", required=True)
    batch_cancel.add_argument("--signal-ids", required=True)
    batch_cancel.add_argument("--idempotency-key", default=None)

    performance = sub.add_parser("performance", help="执行绩效统计")
    performance.add_argument("--user-id", required=True)
    performance.add_argument("--strategy-id", default=None)
    performance.add_argument("--symbol", default=None)

    return parser


_COMMANDS = {
    "trend": _cmd_trend,
    "cleanup-all": _cmd_cleanup_all,
    "execute": _cmd_execute,
    "batch-execute": _cmd_batch_execute,
    "batch-cancel": _cmd_batch_cancel,
    "performance": _cmd_performance,
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
