"""signal_execution CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Any

from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import (
    AdminRequiredError,
    BatchIdempotencyConflictError,
    InvalidSignalParametersError,
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


def _parse_json(text: str | None) -> dict[str, Any]:
    if not text:
        return {}
    return json.loads(text)


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _execution_payload(record) -> dict:
    return {
        "id": record.id,
        "signalId": record.signal_id,
        "strategyId": record.strategy_id,
        "symbol": record.symbol,
        "status": record.status,
        "metrics": record.metrics,
        "createdAt": _dt(record.created_at),
    }


def _running_signal_payload(signal) -> dict:
    return {
        "signalId": signal.id,
        "strategyId": signal.strategy_id,
        "accountId": signal.account_id,
        "symbol": signal.symbol,
        "status": signal.status,
        "updatedAt": _dt(signal.updated_at),
    }


def _cmd_trend(args: argparse.Namespace) -> None:
    _output({"success": True, "data": _service.execution_trend(user_id=args.user_id)})


def _cmd_validate_parameters(args: argparse.Namespace) -> None:
    try:
        parameters = _parse_json(args.parameters)
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_PARAMETERS", "message": "invalid parameters json"}})
        return

    try:
        _service.validate_parameters(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            account_id=args.account_id,
            parameters=parameters,
        )
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
    except InvalidSignalParametersError as exc:
        _output(
            {
                "success": False,
                "error": {
                    "code": "SIGNAL_INVALID_PARAMETERS",
                    "message": str(exc),
                },
            }
        )
        return

    _output({"success": True, "data": {"valid": True}})


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


def _cmd_execution_detail(args: argparse.Namespace) -> None:
    try:
        execution = _service.get_execution(user_id=args.user_id, execution_id=args.execution_id)
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

    _output({"success": True, "data": _execution_payload(execution)})


def _cmd_running(args: argparse.Namespace) -> None:
    items = _service.list_running_executions(user_id=args.user_id)
    _output({"success": True, "data": [_running_signal_payload(item) for item in items]})


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

    validate_parameters = sub.add_parser("validate-parameters", help="执行前参数校验")
    validate_parameters.add_argument("--user-id", required=True)
    validate_parameters.add_argument("--strategy-id", required=True)
    validate_parameters.add_argument("--account-id", required=True)
    validate_parameters.add_argument("--parameters", default="{}")

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

    execution_detail = sub.add_parser("execution-detail", help="执行详情")
    execution_detail.add_argument("--user-id", required=True)
    execution_detail.add_argument("--execution-id", required=True)

    running = sub.add_parser("running", help="运行中执行")
    running.add_argument("--user-id", required=True)

    performance = sub.add_parser("performance", help="执行绩效统计")
    performance.add_argument("--user-id", required=True)
    performance.add_argument("--strategy-id", default=None)
    performance.add_argument("--symbol", default=None)

    return parser


_COMMANDS = {
    "trend": _cmd_trend,
    "validate-parameters": _cmd_validate_parameters,
    "cleanup-all": _cmd_cleanup_all,
    "execute": _cmd_execute,
    "batch-execute": _cmd_batch_execute,
    "batch-cancel": _cmd_batch_cancel,
    "execution-detail": _cmd_execution_detail,
    "running": _cmd_running,
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
