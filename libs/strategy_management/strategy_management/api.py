"""strategy_management FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from platform_core.response import error_response, success_response
from strategy_management.domain import StrategyInUseError
from strategy_management.service import StrategyService


class CreateStrategyRequest(BaseModel):
    name: str
    template: str
    parameters: dict[str, Any] = Field(default_factory=dict)


def _dt(value: datetime) -> str:
    return value.isoformat()


def _serialize_strategy(strategy) -> dict[str, Any]:
    return {
        "id": strategy.id,
        "userId": strategy.user_id,
        "name": strategy.name,
        "template": strategy.template,
        "parameters": strategy.parameters,
        "createdAt": _dt(strategy.created_at),
        "updatedAt": _dt(strategy.updated_at),
    }


def create_router(*, service: StrategyService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/strategies")
    def list_strategies(current_user=Depends(get_current_user)):
        items = service.list_strategies(user_id=current_user.id)
        return success_response(data=[_serialize_strategy(item) for item in items])

    @router.get("/strategies/{strategy_id}")
    def get_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        strategy = service.get_strategy(user_id=current_user.id, strategy_id=strategy_id)
        if strategy is None:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="STRATEGY_ACCESS_DENIED",
                    message="strategy does not belong to current user",
                ),
            )
        return success_response(data=_serialize_strategy(strategy))

    @router.post("/strategies")
    def create_strategy(body: CreateStrategyRequest, current_user=Depends(get_current_user)):
        created = service.create_strategy(
            user_id=current_user.id,
            name=body.name,
            template=body.template,
            parameters=body.parameters,
        )
        return success_response(data=_serialize_strategy(created))

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
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="STRATEGY_ACCESS_DENIED",
                    message="strategy does not belong to current user",
                ),
            )

        return success_response(data={"deleted": True})

    return router
