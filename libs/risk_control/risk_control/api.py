"""risk_control FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from job_orchestration.service import (
    IdempotencyConflictError as JobIdempotencyConflictError,
)
from job_orchestration.service import JobOrchestrationService
from pydantic import BaseModel, Field

from platform_core.response import error_response, success_response
from risk_control.domain import RiskAlert, RiskAssessmentSnapshot, RiskRule
from risk_control.service import AccountAccessDeniedError, RiskControlService


class RuleCreateRequest(BaseModel):
    account_id: str = Field(alias="accountId")
    strategy_id: str | None = Field(default=None, alias="strategyId")
    rule_name: str = Field(alias="ruleName")
    threshold: float

    model_config = {"populate_by_name": True}


class RuleUpdateRequest(BaseModel):
    strategy_id: str | None = Field(default=None, alias="strategyId")
    rule_name: str | None = Field(default=None, alias="ruleName")
    threshold: float | None = None

    model_config = {"populate_by_name": True}


class RuleToggleRequest(BaseModel):
    is_active: bool = Field(alias="isActive")

    model_config = {"populate_by_name": True}


class BatchAcknowledgeRequest(BaseModel):
    alert_ids: list[str] = Field(alias="alertIds")

    model_config = {"populate_by_name": True}


class EvaluateTaskRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class BatchCheckTaskRequest(BaseModel):
    account_ids: list[str] = Field(alias="accountIds")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class ReportGenerateTaskRequest(BaseModel):
    report_type: str = Field(alias="reportType")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class ContinuousMonitorTaskRequest(BaseModel):
    account_ids: list[str] = Field(alias="accountIds")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class SnapshotGenerateAllTaskRequest(BaseModel):
    account_ids: list[str] = Field(alias="accountIds")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class AlertCleanupTaskRequest(BaseModel):
    retention_days: int = Field(alias="retentionDays")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _rule_payload(rule: RiskRule) -> dict:
    return {
        "id": rule.id,
        "userId": rule.user_id,
        "accountId": rule.account_id,
        "strategyId": rule.strategy_id,
        "ruleName": rule.rule_name,
        "threshold": rule.threshold,
        "isActive": rule.is_active,
        "createdAt": _dt(rule.created_at),
        "updatedAt": _dt(rule.updated_at),
    }


def _alert_payload(alert: RiskAlert) -> dict:
    return {
        "id": alert.id,
        "userId": alert.user_id,
        "accountId": alert.account_id,
        "ruleName": alert.rule_name,
        "severity": alert.severity,
        "message": alert.message,
        "status": alert.status,
        "createdAt": _dt(alert.created_at),
        "acknowledgedAt": _dt(alert.acknowledged_at),
        "acknowledgedBy": alert.acknowledged_by,
        "resolvedAt": _dt(alert.resolved_at),
        "resolvedBy": alert.resolved_by,
        "notificationStatus": alert.notification_status,
        "notifiedAt": _dt(alert.notified_at),
        "notifiedBy": alert.notified_by,
    }


def _assessment_payload(snapshot: RiskAssessmentSnapshot) -> dict:
    return {
        "assessmentId": snapshot.id,
        "accountId": snapshot.account_id,
        "strategyId": snapshot.strategy_id,
        "riskScore": snapshot.risk_score,
        "riskLevel": snapshot.risk_level,
        "triggeredRuleIds": snapshot.triggered_rule_ids,
        "createdAt": _dt(snapshot.created_at),
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
    service: RiskControlService,
    get_current_user: Any,
    job_service: JobOrchestrationService | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/risk/batch/check-task")
    def batch_check_task(body: BatchCheckTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or f"risk-batch-check:{','.join(body.account_ids)}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="risk_batch_check",
                payload={"accountIds": body.account_ids},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.batch_check_accounts(user_id=current_user.id, account_ids=body.account_ids)
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.post("/risk/reports/generate-task")
    def generate_report_task(body: ReportGenerateTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or f"risk-report-generate:{body.report_type}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="risk_report_generate",
                payload={"reportType": body.report_type},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            report = service.generate_risk_report(user_id=current_user.id, report_type=body.report_type)
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=report)
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

    @router.post("/risk/alerts/notify-task")
    def notify_alert_task(body: EvaluateTaskRequest | None = None, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = (body.idempotency_key if body is not None else None) or "risk-alert-notify"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="risk_alert_notify",
                payload={},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result, _audit_id = service.notify_pending_alerts(user_id=current_user.id, actor_id=current_user.id)
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

    @router.post("/risk/monitor/continuous-task")
    def continuous_monitor_task(body: ContinuousMonitorTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or "risk-continuous-monitor"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="risk_continuous_monitor",
                payload={"accountIds": body.account_ids},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.submit_continuous_monitor(user_id=current_user.id, account_ids=body.account_ids)
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.get("/risk/monitor/continuous-task/{task_id}")
    def continuous_monitor_task_status(task_id: str, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job = job_service.get_job(user_id=current_user.id, job_id=task_id)
        if job is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code="TASK_NOT_FOUND", message="task not found"),
            )
        return success_response(data=_job_payload(job))

    @router.post("/risk/snapshots/generate-all-task")
    def generate_all_snapshots_task(body: SnapshotGenerateAllTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or "risk-snapshot-generate-all"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="risk_snapshot_generate_all",
                payload={"accountIds": body.account_ids},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            result = service.generate_all_snapshots(user_id=current_user.id, account_ids=body.account_ids)
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=result)
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.post("/risk/accounts/{account_id}/snapshot-task")
    def generate_account_snapshot_task(
        account_id: str,
        body: EvaluateTaskRequest | None = None,
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

        job_idempotency_key = (body.idempotency_key if body is not None else None) or f"risk-snapshot-account:{account_id}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="risk_snapshot_generate_account",
                payload={"accountId": account_id},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            snapshot = service.generate_account_snapshot(user_id=current_user.id, account_id=account_id)
            job = job_service.succeed_job(user_id=current_user.id, job_id=job.id, result=_assessment_payload(snapshot))
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.post("/risk/alerts/cleanup-task")
    def cleanup_alerts_task(body: AlertCleanupTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or f"risk-alert-cleanup:{body.retention_days}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="risk_alert_cleanup",
                payload={"retentionDays": body.retention_days},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            deleted, audit_id = service.cleanup_resolved_alerts(
                user_id=current_user.id,
                retention_days=body.retention_days,
            )
            job = job_service.succeed_job(
                user_id=current_user.id,
                job_id=job.id,
                result={"deleted": deleted, "auditId": audit_id},
            )
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(code="ALERT_CLEANUP_INVALID", message=str(exc)),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.post("/risk/rules")
    def create_rule(body: RuleCreateRequest, current_user=Depends(get_current_user)):
        try:
            rule = service.create_rule(
                user_id=current_user.id,
                account_id=body.account_id,
                strategy_id=body.strategy_id,
                rule_name=body.rule_name,
                threshold=body.threshold,
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="RULE_ACCESS_DENIED",
                    message="rule does not belong to current user",
                ),
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(code="RULE_INVALID", message=str(exc)),
            )

        return success_response(data=_rule_payload(rule))

    @router.get("/risk/rules")
    def list_rules(
        account_id: str | None = Query(default=None, alias="accountId"),
        strategy_id: str | None = Query(default=None, alias="strategyId"),
        is_active: bool | None = Query(default=None, alias="isActive"),
        current_user=Depends(get_current_user),
    ):
        try:
            rules = service.list_rules(
                user_id=current_user.id,
                account_id=account_id,
                strategy_id=strategy_id,
                is_active=is_active,
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="RULE_ACCESS_DENIED",
                    message="rule does not belong to current user",
                ),
            )

        return success_response(data=[_rule_payload(item) for item in rules])

    @router.get("/risk/rules/{rule_id}")
    def get_rule(rule_id: str, current_user=Depends(get_current_user)):
        rule = service.get_rule(user_id=current_user.id, rule_id=rule_id)
        if rule is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code="RULE_NOT_FOUND", message="rule not found"),
            )
        return success_response(data=_rule_payload(rule))

    @router.put("/risk/rules/{rule_id}")
    def update_rule(rule_id: str, body: RuleUpdateRequest, current_user=Depends(get_current_user)):
        updated = service.update_rule(
            user_id=current_user.id,
            rule_id=rule_id,
            strategy_id=body.strategy_id,
            rule_name=body.rule_name,
            threshold=body.threshold,
        )
        if updated is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code="RULE_NOT_FOUND", message="rule not found"),
            )
        return success_response(data=_rule_payload(updated))

    @router.delete("/risk/rules/{rule_id}")
    def delete_rule(rule_id: str, current_user=Depends(get_current_user)):
        deleted = service.delete_rule(user_id=current_user.id, rule_id=rule_id)
        if not deleted:
            return JSONResponse(
                status_code=404,
                content=error_response(code="RULE_NOT_FOUND", message="rule not found"),
            )
        return success_response(data={"deleted": True})

    @router.patch("/risk/rules/{rule_id}/toggle")
    def toggle_rule(rule_id: str, body: RuleToggleRequest, current_user=Depends(get_current_user)):
        try:
            toggled = service.toggle_rule_status(
                user_id=current_user.id,
                rule_id=rule_id,
                is_active=body.is_active,
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="RULE_ACCESS_DENIED",
                    message="rule does not belong to current user",
                ),
            )

        if toggled is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code="RULE_NOT_FOUND", message="rule not found"),
            )

        return success_response(data=_rule_payload(toggled))

    @router.get("/risk/rules/applicable/{account_id}")
    def applicable_rules(
        account_id: str,
        strategy_id: str | None = Query(default=None, alias="strategyId"),
        current_user=Depends(get_current_user),
    ):
        try:
            rules = service.list_applicable_rules(
                user_id=current_user.id,
                account_id=account_id,
                strategy_id=strategy_id,
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="RULE_ACCESS_DENIED",
                    message="rule does not belong to current user",
                ),
            )

        return success_response(data=[_rule_payload(item) for item in rules])

    @router.post("/risk/check/account/{account_id}")
    def check_account_risk(account_id: str, current_user=Depends(get_current_user)):
        try:
            snapshot = service.assess_account_risk(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )

        return success_response(data=_assessment_payload(snapshot))

    @router.get("/risk/accounts/{account_id}/snapshot")
    def get_account_assessment_snapshot(account_id: str, current_user=Depends(get_current_user)):
        try:
            snapshot = service.get_account_assessment_snapshot(
                user_id=current_user.id,
                account_id=account_id,
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )

        if snapshot is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code="ASSESSMENT_NOT_FOUND", message="assessment snapshot not found"),
            )

        return success_response(data=_assessment_payload(snapshot))

    @router.post("/risk/accounts/{account_id}/evaluate")
    def evaluate_account_risk(account_id: str, current_user=Depends(get_current_user)):
        try:
            snapshot = service.evaluate_account_risk(
                user_id=current_user.id,
                account_id=account_id,
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )

        return success_response(data=_assessment_payload(snapshot))

    @router.post("/risk/accounts/{account_id}/evaluate-task")
    def evaluate_account_risk_task(
        account_id: str,
        body: EvaluateTaskRequest | None = None,
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
            service.list_rules(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )

        job_idempotency_key = (body.idempotency_key if body is not None else None) or f"risk-account-evaluate:{account_id}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="risk_account_evaluate",
                payload={"accountId": account_id},
                idempotency_key=job_idempotency_key,
            )
            job_service.start_job(user_id=current_user.id, job_id=job.id)
            snapshot = service.evaluate_account_risk(
                user_id=current_user.id,
                account_id=account_id,
            )
            job = job_service.succeed_job(
                user_id=current_user.id,
                job_id=job.id,
                result=_assessment_payload(snapshot),
            )
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

    @router.post("/risk/check/strategy/{strategy_id}")
    def check_strategy_risk(
        strategy_id: str,
        account_id: str = Query(alias="accountId"),
        current_user=Depends(get_current_user),
    ):
        try:
            snapshot = service.assess_strategy_risk(
                user_id=current_user.id,
                account_id=account_id,
                strategy_id=strategy_id,
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )

        return success_response(data=_assessment_payload(snapshot))

    @router.get("/risk/dashboard/{account_id}")
    def risk_dashboard(account_id: str, current_user=Depends(get_current_user)):
        try:
            dashboard = service.get_risk_dashboard(user_id=current_user.id, account_id=account_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(code="RULE_ACCESS_DENIED", message="account does not belong to current user"),
            )
        return success_response(data=dashboard)

    @router.get("/risk/alerts")
    def list_alerts(
        account_id: str | None = Query(default=None, alias="accountId"),
        unresolved_only: bool = Query(default=False, alias="unresolvedOnly"),
        current_user=Depends(get_current_user),
    ):
        try:
            alerts = service.list_alerts(
                user_id=current_user.id,
                account_id=account_id,
                unresolved_only=unresolved_only,
            )
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ALERT_ACCESS_DENIED",
                    message="alert does not belong to current user",
                ),
            )

        return success_response(data=[_alert_payload(item) for item in alerts])

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

    @router.get("/risk/alerts/{alert_id}")
    def get_alert(alert_id: str, current_user=Depends(get_current_user)):
        alert = service.get_alert(user_id=current_user.id, alert_id=alert_id)
        if alert is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code="ALERT_NOT_FOUND", message="alert not found"),
            )
        return success_response(data=_alert_payload(alert))

    @router.patch("/risk/alerts/{alert_id}/acknowledge")
    def acknowledge_alert(alert_id: str, current_user=Depends(get_current_user)):
        try:
            alert = service.acknowledge_alert(user_id=current_user.id, alert_id=alert_id)
        except AccountAccessDeniedError:
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code="ALERT_ACCESS_DENIED",
                    message="alert does not belong to current user",
                ),
            )

        if alert is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code="ALERT_NOT_FOUND", message="alert not found"),
            )

        return success_response(data=_alert_payload(alert))

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

    return router
