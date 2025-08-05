"""backtest_runner FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backtest_runner.domain import InvalidBacktestTransitionError
from backtest_runner.service import (
    BacktestAccessDeniedError,
    BacktestIdempotencyConflictError,
    BacktestService,
)
from platform_core.response import error_response, paged_response, success_response


class CreateBacktestRequest(BaseModel):
    strategy_id: str = Field(alias="strategyId")
    config: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class TransitionRequest(BaseModel):
    to_status: str = Field(alias="toStatus")
    metrics: dict[str, float] | None = Field(default=None)

    model_config = {"populate_by_name": True}


class CompareRequest(BaseModel):
    task_ids: list[str] = Field(alias="taskIds")

    model_config = {"populate_by_name": True}


def _dt(value: datetime) -> str:
    return value.isoformat()


def _serialize_task(task) -> dict[str, Any]:
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
            code="BACKTEST_ACCESS_DENIED",
            message="backtest task does not belong to current user",
        ),
    )


def create_router(*, service: BacktestService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/backtests")
    def create_backtest(body: CreateBacktestRequest, current_user=Depends(get_current_user)):
        try:
            task = service.create_task(
                user_id=current_user.id,
                strategy_id=body.strategy_id,
                config=body.config,
                idempotency_key=body.idempotency_key,
            )
        except BacktestIdempotencyConflictError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="BACKTEST_IDEMPOTENCY_CONFLICT",
                    message=str(exc),
                ),
            )
        return success_response(data=_serialize_task(task))

    @router.get("/backtests")
    def list_backtests(
        current_user=Depends(get_current_user),
        status: str | None = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, alias="pageSize", ge=1, le=200),
    ):
        listing = service.list_tasks(
            user_id=current_user.id,
            status=status,
            page=page,
            page_size=page_size,
        )
        return paged_response(
            items=[_serialize_task(item) for item in listing["items"]],
            total=listing["total"],
            page=listing["page"],
            page_size=listing["pageSize"],
        )

    @router.get("/backtests/statistics")
    def backtest_statistics(current_user=Depends(get_current_user)):
        return success_response(data=service.statistics(user_id=current_user.id))

    @router.post("/backtests/compare")
    def compare_backtests(body: CompareRequest, current_user=Depends(get_current_user)):
        try:
            compared = service.compare_tasks(user_id=current_user.id, task_ids=body.task_ids)
        except BacktestAccessDeniedError:
            return _access_denied_response()
        return success_response(data=compared)

    @router.get("/backtests/{task_id}")
    def get_backtest(task_id: str, current_user=Depends(get_current_user)):
        task = service.get_task(user_id=current_user.id, task_id=task_id)
        if task is None:
            return _access_denied_response()

        return success_response(data=_serialize_task(task))

    @router.post("/backtests/{task_id}/transition")
    def transition_backtest(
        task_id: str,
        body: TransitionRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            task = service.transition(
                user_id=current_user.id,
                task_id=task_id,
                to_status=body.to_status,
                metrics=body.metrics,
            )
        except InvalidBacktestTransitionError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(
                    code="INVALID_TRANSITION",
                    message=str(exc),
                ),
            )

        if task is None:
            return _access_denied_response()

        return success_response(data=_serialize_task(task))

    @router.post("/backtests/{task_id}/cancel")
    def cancel_backtest(task_id: str, current_user=Depends(get_current_user)):
        try:
            task = service.cancel_task(user_id=current_user.id, task_id=task_id)
        except InvalidBacktestTransitionError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(code="INVALID_TRANSITION", message=str(exc)),
            )
        if task is None:
            return _access_denied_response()
        return success_response(data=_serialize_task(task))

    @router.post("/backtests/{task_id}/retry")
    def retry_backtest(task_id: str, current_user=Depends(get_current_user)):
        try:
            task = service.retry_task(user_id=current_user.id, task_id=task_id)
        except InvalidBacktestTransitionError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(code="INVALID_TRANSITION", message=str(exc)),
            )
        if task is None:
            return _access_denied_response()
        return success_response(data=_serialize_task(task))

    return router
