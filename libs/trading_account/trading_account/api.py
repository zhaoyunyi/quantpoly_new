"""trading_account FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from job_orchestration.service import (
    IdempotencyConflictError as JobIdempotencyConflictError,
)
from job_orchestration.service import JobOrchestrationService
from pydantic import BaseModel, Field

from platform_core.authz import resolve_admin_decision
from platform_core.response import error_response, success_response
from trading_account.domain import InvalidTradeOrderTransitionError
from trading_account.service import (
    AccountAccessDeniedError,
    InsufficientFundsError,
    InsufficientPositionError,
    LedgerTransactionError,
    OrderNotFoundError,
    PriceRefreshConflictError,
    RiskAssessmentPendingError,
    RiskAssessmentUnavailableError,
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




def _assessment_to_payload(snapshot) -> dict[str, Any]:
    return {
        "assessmentId": snapshot.id,
        "accountId": snapshot.account_id,
        "strategyId": snapshot.strategy_id,
        "riskScore": snapshot.risk_score,
        "riskLevel": snapshot.risk_level,
        "triggeredRuleIds": snapshot.triggered_rule_ids,
        "createdAt": _dt(snapshot.created_at),
    }


def _job_payload(job) -> dict[str, Any]:
    return {
        "taskId": job.id,
        "taskType": job.task_type,
        "status": job.status,
        "result": job.result,
        "error": {"code": job.error_code, "message": job.error_message}
        if job.error_code or job.error_message
        else None,
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




def _trade_command_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "order": _order_to_payload(result["order"]),
        "trade": _trade_to_payload(result["trade"]),
        "cashFlow": _cash_flow_to_payload(result["cashFlow"]),
        "position": _position_to_payload(result["position"]),
    }


class AccountCreateRequest(BaseModel):
    account_name: str = Field(alias="accountName")
    initial_capital: float = Field(default=0.0, alias="initialCapital")

    model_config = {"populate_by_name": True}


class AccountUpdateRequest(BaseModel):
    account_name: str | None = Field(default=None, alias="accountName")
    is_active: bool | None = Field(default=None, alias="isActive")

    model_config = {"populate_by_name": True}

class TradeCommandRequest(BaseModel):
    symbol: str
    quantity: float
    price: float


class OrderCreateRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float


class OrderAmendRequest(BaseModel):
    quantity: float | None = None
    price: float | None = None


class AmountRequest(BaseModel):
    amount: float


class RefreshPricesRequest(BaseModel):
    price_updates: dict[str, float] = Field(alias="priceUpdates")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")
    account_id: str | None = Field(default=None, alias="accountId")

    model_config = {"populate_by_name": True}


class PendingProcessTaskRequest(BaseModel):
    max_trades: int = Field(default=100, ge=1, alias="maxTrades")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")

    model_config = {"populate_by_name": True}


class DailyStatsTaskRequest(BaseModel):
    account_ids: list[str] = Field(default_factory=list, alias="accountIds")
    target_date: str = Field(alias="targetDate")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")

    model_config = {"populate_by_name": True}


class BatchExecuteTaskRequest(BaseModel):
    trade_requests: list[dict[str, Any]] = Field(default_factory=list, alias="tradeRequests")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")

    model_config = {"populate_by_name": True}


class RiskMonitorTaskRequest(BaseModel):
    account_ids: list[str] = Field(default_factory=list, alias="accountIds")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")

    model_config = {"populate_by_name": True}


class AccountCleanupTaskRequest(BaseModel):
    account_ids: list[str] = Field(default_factory=list, alias="accountIds")
    days_threshold: int = Field(default=90, ge=1, alias="daysThreshold")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")

    model_config = {"populate_by_name": True}


def create_router(
    *,
    service: TradingAccountService,
    get_current_user: Any,
    job_service: JobOrchestrationService | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/trading/accounts")
    def list_accounts(current_user=Depends(get_current_user)):
        accounts = service.list_accounts(user_id=current_user.id)
        return success_response(data=[_account_to_payload(item) for item in accounts])

    @router.post("/trading/accounts")
    def create_account(body: AccountCreateRequest, current_user=Depends(get_current_user)):
        created = service.create_account(
            user_id=current_user.id,
            account_name=body.account_name,
            initial_capital=body.initial_capital,
        )
        return success_response(data=_account_to_payload(created))

    @router.get("/trading/accounts/aggregate")
    def account_aggregate(current_user=Depends(get_current_user)):
        data = service.user_account_aggregate(user_id=current_user.id)
        return success_response(data=data)

    @router.get("/trading/accounts/filter-config")
    def account_filter_config(current_user=Depends(get_current_user)):
        return success_response(data=service.account_filter_config(user_id=current_user.id))

    @router.get("/trading/accounts/{account_id}")
    def get_account(account_id: str, current_user=Depends(get_current_user)):
        account = service.get_account(user_id=current_user.id, account_id=account_id)
        if account is None:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        return success_response(data=_account_to_payload(account))

    @router.put("/trading/accounts/{account_id}")
    def update_account(
        account_id: str,
        body: AccountUpdateRequest,
        current_user=Depends(get_current_user),
    ):
        updated = service.update_account(
            user_id=current_user.id,
            account_id=account_id,
            account_name=body.account_name,
            is_active=body.is_active,
        )
        if updated is None:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        return success_response(data=_account_to_payload(updated))

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

    @router.get("/trading/accounts/{account_id}/positions/{symbol}")
    def get_position_by_symbol(account_id: str, symbol: str, current_user=Depends(get_current_user)):
        try:
            position = service.get_position_by_symbol(
                user_id=current_user.id,
                account_id=account_id,
                symbol=symbol,
            )
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        if position is None:
            return _error(status_code=404, code="POSITION_NOT_FOUND", message="position not found")

        return success_response(data=_position_to_payload(position))

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

    @router.post("/trading/accounts/{account_id}/buy")
    def buy(account_id: str, body: TradeCommandRequest, current_user=Depends(get_current_user)):
        try:
            result = service.execute_buy_command(
                user_id=current_user.id,
                account_id=account_id,
                symbol=body.symbol,
                quantity=body.quantity,
                price=body.price,
            )
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
        except ValueError as exc:
            return _error(
                status_code=400,
                code="INVALID_ARGUMENT",
                message=str(exc),
            )
        except LedgerTransactionError:
            return _error(
                status_code=500,
                code="LEDGER_TRANSACTION_FAILED",
                message="ledger transaction failed",
            )

        return success_response(data=_trade_command_payload(result))

    @router.post("/trading/accounts/{account_id}/sell")
    def sell(account_id: str, body: TradeCommandRequest, current_user=Depends(get_current_user)):
        try:
            result = service.execute_sell_command(
                user_id=current_user.id,
                account_id=account_id,
                symbol=body.symbol,
                quantity=body.quantity,
                price=body.price,
            )
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        except InsufficientPositionError:
            return _error(
                status_code=409,
                code="INSUFFICIENT_POSITION",
                message="insufficient position",
            )
        except ValueError as exc:
            return _error(
                status_code=400,
                code="INVALID_ARGUMENT",
                message=str(exc),
            )
        except LedgerTransactionError:
            return _error(
                status_code=500,
                code="LEDGER_TRANSACTION_FAILED",
                message="ledger transaction failed",
            )

        return success_response(data=_trade_command_payload(result))

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

    @router.patch("/trading/accounts/{account_id}/orders/{order_id}")
    def update_order(
        account_id: str,
        order_id: str,
        body: OrderAmendRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            order = service.update_order(
                user_id=current_user.id,
                account_id=account_id,
                order_id=order_id,
                quantity=body.quantity,
                price=body.price,
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
        except ValueError as exc:
            return _error(status_code=400, code="INVALID_ARGUMENT", message=str(exc))

        return success_response(data=_order_to_payload(order))

    @router.delete("/trading/accounts/{account_id}/orders/{order_id}")
    def delete_order(account_id: str, order_id: str, current_user=Depends(get_current_user)):
        try:
            order = service.delete_order(
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

    @router.get("/trading/accounts/{account_id}/trades/pending")
    def list_pending_trades(account_id: str, current_user=Depends(get_current_user)):
        try:
            orders = service.list_pending_trades(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=[_order_to_payload(item) for item in orders])

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

    @router.post("/trading/ops/refresh-prices/task")
    def refresh_prices_task(body: RefreshPricesRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return _error(
                status_code=503,
                code="TASK_ORCHESTRATION_UNAVAILABLE",
                message="job orchestration is not configured",
            )

        decision = resolve_admin_decision(current_user)
        if not decision.is_admin:
            return _error(
                status_code=403,
                code="ADMIN_REQUIRED",
                message="admin role required",
            )

        job_idempotency_key = body.idempotency_key or f"trading-refresh-prices:{current_user.id}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="trading_refresh_prices",
                payload={
                    "accountId": body.account_id,
                    "priceUpdates": body.price_updates,
                },
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.refresh_market_prices(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
                price_updates=body.price_updates,
                idempotency_key=None,
                confirmation_token=body.confirmation_token,
                account_id=body.account_id,
            )
            if "symbols" in result and "updatedSymbols" not in result:
                result = {**result, "updatedSymbols": result["symbols"]}
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return _error(
                status_code=409,
                code="IDEMPOTENCY_CONFLICT",
                message="idempotency key already exists",
            )
        except TradingAdminRequiredError:
            return _error(
                status_code=403,
                code="ADMIN_REQUIRED",
                message="admin role required",
            )
        except ValueError as exc:
            return _error(
                status_code=400,
                code="INVALID_ARGUMENT",
                message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            return _error(
                status_code=500,
                code="TASK_EXECUTION_FAILED",
                message=str(exc),
            )

        return success_response(data=_job_payload(job))

    @router.post("/trading/ops/pending/process-task")
    def pending_process_task(body: PendingProcessTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return _error(
                status_code=503,
                code="TASK_ORCHESTRATION_UNAVAILABLE",
                message="job orchestration is not configured",
            )

        decision = resolve_admin_decision(current_user)
        if not decision.is_admin:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")

        job_idempotency_key = body.idempotency_key or f"trading-pending-process:{current_user.id}:{body.max_trades}"

        audit_id = f"audit-{current_user.id}:{datetime.now().timestamp()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="trading_pending_process",
                payload={"maxTrades": body.max_trades},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.process_pending_trades(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
                max_trades=body.max_trades,
                idempotency_key=body.idempotency_key,
                confirmation_token=body.confirmation_token,
                audit_id=audit_id,
            )
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return _error(status_code=409, code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        except TradingAdminRequiredError:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")
        except ValueError as exc:
            return _error(status_code=400, code="INVALID_ARGUMENT", message=str(exc))
        except Exception as exc:  # noqa: BLE001
            return _error(status_code=500, code="TASK_EXECUTION_FAILED", message=str(exc))

        return success_response(data=_job_payload(job))

    @router.post("/trading/ops/daily-stats/calculate-task")
    def daily_stats_task(body: DailyStatsTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return _error(
                status_code=503,
                code="TASK_ORCHESTRATION_UNAVAILABLE",
                message="job orchestration is not configured",
            )

        decision = resolve_admin_decision(current_user)
        if not decision.is_admin:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")

        job_idempotency_key = body.idempotency_key or f"trading-daily-stats:{current_user.id}:{body.target_date}"

        audit_id = f"audit-{current_user.id}:{datetime.now().timestamp()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="trading_daily_stats_calculate",
                payload={"accountIds": body.account_ids, "targetDate": body.target_date},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.calculate_daily_stats(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
                account_ids=body.account_ids,
                target_date=body.target_date,
                idempotency_key=body.idempotency_key,
                confirmation_token=body.confirmation_token,
                audit_id=audit_id,
            )
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return _error(status_code=409, code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        except TradingAdminRequiredError:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")
        except ValueError as exc:
            return _error(status_code=400, code="INVALID_ARGUMENT", message=str(exc))
        except Exception as exc:  # noqa: BLE001
            return _error(status_code=500, code="TASK_EXECUTION_FAILED", message=str(exc))

        return success_response(data=_job_payload(job))

    @router.get("/trading/stats/daily")
    def get_daily_stats(
        date: str = Query(...),
        account_id: str = Query(..., alias="accountId"),
        current_user=Depends(get_current_user),
    ):
        try:
            stats = service.get_daily_stats(user_id=current_user.id, date=date, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(status_code=403, code="ACCOUNT_ACCESS_DENIED", message="account does not belong to current user")

        if stats is None:
            return _error(status_code=404, code="NOT_FOUND", message="daily stats not found")

        return success_response(data={"date": date, "items": [stats]})

    @router.post("/trading/ops/batch/execute-task")
    def batch_execute_task(body: BatchExecuteTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return _error(status_code=503, code="TASK_ORCHESTRATION_UNAVAILABLE", message="job orchestration is not configured")

        decision = resolve_admin_decision(current_user)
        if not decision.is_admin:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")

        job_idempotency_key = body.idempotency_key or f"trading-batch-execute:{current_user.id}"

        audit_id = f"audit-{current_user.id}:{datetime.now().timestamp()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="trading_batch_execute",
                payload={"tradeRequests": body.trade_requests},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.batch_execute_trades(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
                trade_requests=body.trade_requests,
                idempotency_key=body.idempotency_key,
                confirmation_token=body.confirmation_token,
                audit_id=audit_id,
            )
            if int(result.get("failed", 0)) > 0:
                job = job_service.fail_job(
                    user_id=current_user.id,
                    job_id=job.id,
                    error_code="TRADING_BATCH_EXECUTE_FAILED",
                    error_message="batch execute completed with failures",
                )
                job.result = result
            else:
                job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return _error(status_code=409, code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        except TradingAdminRequiredError:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")
        except ValueError as exc:
            return _error(status_code=400, code="INVALID_ARGUMENT", message=str(exc))
        except Exception as exc:  # noqa: BLE001
            return _error(status_code=500, code="TASK_EXECUTION_FAILED", message=str(exc))

        return success_response(data=_job_payload(job))

    @router.post("/trading/ops/risk/monitor-task")
    def risk_monitor_task(body: RiskMonitorTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return _error(status_code=503, code="TASK_ORCHESTRATION_UNAVAILABLE", message="job orchestration is not configured")

        decision = resolve_admin_decision(current_user)
        if not decision.is_admin:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")

        job_idempotency_key = body.idempotency_key or f"trading-risk-monitor:{current_user.id}"

        audit_id = f"audit-{current_user.id}:{datetime.now().timestamp()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="trading_risk_monitor",
                payload={"accountIds": body.account_ids},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.monitor_risk(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
                account_ids=body.account_ids,
                idempotency_key=body.idempotency_key,
                confirmation_token=body.confirmation_token,
                audit_id=audit_id,
            )
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return _error(status_code=409, code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        except TradingAdminRequiredError:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")
        except ValueError as exc:
            return _error(status_code=400, code="INVALID_ARGUMENT", message=str(exc))
        except Exception as exc:  # noqa: BLE001
            return _error(status_code=500, code="TASK_EXECUTION_FAILED", message=str(exc))

        return success_response(data=_job_payload(job))

    @router.post("/trading/ops/accounts/cleanup-task")
    def account_cleanup_task(body: AccountCleanupTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return _error(status_code=503, code="TASK_ORCHESTRATION_UNAVAILABLE", message="job orchestration is not configured")

        decision = resolve_admin_decision(current_user)
        if not decision.is_admin:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")

        job_idempotency_key = body.idempotency_key or f"trading-account-cleanup:{current_user.id}:{body.days_threshold}"

        audit_id = f"audit-{current_user.id}:{datetime.now().timestamp()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="trading_account_cleanup",
                payload={"accountIds": body.account_ids, "daysThreshold": body.days_threshold},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.cleanup_account_history(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
                account_ids=body.account_ids,
                days_threshold=body.days_threshold,
                idempotency_key=body.idempotency_key,
                confirmation_token=body.confirmation_token,
                audit_id=audit_id,
            )
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return _error(status_code=409, code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists")
        except TradingAdminRequiredError:
            return _error(status_code=403, code="ADMIN_REQUIRED", message="admin role required")
        except ValueError as exc:
            return _error(status_code=400, code="INVALID_ARGUMENT", message=str(exc))
        except Exception as exc:  # noqa: BLE001
            return _error(status_code=500, code="TASK_EXECUTION_FAILED", message=str(exc))

        return success_response(data=_job_payload(job))

    @router.get("/trading/ops/tasks/{task_id}")
    def trading_ops_task_status(task_id: str, current_user=Depends(get_current_user)):
        if job_service is None:
            return _error(
                status_code=503,
                code="TASK_ORCHESTRATION_UNAVAILABLE",
                message="job orchestration is not configured",
            )

        job = job_service.get_job(user_id=current_user.id, job_id=task_id)
        if job is None:
            return _error(status_code=404, code="TASK_NOT_FOUND", message="task not found")
        return success_response(data=_job_payload(job))

    @router.get("/trading/accounts/{account_id}/summary")
    def account_summary(account_id: str, current_user=Depends(get_current_user)):
        try:
            summary = service.account_summary(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(
            data={
                "account": _account_to_payload(summary["account"]),
                "positions": [_position_to_payload(item) for item in summary["positions"]],
                "positionCount": summary["positionCount"],
                "totalReturnRatio": summary["totalReturnRatio"],
                "stats": summary["stats"],
            }
        )

    @router.get("/trading/accounts/{account_id}/cash-flows/summary")
    def cash_flow_summary(account_id: str, current_user=Depends(get_current_user)):
        try:
            summary = service.cash_flow_summary(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )

        return success_response(data=summary)

    @router.get("/trading/accounts/{account_id}/risk-assessment")
    def get_risk_assessment(account_id: str, current_user=Depends(get_current_user)):
        try:
            snapshot = service.get_risk_assessment(user_id=current_user.id, account_id=account_id)
        except RiskAssessmentPendingError as exc:
            return _error(
                status_code=202,
                code="RISK_ASSESSMENT_PENDING",
                message=str(exc),
            )
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        except RiskAssessmentUnavailableError as exc:
            return _error(
                status_code=503,
                code="RISK_ASSESSMENT_UNAVAILABLE",
                message=str(exc),
            )

        return success_response(data=_assessment_to_payload(snapshot))

    @router.post("/trading/accounts/{account_id}/risk-assessment/evaluate")
    def evaluate_risk_assessment(account_id: str, current_user=Depends(get_current_user)):
        try:
            snapshot = service.evaluate_risk_assessment(
                user_id=current_user.id,
                account_id=account_id,
            )
        except AccountAccessDeniedError:
            return _error(
                status_code=403,
                code="ACCOUNT_ACCESS_DENIED",
                message="account does not belong to current user",
            )
        except RiskAssessmentUnavailableError as exc:
            return _error(
                status_code=503,
                code="RISK_ASSESSMENT_UNAVAILABLE",
                message=str(exc),
            )

        return success_response(data=_assessment_to_payload(snapshot))

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
