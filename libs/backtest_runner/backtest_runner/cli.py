"""backtest_runner CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from backtest_runner.domain import InvalidBacktestTransitionError
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.service import BacktestService

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
    }


def _cmd_create(args: argparse.Namespace) -> None:
    try:
        config = json.loads(args.config) if args.config else {}
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_CONFIG", "message": "invalid config json"}})
        return

    task = _service.create_task(
        user_id=args.user_id,
        strategy_id=args.strategy_id,
        config=config,
    )
    _output({"success": True, "data": _serialize_task(task)})


def _cmd_status(args: argparse.Namespace) -> None:
    task = _service.get_task(user_id=args.user_id, task_id=args.task_id)
    if task is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "task not found"}})
        return
    _output({"success": True, "data": _serialize_task(task)})


def _cmd_transition(args: argparse.Namespace) -> None:
    try:
        task = _service.transition(
            user_id=args.user_id,
            task_id=args.task_id,
            to_status=args.to_status,
        )
    except InvalidBacktestTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    if task is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "task not found"}})
        return

    _output({"success": True, "data": _serialize_task(task)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backtest-runner", description="QuantPoly 回测任务 CLI")
    sub = parser.add_subparsers(dest="command")

    create = sub.add_parser("create", help="创建回测任务")
    create.add_argument("--user-id", required=True)
    create.add_argument("--strategy-id", required=True)
    create.add_argument("--config", default="{}")

    status = sub.add_parser("status", help="查询回测任务")
    status.add_argument("--user-id", required=True)
    status.add_argument("--task-id", required=True)

    transition = sub.add_parser("transition", help="状态迁移")
    transition.add_argument("--user-id", required=True)
    transition.add_argument("--task-id", required=True)
    transition.add_argument("--to-status", required=True)

    return parser


_COMMANDS = {
    "create": _cmd_create,
    "status": _cmd_status,
    "transition": _cmd_transition,
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
