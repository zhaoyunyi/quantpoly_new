"""trading_account FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from platform_core.authz import resolve_admin_decision
from platform_core.response import error_response, success_response
from trading_account.domain import InvalidTradeOrderTransitionError
from trading_account.service import (
    AccountAccessDeniedError,
    InsufficientFundsError,
    LedgerTransactionError,
    OrderNotFoundError,
    PriceRefreshConflictError,
    TradeNotFoundError,
    TradingAccountService,
    TradingAdminRequiredError,
)


def _dt(value: datetime) -> str:
    return value.isoformat()


def _error(*, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_response(code=code, message=message),
    )


def _account_to_payload(account) -> dict[str, Any]:
    return {
        "id": account.id,
        "userId": account.user_id,
        "accountName": account.account_name,
        "isActive": account.is_active,
        "createdAt": _dt(account.created_at),
    }


def _position_to_payload(position) -> dict[str, Any]:
    return {
        "id": position.id,
        "userId": position.user_id,
        "accountId": position.account_id,
        "symbol": position.symbol,
        "quantity": position.quantity,
        "avgPrice": position.avg_price,
        "lastPrice": position.last_price,
    }


def _order_to_payload(order) -> dict[str, Any]:
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


def _trade_to_payload(trade) -> dict[str, Any]:
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


def _cash_flow_to_payload(flow) -> dict[str, Any]:
    return {
        "id": flow.id,
        "userId": flow.user_id,
        "accountId": flow.account_id,
        "amount": flow.amount,
        "flowType": flow.flow_type,
        "relatedTradeId": flow.related_trade_id,
        "createdAt": _dt(flow.created_at),
    }


class OrderCreateRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float


class AmountRequest(BaseModel):
    amount: float


class RefreshPricesRequest(BaseModel):
    price_updates: dict[str, float] = Field(alias="priceUpdates")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")
    account_id: str | None = Field(default=None, alias="accountId")

    model_config = {"populate_by_name": True}


def create_router(*, service: TradingAccountService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/trading/accounts")
    def list_accounts(current_user=Depends(get_current_user)):
        accounts = service.list_accounts(user_id=current_user.id)
        return success_response(data=[_account_to_payload(item) for item in accounts])

    @router.get("/trading/accounts/aggregate")
    def account_aggregate(current_user=Depends(get_current_user)):
        data = service.user_account_aggregate(user_id=current_user.id)
        return success_response(data=data)

    @router.get("/trading/accounts/{account_id}/positions")
    def list_positions(account_id: str, current_user=Depends(get_current_user)):
        try:
            positions = service.list_positions(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=[_position_to_payload(item) for item in positions])

    @router.get("/trading/accounts/{account_id}/position-summary")
    def position_summary(account_id: str, current_user=Depends(get_current_user)):
        try:
            summary = service.position_summary(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=summary)

    @router.get("/trading/accounts/{account_id}/trade-stats")
    def trade_stats(account_id: str, current_user=Depends(get_current_user)):
        try:
            stats = service.trade_stats(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=stats)

    @router.get("/trading/accounts/{account_id}/risk-metrics")
    def risk_metrics(account_id: str, current_user=Depends(get_current_user)):
        try:
            metrics = service.account_risk_metrics(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=metrics)

    @router.get("/trading/accounts/{account_id}/equity-curve")
    def equity_curve(account_id: str, current_user=Depends(get_current_user)):
        try:
            curve = service.account_equity_curve(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=curve)

    @router.get("/trading/accounts/{account_id}/position-analysis")
    def position_analysis(account_id: str, current_user=Depends(get_current_user)):
        try:
            analysis = service.account_position_analysis(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=analysis)

    @router.post("/trading/accounts/{account_id}/orders")
    def create_order(account_id: str, body: OrderCreateRequest, current_user=Depends(get_current_user)):
        try:
            order = service.submit_order(
                user_id=current_user.id,
                account_id=account_id,
                symbol=body.symbol,
                side=body.side,
                quantity=body.quantity,
                price=body.price,
            )
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=_order_to_payload(order))

    @router.get("/trading/accounts/{account_id}/orders")
    def list_orders(account_id: str, current_user=Depends(get_current_user)):
        try:
            orders = service.list_orders(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=[_order_to_payload(item) for item in orders])

    @router.get("/trading/accounts/{account_id}/orders/{order_id}")
    def get_order(account_id: str, order_id: str, current_user=Depends(get_current_user)):
        try:
            order = service.get_order(
                user_id=current_user.id,
                account_id=account_id,
                order_id=order_id,
            )
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        if order is None:
            return _error(status_code=404, code="ORDER_NOT_FOUND", message="order not found")

        return success_response(data=_order_to_payload(order))

    @router.post("/trading/accounts/{account_id}/orders/{order_id}/fill")
    def fill_order(account_id: str, order_id: str, current_user=Depends(get_current_user)):
        try:
            order = service.fill_order(user_id=current_user.id, account_id=account_id, order_id=order_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        except OrderNotFoundError:
            return _error(status_code=404, code="ORDER_NOT_FOUND", message="order not found")
        except InvalidTradeOrderTransitionError:
            return _error(
                status_code=409,
                code="ORDER_INVALID_TRANSITION",
                message="order state transition is invalid",
            )
        except LedgerTransactionError:
            return _error(
                status_code=500,
                code="LEDGER_TRANSACTION_FAILED",
                message="ledger transaction failed",
            )

        return success_response(data=_order_to_payload(order))

    @router.post("/trading/accounts/{account_id}/orders/{order_id}/cancel")
    def cancel_order(account_id: str, order_id: str, current_user=Depends(get_current_user)):
        try:
            order = service.cancel_order(
                user_id=current_user.id,
                account_id=account_id,
                order_id=order_id,
            )
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        except OrderNotFoundError:
            return _error(status_code=404, code="ORDER_NOT_FOUND", message="order not found")
        except InvalidTradeOrderTransitionError:
            return _error(
                status_code=409,
                code="ORDER_INVALID_TRANSITION",
                message="order state transition is invalid",
            )

        return success_response(data=_order_to_payload(order))

    @router.get("/trading/accounts/{account_id}/trades")
    def list_trades(account_id: str, current_user=Depends(get_current_user)):
        try:
            trades = service.list_trades(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=[_trade_to_payload(item) for item in trades])

    @router.get("/trading/accounts/{account_id}/trades/{trade_id}")
    def get_trade(account_id: str, trade_id: str, current_user=Depends(get_current_user)):
        try:
            trade = service.get_trade(
                user_id=current_user.id,
                account_id=account_id,
                trade_id=trade_id,
            )
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        except TradeNotFoundError:
            return _error(status_code=404, code="TRADE_NOT_FOUND", message="trade not found")

        return success_response(data=_trade_to_payload(trade))

    @router.get("/trading/accounts/{account_id}/cash-flows")
    def list_cash_flows(account_id: str, current_user=Depends(get_current_user)):
        try:
            flows = service.list_cash_flows(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=[_cash_flow_to_payload(item) for item in flows])

    @router.post("/trading/accounts/{account_id}/deposit")
    def deposit(account_id: str, body: AmountRequest, current_user=Depends(get_current_user)):
        try:
            flow = service.deposit(user_id=current_user.id, account_id=account_id, amount=body.amount)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        except ValueError:
            return _error(status_code=400, code="INVALID_ARGUMENT", message="amount must be positive")

        return success_response(data=_cash_flow_to_payload(flow))

    @router.post("/trading/accounts/{account_id}/withdraw")
    def withdraw(account_id: str, body: AmountRequest, current_user=Depends(get_current_user)):
        try:
            flow = service.withdraw(user_id=current_user.id, account_id=account_id, amount=body.amount)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        except InsufficientFundsError:
            return _error(
                status_code=409,
                code="INSUFFICIENT_FUNDS",
                message="insufficient funds",
            )
        except ValueError:
            return _error(status_code=400, code="INVALID_ARGUMENT", message="amount must be positive")

        return success_response(data=_cash_flow_to_payload(flow))

    @router.get("/trading/ops/pending-orders")
    def pending_orders(
        account_id: str | None = Query(default=None, alias="accountId"),
        current_user=Depends(get_current_user),
    ):
        decision = resolve_admin_decision(current_user)
        try:
            orders = service.list_pending_orders(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
                account_id=account_id,
            )
        except TradingAdminRequiredError:
            return _error(
                status_code=403,
                code="ADMIN_REQUIRED",
                message="admin role required",
            )

        return success_response(data=[_order_to_payload(item) for item in orders])

    @router.post("/trading/ops/refresh-prices")
    def refresh_prices(body: RefreshPricesRequest, current_user=Depends(get_current_user)):
        decision = resolve_admin_decision(current_user)
        try:
            result = service.refresh_market_prices(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
                price_updates=body.price_updates,
                idempotency_key=body.idempotency_key,
                confirmation_token=body.confirmation_token,
                account_id=body.account_id,
            )
        except TradingAdminRequiredError:
            return _error(
                status_code=403,
                code="ADMIN_REQUIRED",
                message="admin role required",
            )
        except PriceRefreshConflictError:
            return _error(
                status_code=409,
                code="IDEMPOTENCY_CONFLICT",
                message="idempotency key already exists",
            )
        except ValueError as exc:
            return _error(
                status_code=400,
                code="INVALID_ARGUMENT",
                message=str(exc),
            )

        return success_response(data=result)

    @router.get("/trading/accounts/{account_id}/overview")
    def account_overview(account_id: str, current_user=Depends(get_current_user)):
        try:
            overview = service.account_overview(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=overview)

    return router
