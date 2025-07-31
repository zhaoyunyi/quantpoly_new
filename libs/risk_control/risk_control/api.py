"""risk_control FastAPI 路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from platform_core.response import error_response, success_response
from risk_control.service import AccountAccessDeniedError, RiskControlService


class BatchAcknowledgeRequest(BaseModel):
    alert_ids: list[str] = Field(alias="alertIds")

    model_config = {"populate_by_name": True}


def create_router(*, service: RiskControlService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/risk/alerts/batch-acknowledge")
    def batch_acknowledge(body: BatchAcknowledgeRequest, current_user=Depends(get_current_user)):
        try:
            affected = service.batch_acknowledge(user_id=current_user.id, alert_ids=body.alert_ids)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ALERT_ACCESS_DENIED",
                    message="alert does not belong to current user",
                ),
            )

        return success_response(data={"affected": affected})

    @router.post("/risk/alerts/{alert_id}/resolve")
    def resolve_alert(alert_id: str, current_user=Depends(get_current_user)):
        try:
            service.resolve_alert(user_id=current_user.id, alert_id=alert_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ALERT_ACCESS_DENIED",
                    message="alert does not belong to current user",
                ),
            )

        return success_response(data={"resolved": True})

    @router.get("/risk/alerts/stats")
    def alert_stats(
        account_id: str | None = Query(default=None, alias="accountId"),
        current_user=Depends(get_current_user),
    ):
        try:
            stats = service.alert_stats(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ALERT_ACCESS_DENIED",
                    message="alert does not belong to current user",
                ),
            )

        return success_response(
            data={
                "total": stats.total,
                "open": stats.open,
                "acknowledged": stats.acknowledged,
                "resolved": stats.resolved,
                "bySeverity": stats.by_severity,
            }
        )

    return router
