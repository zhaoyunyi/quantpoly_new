"""trading_account CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from uuid import uuid4

from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import IdempotencyConflictError, JobOrchestrationService
from trading_account.domain import InvalidTradeOrderTransitionError
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import (
    AccountAccessDeniedError,
    InsufficientFundsError,
    InsufficientPositionError,
    LedgerTransactionError,
    OrderNotFoundError,
    PriceRefreshConflictError,
    RiskAssessmentPendingError,
    RiskAssessmentUnavailableError,
    TradingAccountService,
    TradingAdminRequiredError,
)

_repo = InMemoryTradingAccountRepository()
_service = TradingAccountService(repository=_repo)
_job_service = JobOrchestrationService(repository=InMemoryJobRepository(), scheduler=InMemoryScheduler())


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _error(*, code: str, message: str) -> None:
    _output(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        }
    )


def _job_payload(job) -> dict:
    return {
        "taskId": job.id,
        "taskType": job.task_type,
        "status": job.status,
        "result": job.result,
        "error": {"code": job.error_code, "message": job.error_message}
        if job.error_code or job.error_message
        else None,
    }


def _dt(value: datetime) -> str:
    return value.isoformat()


def _parse_json_dict(text: str | None) -> dict:
    if not text:
        return {}
    return json.loads(text)


def _serialize_account(account) -> dict:
    return {
        "id": account.id,
        "userId": account.user_id,
        "accountName": account.account_name,
        "isActive": account.is_active,
        "createdAt": _dt(account.created_at),
    }


def _serialize_order(order) -> dict:
    return {
        "id": order.id,
        "userId": order.user_id,
        "accountId": order.account_id,
        "symbol": order.symbol,
        "side": order.side,
        "quantity": order.quantity,
        "price": order.price,
        "status": order.status,
        "createdAt": _dt(order.created_at),
        "updatedAt": _dt(order.updated_at),
    }


def _serialize_trade(trade) -> dict:
    return {
        "id": trade.id,
        "userId": trade.user_id,
        "accountId": trade.account_id,
        "orderId": trade.order_id,
        "symbol": trade.symbol,
        "side": trade.side,
        "quantity": trade.quantity,
        "price": trade.price,
        "createdAt": _dt(trade.created_at),
    }


def _serialize_cash_flow(flow) -> dict:
    return {
        "id": flow.id,
        "userId": flow.user_id,
        "accountId": flow.account_id,
        "amount": flow.amount,
        "flowType": flow.flow_type,
        "relatedTradeId": flow.related_trade_id,
        "createdAt": _dt(flow.created_at),
    }


def _serialize_position(position) -> dict:
    return {
        "id": position.id,
        "userId": position.user_id,
        "accountId": position.account_id,
        "symbol": position.symbol,
        "quantity": position.quantity,
        "avgPrice": position.avg_price,
        "lastPrice": position.last_price,
    }




def _trade_command_payload(result: dict) -> dict:
    return {
        "order": _serialize_order(result["order"]),
        "trade": _serialize_trade(result["trade"]),
        "cashFlow": _serialize_cash_flow(result["cashFlow"]),
        "position": _serialize_position(result["position"]),
    }

def _cmd_account_create(args: argparse.Namespace) -> None:
    created = _service.create_account(
        user_id=args.user_id,
        account_name=args.account_name,
        initial_capital=float(getattr(args, "initial_capital", 0.0) or 0.0),
    )
    _output({"success": True, "data": _serialize_account(created)})


def _cmd_account_get(args: argparse.Namespace) -> None:
    account = _service.get_account(user_id=args.user_id, account_id=args.account_id)
    if account is None:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    _output({"success": True, "data": _serialize_account(account)})


def _cmd_account_update(args: argparse.Namespace) -> None:
    account_name = getattr(args, "account_name", None)
    is_active = getattr(args, "is_active", None)

    if isinstance(is_active, str):
        lowered = is_active.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            is_active = True
        elif lowered in {"0", "false", "no", "off"}:
            is_active = False
        else:
            _error(code="INVALID_ARGUMENT", message="is_active must be true/false")
            return

    updated = _service.update_account(
        user_id=args.user_id,
        account_id=args.account_id,
        account_name=account_name,
        is_active=is_active,
    )
    if updated is None:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": _serialize_account(updated)})


def _cmd_account_filter_config(args: argparse.Namespace) -> None:
    config = _service.account_filter_config(user_id=args.user_id)
    _output({"success": True, "data": config})


def _cmd_account_summary(args: argparse.Namespace) -> None:
    try:
        summary = _service.account_summary(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except RiskAssessmentUnavailableError as exc:
        _error(code="RISK_ASSESSMENT_UNAVAILABLE", message=str(exc))
        return

    _output(
        {
            "success": True,
            "data": {
                "account": _serialize_account(summary["account"]),
                "positions": [
                    {
                        "id": item.id,
                        "userId": item.user_id,
                        "accountId": item.account_id,
                        "symbol": item.symbol,
                        "quantity": item.quantity,
                        "avgPrice": item.avg_price,
                        "lastPrice": item.last_price,
                    }
                    for item in summary["positions"]
                ],
                "positionCount": summary["positionCount"],
                "totalReturnRatio": summary["totalReturnRatio"],
                "stats": summary["stats"],
            },
        }
    )


def _cmd_cash_flow_summary(args: argparse.Namespace) -> None:
    try:
        summary = _service.cash_flow_summary(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": summary})


def _cmd_risk_assessment(args: argparse.Namespace) -> None:
    try:
        snapshot = _service.get_risk_assessment(user_id=args.user_id, account_id=args.account_id)
    except RiskAssessmentPendingError as exc:
        _error(code="RISK_ASSESSMENT_PENDING", message=str(exc))
        return
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except RiskAssessmentUnavailableError as exc:
        _error(code="RISK_ASSESSMENT_UNAVAILABLE", message=str(exc))
        return

    _output(
        {
            "success": True,
            "data": {
                "assessmentId": snapshot.id,
                "accountId": snapshot.account_id,
                "strategyId": snapshot.strategy_id,
                "riskScore": snapshot.risk_score,
                "riskLevel": snapshot.risk_level,
                "triggeredRuleIds": snapshot.triggered_rule_ids,
                "createdAt": snapshot.created_at.isoformat(),
            },
        }
    )


def _cmd_risk_assessment_evaluate(args: argparse.Namespace) -> None:
    try:
        snapshot = _service.evaluate_risk_assessment(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output(
        {
            "success": True,
            "data": {
                "assessmentId": snapshot.id,
                "accountId": snapshot.account_id,
                "strategyId": snapshot.strategy_id,
                "riskScore": snapshot.risk_score,
                "riskLevel": snapshot.risk_level,
                "triggeredRuleIds": snapshot.triggered_rule_ids,
                "createdAt": snapshot.created_at.isoformat(),
            },
        }
    )


def _cmd_account_list(args: argparse.Namespace) -> None:
    accounts = _service.list_accounts(user_id=args.user_id)
    _output({"success": True, "data": [_serialize_account(item) for item in accounts]})


def _cmd_account_aggregate(args: argparse.Namespace) -> None:
    aggregate = _service.user_account_aggregate(user_id=args.user_id)
    _output({"success": True, "data": aggregate})


def _cmd_position_summary(args: argparse.Namespace) -> None:
    try:
        summary = _service.position_summary(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": summary})


def _cmd_trade_stats(args: argparse.Namespace) -> None:
    try:
        stats = _service.trade_stats(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": stats})


def _cmd_risk_metrics(args: argparse.Namespace) -> None:
    try:
        metrics = _service.account_risk_metrics(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": metrics})


def _cmd_equity_curve(args: argparse.Namespace) -> None:
    try:
        curve = _service.account_equity_curve(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": curve})


def _cmd_position_analysis(args: argparse.Namespace) -> None:
    try:
        analysis = _service.account_position_analysis(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": analysis})


def _cmd_pending_orders(args: argparse.Namespace) -> None:
    try:
        orders = _service.list_pending_orders(
            user_id=args.user_id,
            is_admin=args.is_admin,
            admin_decision_source="is_admin" if args.is_admin else "none",
            account_id=args.account_id,
        )
    except TradingAdminRequiredError:
        _error(code="ADMIN_REQUIRED", message="admin role required")
        return

    _output({"success": True, "data": [_serialize_order(item) for item in orders]})


def _cmd_refresh_prices(args: argparse.Namespace) -> None:
    try:
        price_updates = _parse_json_dict(args.price_updates)
    except json.JSONDecodeError:
        _error(code="INVALID_ARGUMENT", message="invalid price updates json")
        return

    try:
        result = _service.refresh_market_prices(
            user_id=args.user_id,
            is_admin=args.is_admin,
            admin_decision_source="is_admin" if args.is_admin else "none",
            price_updates=price_updates,
            idempotency_key=args.idempotency_key,
            confirmation_token=args.confirmation_token,
            account_id=getattr(args, "account_id", None),
        )
    except TradingAdminRequiredError:
        _error(code="ADMIN_REQUIRED", message="admin role required")
        return
    except PriceRefreshConflictError:
        _error(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        return
    except ValueError as exc:
        _error(code="INVALID_ARGUMENT", message=str(exc))
        return

    _output({"success": True, "data": result})


def _cmd_ops_pending_process_task(args: argparse.Namespace) -> None:
    if not args.is_admin:
        _error(code="ADMIN_REQUIRED", message="admin role required")
        return

    job_idempotency_key = args.idempotency_key or f"trading-pending-process-cli:{args.user_id}:{args.max_trades}:{uuid4()}"

    audit_id = getattr(args, "audit_id", None) or "cli"

    try:
        job = _job_service.submit_job(
            user_id=args.user_id,
            task_type="trading_pending_process",
            payload={"maxTrades": args.max_trades},
            idempotency_key=job_idempotency_key,
        )
        _job_service.start_job(user_id=args.user_id, job_id=job.id)
        result = _service.process_pending_trades(
            user_id=args.user_id,
            is_admin=args.is_admin,
            admin_decision_source="is_admin" if args.is_admin else "none",
            max_trades=args.max_trades,
            idempotency_key=args.idempotency_key,
            confirmation_token=getattr(args, "confirmation_token", None),
            audit_id=audit_id,
        )
        job = _job_service.succeed_job(user_id=args.user_id, job_id=job.id, result=result)
    except IdempotencyConflictError:
        _error(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        return
    except TradingAdminRequiredError:
        _error(code="ADMIN_REQUIRED", message="admin role required")
        return
    except ValueError as exc:
        _error(code="INVALID_ARGUMENT", message=str(exc))
        return
    except Exception as exc:  # noqa: BLE001
        _error(code="TASK_EXECUTION_FAILED", message=str(exc))
        return

    _output({"success": True, "data": _job_payload(job)})


def _cmd_ops_daily_stats_task(args: argparse.Namespace) -> None:
    if not args.is_admin:
        _error(code="ADMIN_REQUIRED", message="admin role required")
        return

    job_idempotency_key = args.idempotency_key or f"trading-daily-stats-cli:{args.user_id}:{args.target_date}:{uuid4()}"

    audit_id = getattr(args, "audit_id", None) or "cli"

    try:
        job = _job_service.submit_job(
            user_id=args.user_id,
            task_type="trading_daily_stats_calculate",
            payload={"accountIds": args.account_ids, "targetDate": args.target_date},
            idempotency_key=job_idempotency_key,
        )
        _job_service.start_job(user_id=args.user_id, job_id=job.id)
        result = _service.calculate_daily_stats(
            user_id=args.user_id,
            is_admin=args.is_admin,
            admin_decision_source="is_admin" if args.is_admin else "none",
            account_ids=args.account_ids,
            target_date=args.target_date,
            idempotency_key=args.idempotency_key,
            confirmation_token=getattr(args, "confirmation_token", None),
            audit_id=audit_id,
        )
        job = _job_service.succeed_job(user_id=args.user_id, job_id=job.id, result=result)
    except IdempotencyConflictError:
        _error(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        return
    except TradingAdminRequiredError:
        _error(code="ADMIN_REQUIRED", message="admin role required")
        return
    except ValueError as exc:
        _error(code="INVALID_ARGUMENT", message=str(exc))
        return
    except Exception as exc:  # noqa: BLE001
        _error(code="TASK_EXECUTION_FAILED", message=str(exc))
        return

    _output({"success": True, "data": _job_payload(job)})


def _cmd_stats_daily_get(args: argparse.Namespace) -> None:
    try:
        stats = _service.get_daily_stats(user_id=args.user_id, date=args.date, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    if stats is None:
        _error(code="NOT_FOUND", message="daily stats not found")
        return

    _output({"success": True, "data": {"date": args.date, "items": [stats]}})


def _cmd_ops_account_cleanup_task(args: argparse.Namespace) -> None:
    if not args.is_admin:
        _error(code="ADMIN_REQUIRED", message="admin role required")
        return

    job_idempotency_key = (
        args.idempotency_key
        or f"trading-account-cleanup-cli:{args.user_id}:{args.days_threshold}:{uuid4()}"
    )

    audit_id = getattr(args, "audit_id", None) or "cli"

    try:
        job = _job_service.submit_job(
            user_id=args.user_id,
            task_type="trading_account_cleanup",
            payload={"accountIds": args.account_ids, "daysThreshold": args.days_threshold},
            idempotency_key=job_idempotency_key,
        )
        _job_service.start_job(user_id=args.user_id, job_id=job.id)
        result = _service.cleanup_account_history(
            user_id=args.user_id,
            is_admin=args.is_admin,
            admin_decision_source="is_admin" if args.is_admin else "none",
            account_ids=args.account_ids,
            days_threshold=args.days_threshold,
            idempotency_key=args.idempotency_key,
            confirmation_token=getattr(args, "confirmation_token", None),
            audit_id=audit_id,
        )
        job = _job_service.succeed_job(user_id=args.user_id, job_id=job.id, result=result)
    except IdempotencyConflictError:
        _error(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        return
    except TradingAdminRequiredError:
        _error(code="ADMIN_REQUIRED", message="admin role required")
        return
    except ValueError as exc:
        _error(code="INVALID_ARGUMENT", message=str(exc))
        return
    except Exception as exc:  # noqa: BLE001
        _error(code="TASK_EXECUTION_FAILED", message=str(exc))
        return

    _output({"success": True, "data": _job_payload(job)})




def _cmd_buy(args: argparse.Namespace) -> None:
    try:
        result = _service.execute_buy_command(
            user_id=args.user_id,
            account_id=args.account_id,
            symbol=args.symbol,
            quantity=args.quantity,
            price=args.price,
        )
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except InsufficientFundsError:
        _error(code="INSUFFICIENT_FUNDS", message="insufficient funds")
        return
    except ValueError as exc:
        _error(code="INVALID_ARGUMENT", message=str(exc))
        return
    except LedgerTransactionError:
        _error(code="LEDGER_TRANSACTION_FAILED", message="ledger transaction failed")
        return

    _output({"success": True, "data": _trade_command_payload(result)})


def _cmd_sell(args: argparse.Namespace) -> None:
    try:
        result = _service.execute_sell_command(
            user_id=args.user_id,
            account_id=args.account_id,
            symbol=args.symbol,
            quantity=args.quantity,
            price=args.price,
        )
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except InsufficientPositionError:
        _error(code="INSUFFICIENT_POSITION", message="insufficient position")
        return
    except ValueError as exc:
        _error(code="INVALID_ARGUMENT", message=str(exc))
        return
    except LedgerTransactionError:
        _error(code="LEDGER_TRANSACTION_FAILED", message="ledger transaction failed")
        return

    _output({"success": True, "data": _trade_command_payload(result)})

def _cmd_order_create(args: argparse.Namespace) -> None:
    try:
        order = _service.submit_order(
            user_id=args.user_id,
            account_id=args.account_id,
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            price=args.price,
        )
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": _serialize_order(order)})


def _cmd_order_list(args: argparse.Namespace) -> None:
    try:
        orders = _service.list_orders(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": [_serialize_order(item) for item in orders]})


def _cmd_order_fill(args: argparse.Namespace) -> None:
    try:
        order = _service.fill_order(
            user_id=args.user_id,
            account_id=args.account_id,
            order_id=args.order_id,
        )
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except OrderNotFoundError:
        _error(code="ORDER_NOT_FOUND", message="order not found")
        return
    except InvalidTradeOrderTransitionError:
        _error(code="ORDER_INVALID_TRANSITION", message="order state transition is invalid")
        return
    except LedgerTransactionError:
        _error(code="LEDGER_TRANSACTION_FAILED", message="ledger transaction failed")
        return

    _output({"success": True, "data": _serialize_order(order)})


def _cmd_order_cancel(args: argparse.Namespace) -> None:
    try:
        order = _service.cancel_order(
            user_id=args.user_id,
            account_id=args.account_id,
            order_id=args.order_id,
        )
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except OrderNotFoundError:
        _error(code="ORDER_NOT_FOUND", message="order not found")
        return
    except InvalidTradeOrderTransitionError:
        _error(code="ORDER_INVALID_TRANSITION", message="order state transition is invalid")
        return

    _output({"success": True, "data": _serialize_order(order)})


def _cmd_order_update(args: argparse.Namespace) -> None:
    try:
        order = _service.update_order(
            user_id=args.user_id,
            account_id=args.account_id,
            order_id=args.order_id,
            quantity=args.quantity,
            price=args.price,
        )
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except OrderNotFoundError:
        _error(code="ORDER_NOT_FOUND", message="order not found")
        return
    except InvalidTradeOrderTransitionError:
        _error(code="ORDER_INVALID_TRANSITION", message="order state transition is invalid")
        return
    except ValueError as exc:
        _error(code="INVALID_ARGUMENT", message=str(exc))
        return

    _output({"success": True, "data": _serialize_order(order)})


def _cmd_order_delete(args: argparse.Namespace) -> None:
    try:
        order = _service.delete_order(
            user_id=args.user_id,
            account_id=args.account_id,
            order_id=args.order_id,
        )
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except OrderNotFoundError:
        _error(code="ORDER_NOT_FOUND", message="order not found")
        return
    except InvalidTradeOrderTransitionError:
        _error(code="ORDER_INVALID_TRANSITION", message="order state transition is invalid")
        return

    _output({"success": True, "data": _serialize_order(order)})


def _cmd_trade_pending(args: argparse.Namespace) -> None:
    try:
        orders = _service.list_pending_trades(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": [_serialize_order(item) for item in orders]})


def _cmd_position_get(args: argparse.Namespace) -> None:
    try:
        position = _service.get_position_by_symbol(
            user_id=args.user_id,
            account_id=args.account_id,
            symbol=args.symbol,
        )
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    if position is None:
        _error(code="POSITION_NOT_FOUND", message="position not found")
        return

    _output({"success": True, "data": _serialize_position(position)})


def _cmd_trade_list(args: argparse.Namespace) -> None:
    try:
        trades = _service.list_trades(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": [_serialize_trade(item) for item in trades]})


def _cmd_cash_flow_list(args: argparse.Namespace) -> None:
    try:
        flows = _service.list_cash_flows(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": [_serialize_cash_flow(item) for item in flows]})


def _cmd_deposit(args: argparse.Namespace) -> None:
    try:
        flow = _service.deposit(user_id=args.user_id, account_id=args.account_id, amount=args.amount)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except ValueError:
        _error(code="INVALID_ARGUMENT", message="amount must be positive")
        return

    _output({"success": True, "data": _serialize_cash_flow(flow)})


def _cmd_withdraw(args: argparse.Namespace) -> None:
    try:
        flow = _service.withdraw(user_id=args.user_id, account_id=args.account_id, amount=args.amount)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return
    except InsufficientFundsError:
        _error(code="INSUFFICIENT_FUNDS", message="insufficient funds")
        return
    except ValueError:
        _error(code="INVALID_ARGUMENT", message="amount must be positive")
        return

    _output({"success": True, "data": _serialize_cash_flow(flow)})


def _cmd_account_overview(args: argparse.Namespace) -> None:
    try:
        overview = _service.account_overview(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _error(code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")
        return

    _output({"success": True, "data": overview})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading-account", description="QuantPoly 交易账户 CLI")
    sub = parser.add_subparsers(dest="command")

    account_create = sub.add_parser("account-create", help="创建交易账户")
    account_create.add_argument("--user-id", required=True)
    account_create.add_argument("--account-name", required=True)
    account_create.add_argument("--initial-capital", type=float, default=0.0)

    account_get = sub.add_parser("account-get", help="查询交易账户详情")
    account_get.add_argument("--user-id", required=True)
    account_get.add_argument("--account-id", required=True)

    account_update = sub.add_parser("account-update", help="更新交易账户")
    account_update.add_argument("--user-id", required=True)
    account_update.add_argument("--account-id", required=True)
    account_update.add_argument("--account-name", default=None)
    account_update.add_argument("--is-active", default=None)

    account_filter_config = sub.add_parser("account-filter-config", help="查询账户筛选配置")
    account_filter_config.add_argument("--user-id", required=True)

    account_list = sub.add_parser("account-list", help="查询用户账户列表")
    account_list.add_argument("--user-id", required=True)

    account_aggregate = sub.add_parser("account-aggregate", help="查询用户账户聚合统计")
    account_aggregate.add_argument("--user-id", required=True)

    position_summary = sub.add_parser("position-summary", help="查询账户持仓分析")
    position_summary.add_argument("--user-id", required=True)
    position_summary.add_argument("--account-id", required=True)

    trade_stats = sub.add_parser("trade-stats", help="查询账户交易统计")
    trade_stats.add_argument("--user-id", required=True)
    trade_stats.add_argument("--account-id", required=True)

    risk_metrics = sub.add_parser("risk-metrics", help="查询账户风险指标")
    risk_metrics.add_argument("--user-id", required=True)
    risk_metrics.add_argument("--account-id", required=True)

    equity_curve = sub.add_parser("equity-curve", help="查询账户权益曲线")
    equity_curve.add_argument("--user-id", required=True)
    equity_curve.add_argument("--account-id", required=True)

    position_analysis = sub.add_parser("position-analysis", help="查询账户仓位分析")
    position_analysis.add_argument("--user-id", required=True)
    position_analysis.add_argument("--account-id", required=True)

    pending_orders = sub.add_parser("pending-orders", help="查询待处理交易（管理员）")
    pending_orders.add_argument("--user-id", required=True)
    pending_orders.add_argument("--is-admin", action="store_true")
    pending_orders.add_argument("--account-id", default=None)

    refresh_prices = sub.add_parser("refresh-prices", help="批量刷新价格（管理员）")
    refresh_prices.add_argument("--user-id", required=True)
    refresh_prices.add_argument("--is-admin", action="store_true")
    refresh_prices.add_argument("--price-updates", required=True)
    refresh_prices.add_argument("--idempotency-key", default=None)
    refresh_prices.add_argument("--confirmation-token", default=None)
    refresh_prices.add_argument("--account-id", default=None)

    ops_pending_process = sub.add_parser("ops-pending-process-task", help="待处理交易处理任务（管理员）")
    ops_pending_process.add_argument("--user-id", required=True)
    ops_pending_process.add_argument("--is-admin", action="store_true")
    ops_pending_process.add_argument("--max-trades", type=int, default=100)
    ops_pending_process.add_argument("--idempotency-key", default=None)
    ops_pending_process.add_argument("--audit-id", default="cli")

    ops_daily_stats = sub.add_parser("ops-daily-stats-task", help="生成交易日统计任务（管理员）")
    ops_daily_stats.add_argument("--user-id", required=True)
    ops_daily_stats.add_argument("--is-admin", action="store_true")
    ops_daily_stats.add_argument("--account-id", action="append", dest="account_ids", default=[])
    ops_daily_stats.add_argument("--target-date", required=True)
    ops_daily_stats.add_argument("--idempotency-key", default=None)
    ops_daily_stats.add_argument("--audit-id", default="cli")

    stats_daily_get = sub.add_parser("stats-daily-get", help="读取交易日统计")
    stats_daily_get.add_argument("--user-id", required=True)
    stats_daily_get.add_argument("--date", required=True)
    stats_daily_get.add_argument("--account-id", required=True)

    ops_account_cleanup = sub.add_parser("ops-account-cleanup-task", help="账户清理任务（管理员）")
    ops_account_cleanup.add_argument("--user-id", required=True)
    ops_account_cleanup.add_argument("--is-admin", action="store_true")
    ops_account_cleanup.add_argument("--account-id", action="append", dest="account_ids", default=[])
    ops_account_cleanup.add_argument("--days-threshold", type=int, default=90)
    ops_account_cleanup.add_argument("--idempotency-key", default=None)
    ops_account_cleanup.add_argument("--audit-id", default="cli")


    buy = sub.add_parser("buy", help="业务买入指令")
    buy.add_argument("--user-id", required=True)
    buy.add_argument("--account-id", required=True)
    buy.add_argument("--symbol", required=True)
    buy.add_argument("--quantity", required=True, type=float)
    buy.add_argument("--price", required=True, type=float)

    sell = sub.add_parser("sell", help="业务卖出指令")
    sell.add_argument("--user-id", required=True)
    sell.add_argument("--account-id", required=True)
    sell.add_argument("--symbol", required=True)
    sell.add_argument("--quantity", required=True, type=float)
    sell.add_argument("--price", required=True, type=float)

    order_create = sub.add_parser("order-create", help="创建订单")
    order_create.add_argument("--user-id", required=True)
    order_create.add_argument("--account-id", required=True)
    order_create.add_argument("--symbol", required=True)
    order_create.add_argument("--side", required=True)
    order_create.add_argument("--quantity", required=True, type=float)
    order_create.add_argument("--price", required=True, type=float)

    order_list = sub.add_parser("order-list", help="查询订单列表")
    order_list.add_argument("--user-id", required=True)
    order_list.add_argument("--account-id", required=True)

    order_fill = sub.add_parser("order-fill", help="成交订单")
    order_fill.add_argument("--user-id", required=True)
    order_fill.add_argument("--account-id", required=True)
    order_fill.add_argument("--order-id", required=True)

    order_cancel = sub.add_parser("order-cancel", help="撤销订单")
    order_cancel.add_argument("--user-id", required=True)
    order_cancel.add_argument("--account-id", required=True)
    order_cancel.add_argument("--order-id", required=True)

    order_update = sub.add_parser("order-update", help="更新订单")
    order_update.add_argument("--user-id", required=True)
    order_update.add_argument("--account-id", required=True)
    order_update.add_argument("--order-id", required=True)
    order_update.add_argument("--quantity", type=float, default=None)
    order_update.add_argument("--price", type=float, default=None)

    order_delete = sub.add_parser("order-delete", help="删除订单（撤单）")
    order_delete.add_argument("--user-id", required=True)
    order_delete.add_argument("--account-id", required=True)
    order_delete.add_argument("--order-id", required=True)

    trade_pending = sub.add_parser("trade-pending", help="查询待处理交易")
    trade_pending.add_argument("--user-id", required=True)
    trade_pending.add_argument("--account-id", required=True)

    position_get = sub.add_parser("position-get", help="按标的查询仓位")
    position_get.add_argument("--user-id", required=True)
    position_get.add_argument("--account-id", required=True)
    position_get.add_argument("--symbol", required=True)

    trade_list = sub.add_parser("trade-list", help="查询成交列表")
    trade_list.add_argument("--user-id", required=True)
    trade_list.add_argument("--account-id", required=True)

    cash_flow_list = sub.add_parser("cash-flow-list", help="查询资金流水")
    cash_flow_list.add_argument("--user-id", required=True)
    cash_flow_list.add_argument("--account-id", required=True)

    deposit = sub.add_parser("deposit", help="账户入金")
    deposit.add_argument("--user-id", required=True)
    deposit.add_argument("--account-id", required=True)
    deposit.add_argument("--amount", required=True, type=float)

    withdraw = sub.add_parser("withdraw", help="账户出金")
    withdraw.add_argument("--user-id", required=True)
    withdraw.add_argument("--account-id", required=True)
    withdraw.add_argument("--amount", required=True, type=float)

    account_summary = sub.add_parser("account-summary", help="账户摘要")
    account_summary.add_argument("--user-id", required=True)
    account_summary.add_argument("--account-id", required=True)

    cash_flow_summary = sub.add_parser("cash-flow-summary", help="资金流水摘要")
    cash_flow_summary.add_argument("--user-id", required=True)
    cash_flow_summary.add_argument("--account-id", required=True)

    risk_assessment = sub.add_parser("risk-assessment", help="查询账户风险评估")
    risk_assessment.add_argument("--user-id", required=True)
    risk_assessment.add_argument("--account-id", required=True)

    risk_assessment_evaluate = sub.add_parser("risk-assessment-evaluate", help="触发账户风险评估")
    risk_assessment_evaluate.add_argument("--user-id", required=True)
    risk_assessment_evaluate.add_argument("--account-id", required=True)

    account_overview = sub.add_parser("account-overview", help="账户概览")
    account_overview.add_argument("--user-id", required=True)
    account_overview.add_argument("--account-id", required=True)

    return parser


_COMMANDS = {
    "account-create": _cmd_account_create,
    "account-get": _cmd_account_get,
    "account-update": _cmd_account_update,
    "account-filter-config": _cmd_account_filter_config,
    "account-list": _cmd_account_list,
    "account-aggregate": _cmd_account_aggregate,
    "position-summary": _cmd_position_summary,
    "trade-stats": _cmd_trade_stats,
    "risk-metrics": _cmd_risk_metrics,
    "equity-curve": _cmd_equity_curve,
    "position-analysis": _cmd_position_analysis,
    "pending-orders": _cmd_pending_orders,
    "refresh-prices": _cmd_refresh_prices,
    "ops-pending-process-task": _cmd_ops_pending_process_task,
    "ops-daily-stats-task": _cmd_ops_daily_stats_task,
    "stats-daily-get": _cmd_stats_daily_get,
    "ops-account-cleanup-task": _cmd_ops_account_cleanup_task,
    "buy": _cmd_buy,
    "sell": _cmd_sell,
    "order-create": _cmd_order_create,
    "order-list": _cmd_order_list,
    "order-fill": _cmd_order_fill,
    "order-cancel": _cmd_order_cancel,
    "order-update": _cmd_order_update,
    "order-delete": _cmd_order_delete,
    "trade-pending": _cmd_trade_pending,
    "position-get": _cmd_position_get,
    "trade-list": _cmd_trade_list,
    "cash-flow-list": _cmd_cash_flow_list,
    "deposit": _cmd_deposit,
    "withdraw": _cmd_withdraw,
    "account-summary": _cmd_account_summary,
    "cash-flow-summary": _cmd_cash_flow_summary,
    "risk-assessment": _cmd_risk_assessment,
    "risk-assessment-evaluate": _cmd_risk_assessment_evaluate,
    "account-overview": _cmd_account_overview,
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
