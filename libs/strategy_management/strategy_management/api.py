"""strategy_management FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from job_orchestration.service import IdempotencyConflictError
from job_orchestration.service import JobOrchestrationService
from pydantic import BaseModel, Field

from platform_core.response import error_response, success_response
from strategy_management.domain import InvalidStrategyTransitionError, StrategyInUseError
from strategy_management.service import (
    InvalidStrategyParametersError,
    StrategyAccessDeniedError,
    StrategyService,
)


class ResearchPerformanceTaskRequest(BaseModel):
    analysis_period_days: int = Field(default=30, alias="analysisPeriodDays", ge=1, le=365)
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class ResearchOptimizationTaskRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class CreateStrategyRequest(BaseModel):
    name: str
    template: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class UpdateStrategyRequest(BaseModel):
    name: str | None = None
    parameters: dict[str, Any] | None = None


class CreateStrategyFromTemplateRequest(BaseModel):
    name: str
    template_id: str = Field(alias="templateId")
    parameters: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class ValidateExecutionRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


class CreateBacktestForStrategyRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


def _dt(value: datetime) -> str:
    return value.isoformat()


def _serialize_strategy(strategy) -> dict[str, Any]:
    return {
        "id": strategy.id,
        "userId": strategy.user_id,
        "name": strategy.name,
        "template": strategy.template,
        "parameters": strategy.parameters,
        "status": strategy.status,
        "createdAt": _dt(strategy.created_at),
        "updatedAt": _dt(strategy.updated_at),
    }


def _serialize_backtest(task: Any) -> dict[str, Any]:
    if isinstance(task, dict):
        return task

    return {
        "id": task.id,
        "userId": task.user_id,
        "strategyId": task.strategy_id,
        "status": task.status,
        "config": task.config,
        "metrics": task.metrics,
        "createdAt": _dt(task.created_at),
        "updatedAt": _dt(task.updated_at),
    }


def _access_denied_response() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=error_response(
            code="STRATEGY_ACCESS_DENIED",
            message="strategy does not belong to current user",
        ),
    )


def create_router(
    *,
    service: StrategyService,
    get_current_user: Any,
    job_service: JobOrchestrationService | None = None,
    signal_service: Any | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/strategies/templates")
    def list_templates(current_user=Depends(get_current_user)):
        del current_user
        return success_response(data=service.list_templates())

    @router.get("/strategies")
    def list_strategies(current_user=Depends(get_current_user)):
        items = service.list_strategies(user_id=current_user.id)
        return success_response(data=[_serialize_strategy(item) for item in items])

    @router.get("/strategies/{strategy_id}")
    def get_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        strategy = service.get_strategy(user_id=current_user.id, strategy_id=strategy_id)
        if strategy is None:
            return _access_denied_response()
        return success_response(data=_serialize_strategy(strategy))

    @router.post("/strategies")
    def create_strategy(body: CreateStrategyRequest, current_user=Depends(get_current_user)):
        try:
            created = service.create_strategy(
                user_id=current_user.id,
                name=body.name,
                template=body.template,
                parameters=body.parameters,
            )
        except InvalidStrategyParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="STRATEGY_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        return success_response(data=_serialize_strategy(created))

    @router.put("/strategies/{strategy_id}")
    def update_strategy(
        strategy_id: str,
        body: UpdateStrategyRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            updated = service.update_strategy(
                user_id=current_user.id,
                strategy_id=strategy_id,
                name=body.name,
                parameters=body.parameters,
            )
        except InvalidStrategyParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="STRATEGY_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        if updated is None:
            return _access_denied_response()

        return success_response(data=_serialize_strategy(updated))

    @router.post("/strategies/from-template")
    def create_strategy_from_template(
        body: CreateStrategyFromTemplateRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            created = service.create_strategy_from_template(
                user_id=current_user.id,
                name=body.name,
                template_id=body.template_id,
                parameters=body.parameters,
            )
        except InvalidStrategyParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="STRATEGY_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        return success_response(data=_serialize_strategy(created))

    @router.post("/strategies/{strategy_id}/validate-execution")
    def validate_execution(
        strategy_id: str,
        body: ValidateExecutionRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            strategy = service.validate_execution_parameters(
                user_id=current_user.id,
                strategy_id=strategy_id,
                parameters=body.parameters,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()
        except InvalidStrategyParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="STRATEGY_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        return success_response(
            data={
                "valid": True,
                "strategyId": strategy.id,
                "template": strategy.template,
            }
        )

    @router.post("/strategies/{strategy_id}/backtests")
    def create_strategy_backtest(
        strategy_id: str,
        body: CreateBacktestForStrategyRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            task = service.create_backtest_for_strategy(
                user_id=current_user.id,
                strategy_id=strategy_id,
                config=body.config,
                idempotency_key=body.idempotency_key,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()

        return success_response(data=_serialize_backtest(task))

    @router.get("/strategies/{strategy_id}/backtests")
    def list_strategy_backtests(
        strategy_id: str,
        current_user=Depends(get_current_user),
        status: str | None = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, alias="pageSize", ge=1, le=200),
    ):
        try:
            listing = service.list_backtests_for_strategy(
                user_id=current_user.id,
                strategy_id=strategy_id,
                status=status,
                page=page,
                page_size=page_size,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()

        items = [_serialize_backtest(item) for item in listing.get("items", [])]
        return success_response(
            data={
                "items": items,
                "total": int(listing.get("total", len(items))),
                "page": int(listing.get("page", page)),
                "pageSize": int(listing.get("pageSize", page_size)),
            }
        )

    @router.get("/strategies/{strategy_id}/backtest-stats")
    def strategy_backtest_stats(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            stats = service.backtest_stats_for_strategy(
                user_id=current_user.id,
                strategy_id=strategy_id,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()

        return success_response(data=stats)

    @router.post("/strategies/{strategy_id}/activate")
    def activate_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            strategy = service.activate_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except InvalidStrategyTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="STRATEGY_INVALID_TRANSITION",
                    message=str(exc),
                ),
            )

        if strategy is None:
            return _access_denied_response()

        return success_response(data=_serialize_strategy(strategy))

    @router.post("/strategies/{strategy_id}/deactivate")
    def deactivate_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            strategy = service.deactivate_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except InvalidStrategyTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="STRATEGY_INVALID_TRANSITION",
                    message=str(exc),
                ),
            )

        if strategy is None:
            return _access_denied_response()

        return success_response(data=_serialize_strategy(strategy))

    @router.post("/strategies/{strategy_id}/archive")
    def archive_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            strategy = service.archive_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except InvalidStrategyTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="STRATEGY_INVALID_TRANSITION",
                    message=str(exc),
                ),
            )

        if strategy is None:
            return _access_denied_response()

        return success_response(data=_serialize_strategy(strategy))

    @router.delete("/strategies/{strategy_id}")
    def delete_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            deleted = service.delete_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except StrategyInUseError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="STRATEGY_IN_USE",
                    message=str(exc),
                ),
            )

        if not deleted:
            return _access_denied_response()

        return success_response(data={"deleted": True})

    @router.post("/strategies/{strategy_id}/research/performance-task")
    def submit_strategy_performance_task(
        strategy_id: str,
        body: ResearchPerformanceTaskRequest,
        current_user=Depends(get_current_user),
    ):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        try:
            owned = service.get_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except StrategyAccessDeniedError:
            owned = None
        if owned is None:
            return _access_denied_response()

        if signal_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="SIGNAL_EXECUTION_UNAVAILABLE",
                    message="signal execution is not configured",
                ),
            )

        metrics = signal_service.performance_statistics(user_id=current_user.id, strategy_id=strategy_id)

        job_idempotency_key = body.idempotency_key or f"strategy-performance-task:{strategy_id}:{uuid4()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="strategy_performance_analyze",
                payload={
                    "strategyId": strategy_id,
                    "analysisPeriodDays": body.analysis_period_days,
                },
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = {
                "strategyId": strategy_id,
                "analysisPeriodDays": body.analysis_period_days,
                "metrics": metrics,
            }
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except IdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(
            data={
                "taskId": job.id,
                "taskType": job.task_type,
                "status": job.status,
                "result": job.result,
            }
        )

    @router.post("/strategies/{strategy_id}/research/optimization-task")
    def submit_strategy_optimization_task(
        strategy_id: str,
        body: ResearchOptimizationTaskRequest | None = None,
        current_user=Depends(get_current_user),
    ):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        try:
            strategy = service.get_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except StrategyAccessDeniedError:
            strategy = None
        if strategy is None:
            return _access_denied_response()

        if signal_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="SIGNAL_EXECUTION_UNAVAILABLE",
                    message="signal execution is not configured",
                ),
            )

        metrics = signal_service.performance_statistics(user_id=current_user.id, strategy_id=strategy_id)
        average_pnl = float(metrics.get("averagePnl", 0.0))
        suggestion = "保持当前参数" if average_pnl >= 0 else "降低风险敞口"

        now = datetime.now().isoformat()
        result = {
            "strategyId": strategy_id,
            "generatedAt": now,
            "parameterRange": {
                "template": strategy.template,
            },
            "suggestions": [
                {
                    "code": "OPTIMIZE_PNL",
                    "message": suggestion,
                    "metrics": metrics,
                }
            ],
        }

        job_idempotency_key = ((body.idempotency_key if body is not None else None) or f"strategy-optimization-task:{strategy_id}:{uuid4()}")

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="strategy_optimization_suggest",
                payload={
                    "strategyId": strategy_id,
                },
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except IdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(
            data={
                "taskId": job.id,
                "taskType": job.task_type,
                "status": job.status,
                "result": job.result,
            }
        )

    return router
