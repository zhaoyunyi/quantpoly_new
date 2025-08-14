"""signal_execution FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from platform_core.response import error_response, success_response
from signal_execution.domain import ExecutionRecord, TradingSignal
from signal_execution.service import (
    AdminRequiredError,
    BatchIdempotencyConflictError,
    InvalidSignalParametersError,
    SignalAccessDeniedError,
    SignalExecutionService,
)


class CreateSignalRequest(BaseModel):
    strategy_id: str = Field(alias="strategyId")
    account_id: str = Field(alias="accountId")
    symbol: str
    side: str
    parameters: dict[str, Any] | None = Field(default=None)
    expires_at: datetime | None = Field(default=None, alias="expiresAt")

    model_config = {"populate_by_name": True}


class ValidateSignalParametersRequest(BaseModel):
    strategy_id: str = Field(alias="strategyId")
    account_id: str = Field(alias="accountId")
    parameters: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class CleanupAllRequest(BaseModel):
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")

    model_config = {"populate_by_name": True}


class BatchSignalRequest(BaseModel):
    signal_ids: list[str] = Field(alias="signalIds")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _signal_payload(signal: TradingSignal) -> dict:
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
    }


def _execution_payload(record: ExecutionRecord) -> dict:
    return {
        "id": record.id,
        "signalId": record.signal_id,
        "strategyId": record.strategy_id,
        "symbol": record.symbol,
        "status": record.status,
        "metrics": record.metrics,
        "createdAt": _dt(record.created_at),
    }


def _running_signal_payload(signal: TradingSignal) -> dict:
    return {
        "signalId": signal.id,
        "strategyId": signal.strategy_id,
        "accountId": signal.account_id,
        "symbol": signal.symbol,
        "status": signal.status,
        "updatedAt": _dt(signal.updated_at),
    }


def create_router(*, service: SignalExecutionService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/signals/validate-parameters")
    def validate_parameters(body: ValidateSignalParametersRequest, current_user=Depends(get_current_user)):
        try:
            service.validate_parameters(
                user_id=current_user.id,
                strategy_id=body.strategy_id,
                account_id=body.account_id,
                parameters=body.parameters,
            )
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )
        except InvalidSignalParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="SIGNAL_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        return success_response(data={"valid": True})

    @router.post("/signals")
    def create_signal(body: CreateSignalRequest, current_user=Depends(get_current_user)):
        try:
            signal = service.create_signal(
                user_id=current_user.id,
                strategy_id=body.strategy_id,
                account_id=body.account_id,
                symbol=body.symbol,
                side=body.side,
                parameters=body.parameters,
                expires_at=body.expires_at,
            )
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )
        except InvalidSignalParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="SIGNAL_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        return success_response(data=_signal_payload(signal))

    @router.get("/signals")
    def list_signals(
        keyword: str | None = Query(default=None),
        strategy_id: str | None = Query(default=None, alias="strategyId"),
        symbol: str | None = Query(default=None),
        status: str | None = Query(default=None),
        current_user=Depends(get_current_user),
    ):
        signals = service.list_signals(
            user_id=current_user.id,
            keyword=keyword,
            strategy_id=strategy_id,
            symbol=symbol,
            status=status,
        )
        return success_response(data=[_signal_payload(item) for item in signals])

    @router.get("/signals/strategy/{strategy_id}")
    def list_signals_by_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        signals = service.list_signals(user_id=current_user.id, strategy_id=strategy_id)
        return success_response(data=[_signal_payload(item) for item in signals])

    @router.get("/signals/symbol/{symbol}")
    def list_signals_by_symbol(symbol: str, current_user=Depends(get_current_user)):
        signals = service.list_signals(user_id=current_user.id, symbol=symbol)
        return success_response(data=[_signal_payload(item) for item in signals])

    @router.post("/signals/batch/execute")
    def batch_execute(body: BatchSignalRequest, current_user=Depends(get_current_user)):
        try:
            result = service.batch_execute_signals(
                user_id=current_user.id,
                signal_ids=body.signal_ids,
                idempotency_key=body.idempotency_key,
            )
        except BatchIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="IDEMPOTENCY_CONFLICT",
                    message="idempotency key already exists",
                ),
            )

        return success_response(data=result)

    @router.post("/signals/batch/cancel")
    def batch_cancel(body: BatchSignalRequest, current_user=Depends(get_current_user)):
        try:
            result = service.batch_cancel_signals(
                user_id=current_user.id,
                signal_ids=body.signal_ids,
                idempotency_key=body.idempotency_key,
            )
        except BatchIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="IDEMPOTENCY_CONFLICT",
                    message="idempotency key already exists",
                ),
            )

        return success_response(data=result)

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

    @router.get("/signals/executions")
    def list_executions(
        signal_id: str | None = Query(default=None, alias="signalId"),
        status: str | None = Query(default=None),
        current_user=Depends(get_current_user),
    ):
        executions = service.list_executions(
            user_id=current_user.id,
            signal_id=signal_id,
            status=status,
        )
        return success_response(data=[_execution_payload(item) for item in executions])

    @router.get("/signals/executions/running")
    def list_running_executions(current_user=Depends(get_current_user)):
        items = service.list_running_executions(user_id=current_user.id)
        return success_response(data=[_running_signal_payload(item) for item in items])

    @router.get("/signals/executions/trend")
    def execution_trend(current_user=Depends(get_current_user)):
        return success_response(data=service.execution_trend(user_id=current_user.id))

    @router.get("/signals/executions/performance")
    def performance_statistics(
        strategy_id: str | None = Query(default=None, alias="strategyId"),
        symbol: str | None = Query(default=None),
        current_user=Depends(get_current_user),
    ):
        return success_response(
            data=service.performance_statistics(
                user_id=current_user.id,
                strategy_id=strategy_id,
                symbol=symbol,
            )
        )

    @router.get("/signals/executions/{execution_id}")
    def get_execution(execution_id: str, current_user=Depends(get_current_user)):
        try:
            execution = service.get_execution(user_id=current_user.id, execution_id=execution_id)
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=_execution_payload(execution))

    @router.post("/signals/maintenance/update-expired")
    def update_expired(current_user=Depends(get_current_user)):
        expired = service.update_expired_signals(user_id=current_user.id)
        return success_response(data={"expired": expired})

    @router.post("/signals/maintenance/cleanup-expired")
    def cleanup_expired(current_user=Depends(get_current_user)):
        deleted = service.cleanup_expired_signals(user_id=current_user.id)
        return success_response(data={"deleted": deleted})

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
