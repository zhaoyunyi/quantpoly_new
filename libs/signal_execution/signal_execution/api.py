"""signal_execution FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from job_orchestration.service import (
    IdempotencyConflictError as JobIdempotencyConflictError,
)
from job_orchestration.service import JobOrchestrationService
from pydantic import BaseModel, Field

from platform_core.authz import resolve_admin_decision
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


class CleanupExecutionsRequest(BaseModel):
    retention_days: int = Field(alias="retentionDays", ge=1)
    confirmation_token: str | None = Field(default=None, alias="confirmationToken")

    model_config = {"populate_by_name": True}


class BatchSignalRequest(BaseModel):
    signal_ids: list[str] = Field(alias="signalIds")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class GenerateSignalsRequest(BaseModel):
    strategy_id: str = Field(alias="strategyId")
    account_id: str = Field(alias="accountId")
    symbols: list[str]
    side: str = Field(default="BUY")
    parameters: dict[str, Any] | None = Field(default=None)
    expires_at: datetime | None = Field(default=None, alias="expiresAt")

    model_config = {"populate_by_name": True}


class GenerateByStrategyRequest(BaseModel):
    strategy_id: str = Field(alias="strategyId")
    account_id: str = Field(alias="accountId")
    symbols: list[str]
    timeframe: str = Field(default="1Day")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")

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
        "metadata": dict(signal.metadata),
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


def _job_payload(job) -> dict[str, Any]:
    return {
        "taskId": job.id,
        "taskType": job.task_type,
        "status": job.status,
        "result": job.result,
    }


def create_router(
    *,
    service: SignalExecutionService,
    get_current_user: Any,
    job_service: JobOrchestrationService | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/signals/generate")
    def generate_signals(body: GenerateSignalsRequest, current_user=Depends(get_current_user)):
        try:
            signals = service.generate_signals(
                user_id=current_user.id,
                strategy_id=body.strategy_id,
                account_id=body.account_id,
                symbols=body.symbols,
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

        return success_response(data={"signals": [_signal_payload(item) for item in signals]})

    @router.post("/signals/generate-by-strategy")
    def generate_signals_by_strategy(body: GenerateByStrategyRequest, current_user=Depends(get_current_user)):
        try:
            result = service.generate_signals_by_strategy(
                user_id=current_user.id,
                strategy_id=body.strategy_id,
                account_id=body.account_id,
                symbols=body.symbols,
                timeframe=body.timeframe,
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

        payload = {
            "strategyId": result["strategyId"],
            "accountId": result["accountId"],
            "template": result["template"],
            "signals": [_signal_payload(item) for item in result["signals"]],
            "skipped": result["skipped"],
        }
        return success_response(data=payload)

    @router.get("/signals/execution-readmodel/templates")
    def list_execution_templates(
        strategy_type: str | None = Query(default=None, alias="strategyType"),
        current_user=Depends(get_current_user),
    ):
        del current_user
        return success_response(data=service.list_execution_templates(strategy_type=strategy_type))

    @router.get("/signals/execution-readmodel/strategies/{strategy_id}/statistics")
    def strategy_execution_statistics(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            data = service.strategy_execution_statistics(
                user_id=current_user.id,
                strategy_id=strategy_id,
            )
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=data)

    @router.get("/signals/execution-readmodel/strategies/{strategy_id}/trend")
    def strategy_execution_trend(
        strategy_id: str,
        days: int = Query(default=7, ge=1),
        current_user=Depends(get_current_user),
    ):
        try:
            data = service.strategy_execution_trend(
                user_id=current_user.id,
                strategy_id=strategy_id,
                days=days,
            )
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=data)

    @router.post("/signals/{signal_id}/process")
    def process_signal(signal_id: str, current_user=Depends(get_current_user)):
        try:
            signal, risk = service.process_signal(user_id=current_user.id, signal_id=signal_id)
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        payload = _signal_payload(signal)
        payload["risk"] = risk
        return success_response(data=payload)

    @router.get("/signals/trends/daily")
    def daily_trend(
        days: int = Query(default=7, ge=1),
        current_user=Depends(get_current_user),
    ):
        return success_response(data=service.daily_trend(user_id=current_user.id, days=days))

    @router.get("/signals/performance/{signal_id}")
    def signal_performance(signal_id: str, current_user=Depends(get_current_user)):
        try:
            data = service.signal_performance(user_id=current_user.id, signal_id=signal_id)
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=data)

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
        account_id: str | None = Query(default=None, alias="accountId"),
        symbol: str | None = Query(default=None),
        status: str | None = Query(default=None),
        current_user=Depends(get_current_user),
    ):
        signals = service.list_signals(
            user_id=current_user.id,
            keyword=keyword,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            status=status,
        )
        return success_response(data=[_signal_payload(item) for item in signals])

    @router.get("/signals/search")
    def search_signals(
        keyword: str | None = Query(default=None),
        strategy_id: str | None = Query(default=None, alias="strategyId"),
        account_id: str | None = Query(default=None, alias="accountId"),
        symbol: str | None = Query(default=None),
        status: str | None = Query(default=None),
        current_user=Depends(get_current_user),
    ):
        signals = service.search_signals(
            user_id=current_user.id,
            keyword=keyword,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            status=status,
        )
        return success_response(data=[_signal_payload(item) for item in signals])

    @router.get("/signals/pending")
    def list_pending_signals(current_user=Depends(get_current_user)):
        signals = service.list_pending_signals(user_id=current_user.id)
        return success_response(data=[_signal_payload(item) for item in signals])

    @router.get("/signals/expired")
    def list_expired_signals(current_user=Depends(get_current_user)):
        signals = service.list_expired_signals(user_id=current_user.id)
        return success_response(data=[_signal_payload(item) for item in signals])

    @router.get("/signals/dashboard")
    def signal_dashboard(
        keyword: str | None = Query(default=None),
        strategy_id: str | None = Query(default=None, alias="strategyId"),
        account_id: str | None = Query(default=None, alias="accountId"),
        symbol: str | None = Query(default=None),
        current_user=Depends(get_current_user),
    ):
        return success_response(
            data=service.signal_dashboard(
                user_id=current_user.id,
                keyword=keyword,
                strategy_id=strategy_id,
                account_id=account_id,
                symbol=symbol,
            )
        )

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

    @router.post("/signals/batch/execute-task")
    def batch_execute_task(body: BatchSignalRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or f"signal-batch-execute:{uuid4()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="signal_batch_execute",
                payload={"signalIds": body.signal_ids},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.batch_execute_signals(
                user_id=current_user.id,
                signal_ids=body.signal_ids,
                idempotency_key=None,
            )
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.post("/signals/batch/cancel-task")
    def batch_cancel_task(body: BatchSignalRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or f"signal-batch-cancel:{uuid4()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="signal_batch_cancel",
                payload={"signalIds": body.signal_ids},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.batch_cancel_signals(
                user_id=current_user.id,
                signal_ids=body.signal_ids,
                idempotency_key=None,
            )
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

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

    @router.post("/signals/{signal_id}/expire")
    def expire_signal(signal_id: str, current_user=Depends(get_current_user)):
        try:
            signal = service.expire_signal(user_id=current_user.id, signal_id=signal_id)
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

    @router.get("/signals/executions/performance/by-strategy")
    def performance_statistics_by_strategy(current_user=Depends(get_current_user)):
        return success_response(data=service.performance_statistics_by_strategy(user_id=current_user.id))

    @router.get("/signals/statistics/{account_id}")
    def account_statistics(account_id: str, current_user=Depends(get_current_user)):
        try:
            stats = service.account_statistics(user_id=current_user.id, account_id=account_id)
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=stats)

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

    @router.get("/signals/{signal_id}")
    def get_signal_detail(signal_id: str, current_user=Depends(get_current_user)):
        try:
            signal = service.get_signal_detail(user_id=current_user.id, signal_id=signal_id)
        except SignalAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="SIGNAL_ACCESS_DENIED",
                    message="signal does not belong to current user",
                ),
            )

        return success_response(data=_signal_payload(signal))

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

    @router.post("/signals/maintenance/cleanup-executions")
    def cleanup_executions(
        body: CleanupExecutionsRequest,
        current_user=Depends(get_current_user),
    ):
        decision = resolve_admin_decision(current_user)
        audit_id = str(uuid4())
        try:
            deleted = service.cleanup_execution_history(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                retention_days=body.retention_days,
                admin_decision_source=decision.source,
                confirmation_token=body.confirmation_token,
                audit_id=audit_id,
            )
        except AdminRequiredError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ADMIN_REQUIRED",
                    message="admin role required",
                ),
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(code="INVALID_ARGUMENT", message=str(exc)),
            )

        return success_response(
            data={
                "deleted": deleted,
                "retentionDays": body.retention_days,
                "auditId": audit_id,
            }
        )

    @router.post("/signals/maintenance/cleanup-all")
    def cleanup_all_signals(
        body: CleanupAllRequest | None = None,
        current_user=Depends(get_current_user),
    ):
        decision = resolve_admin_decision(current_user)
        try:
            deleted = service.cleanup_all_signals(
                user_id=current_user.id,
                is_admin=decision.is_admin,
                admin_decision_source=decision.source,
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
