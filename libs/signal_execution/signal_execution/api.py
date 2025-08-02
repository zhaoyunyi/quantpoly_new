"""signal_execution FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from platform_core.response import error_response, success_response
from signal_execution.service import AdminRequiredError, SignalAccessDeniedError, SignalExecutionService


class CreateSignalRequest(BaseModel):
    strategy_id: str = Field(alias="strategyId")
    account_id: str = Field(alias="accountId")
    symbol: str
    side: str

    model_config = {"populate_by_name": True}


class CleanupAllRequest(BaseModel):
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")

    model_config = {"populate_by_name": True}


def _dt(value: datetime) -> str:
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
    }


def create_router(*, service: SignalExecutionService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/signals")
    def create_signal(body: CreateSignalRequest, current_user=Depends(get_current_user)):
        try:
            signal = service.create_signal(
                user_id=current_user.id,
                strategy_id=body.strategy_id,
                account_id=body.account_id,
                symbol=body.symbol,
                side=body.side,
            )
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=_signal_payload(signal))

    @router.get("/signals")
    def list_signals(
        keyword: str | None = Query(default=None),
        current_user=Depends(get_current_user),
    ):
        signals = service.list_signals(user_id=current_user.id, keyword=keyword)
        return success_response(data=[_signal_payload(item) for item in signals])

    @router.post("/signals/{signal_id}/execute")
    def execute_signal(signal_id: str, current_user=Depends(get_current_user)):
        try:
            signal = service.execute_signal(user_id=current_user.id, signal_id=signal_id)
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=_signal_payload(signal))

    @router.post("/signals/{signal_id}/cancel")
    def cancel_signal(signal_id: str, current_user=Depends(get_current_user)):
        try:
            signal = service.cancel_signal(user_id=current_user.id, signal_id=signal_id)
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=_signal_payload(signal))

    @router.get("/signals/executions/trend")
    def execution_trend(current_user=Depends(get_current_user)):
        return success_response(data=service.execution_trend(user_id=current_user.id))

    @router.post("/signals/maintenance/cleanup")
    def cleanup_signals(current_user=Depends(get_current_user)):
        deleted = service.cleanup_signals(user_id=current_user.id)
        return success_response(data={"deleted": deleted})

    @router.post("/signals/maintenance/cleanup-all")
    def cleanup_all_signals(
        body: CleanupAllRequest | None = None,
        current_user=Depends(get_current_user),
    ):
        try:
            deleted = service.cleanup_all_signals(
                user_id=current_user.id,
                is_admin=bool(getattr(current_user, "is_admin", False)),
                confirmation_token=body.confirmation_token if body is not None else None,
            )
        except AdminRequiredError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ADMIN_REQUIRED",
                    message="admin role required",
                ),
            )

        return success_response(data={"deleted": deleted})

    return router
