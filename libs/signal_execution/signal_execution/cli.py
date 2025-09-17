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


def _signal_payload(signal) -> dict:
    return {
        "id": signal.id,
        "userId": signal.user_id,
        "strategyId": signal.strategy_id,
        "accountId": signal.account_id,
        "symbol": signal.symbol,
        "side": signal.side,
        "status": signal.status,
        "createdAt": _dt(signal.created_at),
        "updatedAt": _dt(signal.updated_at),
        "expiresAt": _dt(signal.expires_at),
        "metadata": dict(signal.metadata),
    }


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


def _cmd_templates(args: argparse.Namespace) -> None:
    data = _service.list_execution_templates(strategy_type=args.strategy_type)
    _output({"success": True, "data": data})


def _cmd_strategy_statistics(args: argparse.Namespace) -> None:
    try:
        data = _service.strategy_execution_statistics(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
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

    _output({"success": True, "data": data})


def _cmd_strategy_trend(args: argparse.Namespace) -> None:
    try:
        data = _service.strategy_execution_trend(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            days=args.days,
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
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_DAYS", "message": str(exc)}})
        return

    _output({"success": True, "data": data})


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
            admin_decision_source="is_admin" if args.is_admin else "none",
            confirmation_token=getattr(args, "confirmation_token", None),
        )
    except AdminRequiredError:
        _output({"success": False, "error": {"code": "ADMIN_REQUIRED", "message": "admin role required"}})
        return

    _output({"success": True, "data": {"deleted": deleted}})


def _cmd_cleanup_executions(args: argparse.Namespace) -> None:
    try:
        deleted = _service.cleanup_execution_history(
            user_id=args.user_id,
            is_admin=args.is_admin,
            retention_days=args.retention_days,
            admin_decision_source="is_admin" if args.is_admin else "none",
            confirmation_token=getattr(args, "confirmation_token", None),
            audit_id=getattr(args, "audit_id", "cli"),
        )
    except AdminRequiredError:
        _output({"success": False, "error": {"code": "ADMIN_REQUIRED", "message": "admin role required"}})
        return
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_ARGUMENT", "message": str(exc)}})
        return

    _output(
        {
            "success": True,
            "data": {
                "deleted": deleted,
                "retentionDays": args.retention_days,
                "auditId": getattr(args, "audit_id", "cli"),
            },
        }
    )


def _cmd_signal_get(args: argparse.Namespace) -> None:
    try:
        signal = _service.get_signal_detail(user_id=args.user_id, signal_id=args.signal_id)
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

    _output({"success": True, "data": _signal_payload(signal)})


def _cmd_pending(args: argparse.Namespace) -> None:
    items = _service.list_pending_signals(user_id=args.user_id)
    _output({"success": True, "data": [_signal_payload(item) for item in items]})


def _cmd_expired(args: argparse.Namespace) -> None:
    items = _service.list_expired_signals(user_id=args.user_id)
    _output({"success": True, "data": [_signal_payload(item) for item in items]})


def _cmd_search(args: argparse.Namespace) -> None:
    items = _service.search_signals(
        user_id=args.user_id,
        keyword=args.keyword,
        strategy_id=args.strategy_id,
        account_id=args.account_id,
        symbol=args.symbol,
        status=args.status,
    )
    _output({"success": True, "data": [_signal_payload(item) for item in items]})


def _cmd_dashboard(args: argparse.Namespace) -> None:
    data = _service.signal_dashboard(
        user_id=args.user_id,
        keyword=args.keyword,
        strategy_id=args.strategy_id,
        account_id=args.account_id,
        symbol=args.symbol,
    )
    _output({"success": True, "data": data})


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


def _cmd_expire(args: argparse.Namespace) -> None:
    try:
        signal = _service.expire_signal(user_id=args.user_id, signal_id=args.signal_id)
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

    _output({"success": True, "data": _signal_payload(signal)})


def _cmd_account_statistics(args: argparse.Namespace) -> None:
    try:
        stats = _service.account_statistics(user_id=args.user_id, account_id=args.account_id)
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

    _output({"success": True, "data": stats})


def _cmd_generate(args: argparse.Namespace) -> None:
    try:
        symbols = _parse_csv(args.symbols)
    except Exception:  # noqa: BLE001
        _output({"success": False, "error": {"code": "INVALID_SYMBOLS", "message": "invalid symbols"}})
        return

    try:
        signals = _service.generate_signals(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            account_id=args.account_id,
            symbols=symbols,
            side=args.side,
            parameters=_parse_json(args.parameters),
            expires_at=None,
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

    _output({"success": True, "data": {"signals": [_signal_payload(item) for item in signals]}})


def _cmd_generate_by_strategy(args: argparse.Namespace) -> None:
    try:
        symbols = _parse_csv(args.symbols)
    except Exception:  # noqa: BLE001
        _output({"success": False, "error": {"code": "INVALID_SYMBOLS", "message": "invalid symbols"}})
        return

    try:
        result = _service.generate_signals_by_strategy(
            user_id=args.user_id,
            strategy_id=args.strategy_id,
            account_id=args.account_id,
            symbols=symbols,
            timeframe=args.timeframe,
            expires_at=None,
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

    payload = {
        "strategyId": result["strategyId"],
        "accountId": result["accountId"],
        "template": result["template"],
        "signals": [_signal_payload(item) for item in result["signals"]],
        "skipped": result["skipped"],
    }
    _output({"success": True, "data": payload})


def _cmd_process(args: argparse.Namespace) -> None:
    try:
        signal, risk = _service.process_signal(user_id=args.user_id, signal_id=args.signal_id)
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

    payload = {"id": signal.id, "status": signal.status, "risk": risk}
    _output({"success": True, "data": payload})


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


def _cmd_daily_trend(args: argparse.Namespace) -> None:
    try:
        data = _service.daily_trend(user_id=args.user_id, days=args.days)
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_DAYS", "message": str(exc)}})
        return

    _output({"success": True, "data": data})


def _cmd_signal_performance(args: argparse.Namespace) -> None:
    try:
        data = _service.signal_performance(user_id=args.user_id, signal_id=args.signal_id)
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

    _output({"success": True, "data": data})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="signal-execution", description="QuantPoly 信号执行 CLI")
    sub = parser.add_subparsers(dest="command")

    trend = sub.add_parser("trend", help="查询执行趋势")
    trend.add_argument("--user-id", required=True)

    templates = sub.add_parser("templates", help="按策略类型查询执行模板")
    templates.add_argument("--strategy-type", default=None)

    strategy_statistics = sub.add_parser("strategy-statistics", help="按策略查询执行统计")
    strategy_statistics.add_argument("--user-id", required=True)
    strategy_statistics.add_argument("--strategy-id", required=True)

    strategy_trend = sub.add_parser("strategy-trend", help="按策略查询执行趋势")
    strategy_trend.add_argument("--user-id", required=True)
    strategy_trend.add_argument("--strategy-id", required=True)
    strategy_trend.add_argument("--days", type=int, default=7)

    validate_parameters = sub.add_parser("validate-parameters", help="执行前参数校验")
    validate_parameters.add_argument("--user-id", required=True)
    validate_parameters.add_argument("--strategy-id", required=True)
    validate_parameters.add_argument("--account-id", required=True)
    validate_parameters.add_argument("--parameters", default="{}")

    cleanup_all = sub.add_parser("cleanup-all", help="全局清理（管理员）")
    cleanup_all.add_argument("--user-id", required=True)
    cleanup_all.add_argument("--is-admin", action="store_true")
    cleanup_all.add_argument("--confirmation-token", default=None)

    cleanup_executions = sub.add_parser("cleanup-executions", help="清理执行历史（管理员）")
    cleanup_executions.add_argument("--user-id", required=True)
    cleanup_executions.add_argument("--is-admin", action="store_true")
    cleanup_executions.add_argument("--retention-days", type=int, required=True)
    cleanup_executions.add_argument("--confirmation-token", default=None)
    cleanup_executions.add_argument("--audit-id", default="cli")

    signal_get = sub.add_parser("signal-get", help="信号详情")
    signal_get.add_argument("--user-id", required=True)
    signal_get.add_argument("--signal-id", required=True)

    pending = sub.add_parser("pending", help="待处理信号")
    pending.add_argument("--user-id", required=True)

    expired = sub.add_parser("expired", help="已过期信号")
    expired.add_argument("--user-id", required=True)

    search = sub.add_parser("search", help="信号高级搜索")
    search.add_argument("--user-id", required=True)
    search.add_argument("--keyword", default=None)
    search.add_argument("--strategy-id", default=None)
    search.add_argument("--account-id", default=None)
    search.add_argument("--symbol", default=None)
    search.add_argument("--status", default=None)

    dashboard = sub.add_parser("dashboard", help="信号账户仪表板")
    dashboard.add_argument("--user-id", required=True)
    dashboard.add_argument("--keyword", default=None)
    dashboard.add_argument("--strategy-id", default=None)
    dashboard.add_argument("--account-id", default=None)
    dashboard.add_argument("--symbol", default=None)

    execute = sub.add_parser("execute", help="执行信号")
    execute.add_argument("--user-id", required=True)
    execute.add_argument("--signal-id", required=True)

    expire = sub.add_parser("expire", help="手动过期信号")
    expire.add_argument("--user-id", required=True)
    expire.add_argument("--signal-id", required=True)

    account_statistics = sub.add_parser("account-statistics", help="账户维度信号统计")
    account_statistics.add_argument("--user-id", required=True)
    account_statistics.add_argument("--account-id", required=True)

    generate = sub.add_parser("generate", help="策略触发生成信号")
    generate.add_argument("--user-id", required=True)
    generate.add_argument("--strategy-id", required=True)
    generate.add_argument("--account-id", required=True)
    generate.add_argument("--symbols", required=True, help="CSV 符号列表")
    generate.add_argument("--side", default="BUY")
    generate.add_argument("--parameters", default="{}")

    generate_by_strategy = sub.add_parser("generate-by-strategy", help="按策略模板与行情自动生成信号")
    generate_by_strategy.add_argument("--user-id", required=True)
    generate_by_strategy.add_argument("--strategy-id", required=True)
    generate_by_strategy.add_argument("--account-id", required=True)
    generate_by_strategy.add_argument("--symbols", required=True, help="CSV 符号列表")
    generate_by_strategy.add_argument("--timeframe", default="1Day")

    process = sub.add_parser("process", help="处理单条信号（含风控前置）")
    process.add_argument("--user-id", required=True)
    process.add_argument("--signal-id", required=True)

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

    daily_trend = sub.add_parser("daily-trend", help="按天趋势")
    daily_trend.add_argument("--user-id", required=True)
    daily_trend.add_argument("--days", type=int, default=7)

    signal_performance = sub.add_parser("signal-performance", help="单信号绩效")
    signal_performance.add_argument("--user-id", required=True)
    signal_performance.add_argument("--signal-id", required=True)

    return parser


_COMMANDS = {
    "trend": _cmd_trend,
    "templates": _cmd_templates,
    "strategy-statistics": _cmd_strategy_statistics,
    "strategy-trend": _cmd_strategy_trend,
    "validate-parameters": _cmd_validate_parameters,
    "cleanup-all": _cmd_cleanup_all,
    "cleanup-executions": _cmd_cleanup_executions,
    "signal-get": _cmd_signal_get,
    "pending": _cmd_pending,
    "expired": _cmd_expired,
    "search": _cmd_search,
    "dashboard": _cmd_dashboard,
    "execute": _cmd_execute,
    "expire": _cmd_expire,
    "account-statistics": _cmd_account_statistics,
    "generate": _cmd_generate,
    "generate-by-strategy": _cmd_generate_by_strategy,
    "process": _cmd_process,
    "batch-execute": _cmd_batch_execute,
    "batch-cancel": _cmd_batch_cancel,
    "execution-detail": _cmd_execution_detail,
    "running": _cmd_running,
    "performance": _cmd_performance,
    "daily-trend": _cmd_daily_trend,
    "signal-performance": _cmd_signal_performance,
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
