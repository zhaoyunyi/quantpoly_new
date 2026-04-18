"""strategy_health FastAPI 路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from platform_core.response import error_response, paged_response, success_response
from strategy_health.service import HealthReportExecutionError, StrategyHealthService


class CreateHealthReportRequest(BaseModel):
    template: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    symbol: str | None = None
    start_date: str | None = Field(default=None, alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")
    initial_capital: float = Field(default=100000, alias="initialCapital")
    commission_rate: float = Field(default=0.0, alias="commissionRate")
    strategy_id: str | None = Field(default=None, alias="strategyId")
    timeframe: str = "1Day"
    prices: list[float] | None = None

    model_config = {"populate_by_name": True}


def _serialize_report(report) -> dict[str, Any]:
    base: dict[str, Any] = {
        "reportId": report.id,
        "userId": report.user_id,
        "strategyId": report.strategy_id,
        "status": report.status,
        "createdAt": report.created_at.isoformat(),
    }
    if report.completed_at:
        base["completedAt"] = report.completed_at.isoformat()
    if report.report:
        base.update(report.report)
    return base


def create_router(
    *,
    service: StrategyHealthService,
    get_current_user: Any,
) -> APIRouter:
    router = APIRouter()

    @router.post("/strategy-health")
    def create_health_report(body: CreateHealthReportRequest, current_user=Depends(get_current_user)):
        config: dict[str, Any] = {
            "template": body.template,
            "parameters": body.parameters,
            "initialCapital": body.initial_capital,
            "commissionRate": body.commission_rate,
            "timeframe": body.timeframe,
        }
        if body.symbol:
            config["symbol"] = body.symbol
        if body.start_date:
            config["startDate"] = body.start_date
        if body.end_date:
            config["endDate"] = body.end_date
        if body.strategy_id:
            config["strategyId"] = body.strategy_id
        if body.prices:
            config["prices"] = body.prices

        report = service.create_report(user_id=current_user.id, config=config)

        try:
            report = service.execute_report(user_id=current_user.id, report_id=report.id)
        except HealthReportExecutionError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(code=exc.code, message=exc.message),
            )

        return success_response(data=_serialize_report(report))

    @router.get("/strategy-health/{report_id}")
    def get_health_report(report_id: str, current_user=Depends(get_current_user)):
        report = service.get_report(user_id=current_user.id, report_id=report_id)
        if report is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code="REPORT_NOT_FOUND", message="report not found"),
            )
        return success_response(data=_serialize_report(report))

    @router.get("/strategy-health")
    def list_health_reports(
        current_user=Depends(get_current_user),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, alias="pageSize", ge=1, le=200),
    ):
        listing = service.list_reports(user_id=current_user.id, page=page, page_size=page_size)
        return paged_response(
            items=[_serialize_report(item) for item in listing["items"]],
            total=listing["total"],
            page=listing["page"],
            page_size=listing["pageSize"],
        )

    return router
