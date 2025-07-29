"""backtest_runner FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backtest_runner.domain import InvalidBacktestTransitionError
from backtest_runner.service import BacktestService
from platform_core.response import error_response, success_response


class CreateBacktestRequest(BaseModel):
    strategy_id: str = Field(alias="strategyId")
    config: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class TransitionRequest(BaseModel):
    to_status: str = Field(alias="toStatus")

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
        "createdAt": _dt(task.created_at),
        "updatedAt": _dt(task.updated_at),
    }


def create_router(*, service: BacktestService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/backtests")
    def create_backtest(body: CreateBacktestRequest, current_user=Depends(get_current_user)):
        task = service.create_task(
            user_id=current_user.id,
            strategy_id=body.strategy_id,
            config=body.config,
        )
        return success_response(data=_serialize_task(task))

    @router.get("/backtests/{task_id}")
    def get_backtest(task_id: str, current_user=Depends(get_current_user)):
        task = service.get_task(user_id=current_user.id, task_id=task_id)
        if task is None:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="BACKTEST_ACCESS_DENIED",
                    message="backtest task does not belong to current user",
                ),
            )

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
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="BACKTEST_ACCESS_DENIED",
                    message="backtest task does not belong to current user",
                ),
            )

        return success_response(data=_serialize_task(task))

    return router
