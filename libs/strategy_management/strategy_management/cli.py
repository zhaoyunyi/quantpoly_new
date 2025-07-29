"""strategy_management CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from strategy_management.domain import StrategyInUseError
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import StrategyService

_repo = InMemoryStrategyRepository()
_service = StrategyService(repository=_repo, count_active_backtests=lambda _strategy_id: 0)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _serialize_strategy(strategy) -> dict:
    return {
        "id": strategy.id,
        "userId": strategy.user_id,
        "name": strategy.name,
        "template": strategy.template,
        "parameters": strategy.parameters,
    }


def _cmd_create(args: argparse.Namespace) -> None:
    try:
        parameters = json.loads(args.parameters) if args.parameters else {}
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_PARAMETERS", "message": "invalid parameters json"}})
        return

    created = _service.create_strategy(
        user_id=args.user_id,
        name=args.name,
        template=args.template,
        parameters=parameters,
    )
    _output({"success": True, "data": _serialize_strategy(created)})


def _cmd_list(args: argparse.Namespace) -> None:
    items = _service.list_strategies(user_id=args.user_id)
    _output({"success": True, "data": [_serialize_strategy(item) for item in items]})


def _cmd_delete(args: argparse.Namespace) -> None:
    try:
        deleted = _service.delete_strategy(user_id=args.user_id, strategy_id=args.strategy_id)
    except StrategyInUseError as exc:
        _output({"success": False, "error": {"code": "STRATEGY_IN_USE", "message": str(exc)}})
        return

    if not deleted:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "strategy not found"}})
        return

    _output({"success": True, "message": "deleted"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="strategy-management", description="QuantPoly 策略管理 CLI")
    sub = parser.add_subparsers(dest="command")

    create = sub.add_parser("create", help="创建策略")
    create.add_argument("--user-id", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--template", required=True)
    create.add_argument("--parameters", default="{}")

    list_cmd = sub.add_parser("list", help="列表策略")
    list_cmd.add_argument("--user-id", required=True)

    delete = sub.add_parser("delete", help="删除策略")
    delete.add_argument("--user-id", required=True)
    delete.add_argument("--strategy-id", required=True)

    return parser


_COMMANDS = {
    "create": _cmd_create,
    "list": _cmd_list,
    "delete": _cmd_delete,
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
