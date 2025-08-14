"""strategy_management CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from strategy_management.domain import InvalidStrategyTransitionError, StrategyInUseError
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import (
    InvalidStrategyParametersError,
    StrategyAccessDeniedError,
    StrategyService,
)

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
        "status": strategy.status,
    }


def _cmd_template_list(args: argparse.Namespace) -> None:
    del args
    _output({"success": True, "data": _service.list_templates()})


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


def _cmd_create_from_template(args: argparse.Namespace) -> None:
    try:
        parameters = json.loads(args.parameters) if args.parameters else {}
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_PARAMETERS", "message": "invalid parameters json"}})
        return

    try:
        created = _service.create_strategy_from_template(
            user_id=args.user_id,
            name=args.name,
            template_id=args.template_id,
            parameters=parameters,
        )
    except InvalidStrategyParametersError as exc:
        _output({"success": False, "error": {"code": "STRATEGY_INVALID_PARAMETERS", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_strategy(created)})


def _cmd_validate_execution(args: argparse.Namespace) -> None:
    try:
        parameters = json.loads(args.parameters) if args.parameters else {}
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_PARAMETERS", "message": "invalid parameters json"}})
        return

    try:
        strategy = _service.validate_execution_parameters(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            parameters=parameters,
        )
    except StrategyAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "STRATEGY_ACCESS_DENIED",
                    "message": "strategy does not belong to current user",
                },
            }
        )
        return
    except InvalidStrategyParametersError as exc:
        _output({"success": False, "error": {"code": "STRATEGY_INVALID_PARAMETERS", "message": str(exc)}})
        return

    _output(
        {
            "success": True,
            "data": {
                "valid": True,
                "strategyId": strategy.id,
                "template": strategy.template,
            },
        }
    )


def _cmd_activate(args: argparse.Namespace) -> None:
    try:
        strategy = _service.activate_strategy(user_id=args.user_id, strategy_id=args.strategy_id)
    except InvalidStrategyTransitionError as exc:
        _output({"success": False, "error": {"code": "STRATEGY_INVALID_TRANSITION", "message": str(exc)}})
        return

    if strategy is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "strategy not found"}})
        return

    _output({"success": True, "data": _serialize_strategy(strategy)})


def _cmd_deactivate(args: argparse.Namespace) -> None:
    try:
        strategy = _service.deactivate_strategy(user_id=args.user_id, strategy_id=args.strategy_id)
    except InvalidStrategyTransitionError as exc:
        _output({"success": False, "error": {"code": "STRATEGY_INVALID_TRANSITION", "message": str(exc)}})
        return

    if strategy is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "strategy not found"}})
        return

    _output({"success": True, "data": _serialize_strategy(strategy)})


def _cmd_archive(args: argparse.Namespace) -> None:
    try:
        strategy = _service.archive_strategy(user_id=args.user_id, strategy_id=args.strategy_id)
    except InvalidStrategyTransitionError as exc:
        _output({"success": False, "error": {"code": "STRATEGY_INVALID_TRANSITION", "message": str(exc)}})
        return

    if strategy is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "strategy not found"}})
        return

    _output({"success": True, "data": _serialize_strategy(strategy)})


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

    template_list = sub.add_parser("template-list", help="列出策略模板")
    template_list.add_argument("--user-id", required=False)

    create = sub.add_parser("create", help="创建策略")
    create.add_argument("--user-id", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--template", required=True)
    create.add_argument("--parameters", default="{}")

    create_from_template = sub.add_parser("create-from-template", help="从模板创建策略")
    create_from_template.add_argument("--user-id", required=True)
    create_from_template.add_argument("--name", required=True)
    create_from_template.add_argument("--template-id", required=True)
    create_from_template.add_argument("--parameters", default="{}")

    validate_execution = sub.add_parser("validate-execution", help="执行前参数校验")
    validate_execution.add_argument("--user-id", required=True)
    validate_execution.add_argument("--strategy-id", required=True)
    validate_execution.add_argument("--parameters", default="{}")

    activate = sub.add_parser("activate", help="激活策略")
    activate.add_argument("--user-id", required=True)
    activate.add_argument("--strategy-id", required=True)

    deactivate = sub.add_parser("deactivate", help="停用策略")
    deactivate.add_argument("--user-id", required=True)
    deactivate.add_argument("--strategy-id", required=True)

    archive = sub.add_parser("archive", help="归档策略")
    archive.add_argument("--user-id", required=True)
    archive.add_argument("--strategy-id", required=True)

    list_cmd = sub.add_parser("list", help="列表策略")
    list_cmd.add_argument("--user-id", required=True)

    delete = sub.add_parser("delete", help="删除策略")
    delete.add_argument("--user-id", required=True)
    delete.add_argument("--strategy-id", required=True)

    return parser


_COMMANDS = {
    "template-list": _cmd_template_list,
    "create": _cmd_create,
    "create-from-template": _cmd_create_from_template,
    "validate-execution": _cmd_validate_execution,
    "activate": _cmd_activate,
    "deactivate": _cmd_deactivate,
    "archive": _cmd_archive,
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
