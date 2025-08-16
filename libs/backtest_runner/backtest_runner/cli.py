"""backtest_runner CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from backtest_runner.domain import InvalidBacktestTransitionError
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.service import (
    BacktestAccessDeniedError,
    BacktestDeleteInvalidStateError,
    BacktestIdempotencyConflictError,
    BacktestService,
)

_repo = InMemoryBacktestRepository()
_service = BacktestService(repository=_repo)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _serialize_task(task) -> dict:
    return {
        "id": task.id,
        "userId": task.user_id,
        "strategyId": task.strategy_id,
        "status": task.status,
        "config": task.config,
        "metrics": task.metrics,
    }


def _cmd_create(args: argparse.Namespace) -> None:
    try:
        config = json.loads(args.config) if args.config else {}
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_CONFIG", "message": "invalid config json"}})
        return

    idempotency_key = getattr(args, "idempotency_key", None)

    try:
        task = _service.create_task(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            config=config,
            idempotency_key=idempotency_key,
        )
    except BacktestAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "BACKTEST_ACCESS_DENIED",
                    "message": "strategy does not belong to current user",
                },
            }
        )
        return
    except BacktestIdempotencyConflictError as exc:
        _output({"success": False, "error": {"code": "BACKTEST_IDEMPOTENCY_CONFLICT", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_task(task)})


def _cmd_status(args: argparse.Namespace) -> None:
    task = _service.get_task(user_id=args.user_id, task_id=args.task_id)
    if task is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "task not found"}})
        return
    _output({"success": True, "data": _serialize_task(task)})


def _cmd_list(args: argparse.Namespace) -> None:
    listing = _service.list_tasks(
        user_id=args.user_id,
        strategy_id=getattr(args, "strategy_id", None),
        status=args.status,
        page=args.page,
        page_size=args.page_size,
    )
    _output(
        {
            "success": True,
            "data": {
                "items": [_serialize_task(item) for item in listing["items"]],
                "total": listing["total"],
                "page": listing["page"],
                "pageSize": listing["pageSize"],
            },
        }
    )


def _cmd_transition(args: argparse.Namespace) -> None:
    try:
        metrics = json.loads(getattr(args, "metrics", "{}") or "{}")
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_METRICS", "message": "invalid metrics json"}})
        return

    metrics_arg = metrics if metrics else None

    try:
        task = _service.transition(
            user_id=args.user_id,
            task_id=args.task_id,
            to_status=args.to_status,
            metrics=metrics_arg,
        )
    except InvalidBacktestTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    if task is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "task not found"}})
        return

    _output({"success": True, "data": _serialize_task(task)})


def _cmd_cancel(args: argparse.Namespace) -> None:
    try:
        task = _service.cancel_task(user_id=args.user_id, task_id=args.task_id)
    except InvalidBacktestTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    if task is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "task not found"}})
        return

    _output({"success": True, "data": _serialize_task(task)})


def _cmd_retry(args: argparse.Namespace) -> None:
    try:
        task = _service.retry_task(user_id=args.user_id, task_id=args.task_id)
    except InvalidBacktestTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    if task is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "task not found"}})
        return

    _output({"success": True, "data": _serialize_task(task)})


def _cmd_delete(args: argparse.Namespace) -> None:
    try:
        deleted = _service.delete_task(user_id=args.user_id, task_id=args.task_id)
    except BacktestDeleteInvalidStateError as exc:
        _output(
            {
                "success": False,
                "error": {
                    "code": "BACKTEST_DELETE_INVALID_STATE",
                    "message": str(exc),
                },
            }
        )
        return

    if not deleted:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "task not found"}})
        return

    _output({"success": True, "data": {"deleted": True}})


def _cmd_statistics(args: argparse.Namespace) -> None:
    stats = _service.statistics(
        user_id=args.user_id,
        strategy_id=getattr(args, "strategy_id", None),
    )
    _output({"success": True, "data": stats})


def _cmd_compare(args: argparse.Namespace) -> None:
    task_ids = [item for item in args.task_ids.split(",") if item]
    try:
        compared = _service.compare_tasks(user_id=args.user_id, task_ids=task_ids)
    except PermissionError:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "task not found"}})
        return

    _output({"success": True, "data": compared})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backtest-runner", description="QuantPoly 回测任务 CLI")
    sub = parser.add_subparsers(dest="command")

    create = sub.add_parser("create", help="创建回测任务")
    create.add_argument("--user-id", required=True)
    create.add_argument("--strategy-id", required=True)
    create.add_argument("--config", default="{}")
    create.add_argument("--idempotency-key", default=None)

    status = sub.add_parser("status", help="查询回测任务")
    status.add_argument("--user-id", required=True)
    status.add_argument("--task-id", required=True)

    list_cmd = sub.add_parser("list", help="列表查询回测任务")
    list_cmd.add_argument("--user-id", required=True)
    list_cmd.add_argument("--strategy-id", default=None)
    list_cmd.add_argument("--status", default=None)
    list_cmd.add_argument("--page", type=int, default=1)
    list_cmd.add_argument("--page-size", type=int, default=20)

    transition = sub.add_parser("transition", help="状态迁移")
    transition.add_argument("--user-id", required=True)
    transition.add_argument("--task-id", required=True)
    transition.add_argument("--to-status", required=True)
    transition.add_argument("--metrics", default="{}")

    cancel = sub.add_parser("cancel", help="取消任务")
    cancel.add_argument("--user-id", required=True)
    cancel.add_argument("--task-id", required=True)

    retry = sub.add_parser("retry", help="重试任务")
    retry.add_argument("--user-id", required=True)
    retry.add_argument("--task-id", required=True)

    delete = sub.add_parser("delete", help="删除任务")
    delete.add_argument("--user-id", required=True)
    delete.add_argument("--task-id", required=True)

    statistics = sub.add_parser("statistics", help="回测统计")
    statistics.add_argument("--user-id", required=True)
    statistics.add_argument("--strategy-id", default=None)

    compare = sub.add_parser("compare", help="回测任务对比")
    compare.add_argument("--user-id", required=True)
    compare.add_argument("--task-ids", required=True)

    return parser


_COMMANDS = {
    "create": _cmd_create,
    "status": _cmd_status,
    "list": _cmd_list,
    "transition": _cmd_transition,
    "cancel": _cmd_cancel,
    "retry": _cmd_retry,
    "delete": _cmd_delete,
    "statistics": _cmd_statistics,
    "compare": _cmd_compare,
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
