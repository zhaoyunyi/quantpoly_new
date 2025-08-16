"""trading_account CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from trading_account.domain import InvalidTradeOrderTransitionError
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import (
    AccountAccessDeniedError,
    InsufficientFundsError,
    LedgerTransactionError,
    OrderNotFoundError,
    PriceRefreshConflictError,
    TradingAccountService,
    TradingAdminRequiredError,
)

_repo = InMemoryTradingAccountRepository()
_service = TradingAccountService(repository=_repo)


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

    account_overview = sub.add_parser("account-overview", help="账户概览")
    account_overview.add_argument("--user-id", required=True)
    account_overview.add_argument("--account-id", required=True)

    return parser


_COMMANDS = {
    "account-list": _cmd_account_list,
    "account-aggregate": _cmd_account_aggregate,
    "position-summary": _cmd_position_summary,
    "trade-stats": _cmd_trade_stats,
    "risk-metrics": _cmd_risk_metrics,
    "equity-curve": _cmd_equity_curve,
    "position-analysis": _cmd_position_analysis,
    "pending-orders": _cmd_pending_orders,
    "refresh-prices": _cmd_refresh_prices,
    "order-create": _cmd_order_create,
    "order-list": _cmd_order_list,
    "order-fill": _cmd_order_fill,
    "order-cancel": _cmd_order_cancel,
    "trade-list": _cmd_trade_list,
    "cash-flow-list": _cmd_cash_flow_list,
    "deposit": _cmd_deposit,
    "withdraw": _cmd_withdraw,
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
