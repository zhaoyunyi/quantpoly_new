"""trading_account FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from platform_core.response import error_response, success_response
from trading_account.service import AccountAccessDeniedError, TradingAccountService


def _dt(value: datetime) -> str:
    return value.isoformat()


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


def create_router(*, service: TradingAccountService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/trading/accounts")
    def list_accounts(current_user=Depends(get_current_user)):
        accounts = service.list_accounts(user_id=current_user.id)
        return success_response(data=[_account_to_payload(item) for item in accounts])

    @router.get("/trading/accounts/{account_id}/positions")
    def list_positions(account_id: str, current_user=Depends(get_current_user)):
        try:
            positions = service.list_positions(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ACCOUNT_ACCESS_DENIED",
                    message="account does not belong to current user",
                ),
            )

        return success_response(data=[_position_to_payload(item) for item in positions])

    @router.get("/trading/accounts/{account_id}/position-summary")
    def position_summary(account_id: str, current_user=Depends(get_current_user)):
        try:
            summary = service.position_summary(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ACCOUNT_ACCESS_DENIED",
                    message="account does not belong to current user",
                ),
            )

        return success_response(data=summary)

    @router.get("/trading/accounts/{account_id}/trade-stats")
    def trade_stats(account_id: str, current_user=Depends(get_current_user)):
        try:
            stats = service.trade_stats(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ACCOUNT_ACCESS_DENIED",
                    message="account does not belong to current user",
                ),
            )

        return success_response(data=stats)

    return router
