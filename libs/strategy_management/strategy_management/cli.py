"""strategy_management CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.service import BacktestService
from strategy_management.domain import InvalidStrategyTransitionError, StrategyInUseError
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import (
    InvalidStrategyParametersError,
    StrategyAccessDeniedError,
    StrategyService,
)

_repo = InMemoryStrategyRepository()
_backtest_repo = InMemoryBacktestRepository()
_backtest_service = BacktestService(
    repository=_backtest_repo,
    strategy_owner_acl=lambda user_id, strategy_id: _repo.get_by_id(strategy_id, user_id=user_id)
    is not None,
)
_service = StrategyService(
    repository=_repo,
    count_active_backtests=lambda user_id, strategy_id: _backtest_service.count_active_backtests(
        user_id=user_id,
        strategy_id=strategy_id,
    ),
    create_backtest_for_strategy=lambda user_id, strategy_id, config, idempotency_key: _backtest_service.create_task(
        user_id=user_id,
        strategy_id=strategy_id,
        config=config,
        idempotency_key=idempotency_key,
    ),
    list_backtests_for_strategy=lambda user_id, strategy_id, status, page, page_size: _backtest_service.list_tasks(
        user_id=user_id,
        strategy_id=strategy_id,
        status=status,
        page=page,
        page_size=page_size,
    ),
    stats_backtests_for_strategy=lambda user_id, strategy_id: _backtest_service.statistics(
        user_id=user_id,
        strategy_id=strategy_id,
    ),
)


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


def _serialize_backtest(task) -> dict:
    if isinstance(task, dict):
        return task

    return {
        "id": task.id,
        "userId": task.user_id,
        "strategyId": task.strategy_id,
        "status": task.status,
        "config": task.config,
        "metrics": task.metrics,
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


def _cmd_update(args: argparse.Namespace) -> None:
    name = getattr(args, "name", None)

    parameters = None
    if getattr(args, "parameters", None) is not None:
        try:
            parameters = json.loads(args.parameters)
        except json.JSONDecodeError:
            _output(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_PARAMETERS",
                        "message": "invalid parameters json",
                    },
                }
            )
            return

    try:
        updated = _service.update_strategy(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            name=name,
            parameters=parameters,
        )
    except InvalidStrategyParametersError as exc:
        _output({"success": False, "error": {"code": "STRATEGY_INVALID_PARAMETERS", "message": str(exc)}})
        return

    if updated is None:
        _output({"success": False, "error": {"code": "NOT_FOUND", "message": "strategy not found"}})
        return

    _output({"success": True, "data": _serialize_strategy(updated)})


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


def _cmd_backtest_create(args: argparse.Namespace) -> None:
    try:
        config = json.loads(args.config) if args.config else {}
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_CONFIG", "message": "invalid config json"}})
        return

    try:
        task = _service.create_backtest_for_strategy(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            config=config,
            idempotency_key=getattr(args, "idempotency_key", None),
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

    _output({"success": True, "data": _serialize_backtest(task)})


def _cmd_backtest_list(args: argparse.Namespace) -> None:
    try:
        listing = _service.list_backtests_for_strategy(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            status=args.status,
            page=args.page,
            page_size=args.page_size,
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

    items = [_serialize_backtest(item) for item in listing.get("items", [])]
    _output(
        {
            "success": True,
            "data": {
                "items": items,
                "total": int(listing.get("total", len(items))),
                "page": int(listing.get("page", args.page)),
                "pageSize": int(listing.get("pageSize", args.page_size)),
            },
        }
    )


def _cmd_backtest_stats(args: argparse.Namespace) -> None:
    try:
        stats = _service.backtest_stats_for_strategy(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
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

    _output({"success": True, "data": stats})


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

    update = sub.add_parser("update", help="更新策略")
    update.add_argument("--user-id", required=True)
    update.add_argument("--strategy-id", required=True)
    update.add_argument("--name", default=None)
    update.add_argument("--parameters", default=None)

    create_from_template = sub.add_parser("create-from-template", help="从模板创建策略")
    create_from_template.add_argument("--user-id", required=True)
    create_from_template.add_argument("--name", required=True)
    create_from_template.add_argument("--template-id", required=True)
    create_from_template.add_argument("--parameters", default="{}")

    validate_execution = sub.add_parser("validate-execution", help="执行前参数校验")
    validate_execution.add_argument("--user-id", required=True)
    validate_execution.add_argument("--strategy-id", required=True)
    validate_execution.add_argument("--parameters", default="{}")

    backtest_create = sub.add_parser("backtest-create", help="触发策略回测")
    backtest_create.add_argument("--user-id", required=True)
    backtest_create.add_argument("--strategy-id", required=True)
    backtest_create.add_argument("--config", default="{}")
    backtest_create.add_argument("--idempotency-key", default=None)

    backtest_list = sub.add_parser("backtest-list", help="查询策略回测列表")
    backtest_list.add_argument("--user-id", required=True)
    backtest_list.add_argument("--strategy-id", required=True)
    backtest_list.add_argument("--status", default=None)
    backtest_list.add_argument("--page", type=int, default=1)
    backtest_list.add_argument("--page-size", type=int, default=20)

    backtest_stats = sub.add_parser("backtest-stats", help="查询策略回测统计")
    backtest_stats.add_argument("--user-id", required=True)
    backtest_stats.add_argument("--strategy-id", required=True)

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
    "update": _cmd_update,
    "create-from-template": _cmd_create_from_template,
    "validate-execution": _cmd_validate_execution,
    "backtest-create": _cmd_backtest_create,
    "backtest-list": _cmd_backtest_list,
    "backtest-stats": _cmd_backtest_stats,
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
