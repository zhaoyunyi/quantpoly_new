"""job_orchestration FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from job_orchestration.domain import InvalidJobTransitionError
from job_orchestration.service import (
    IdempotencyConflictError,
    JobAccessDeniedError,
    JobOrchestrationService,
    ScheduleAccessDeniedError,
)
from platform_core.response import error_response, success_response


class JobSubmitRequest(BaseModel):
    task_type: str = Field(alias="taskType")
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class JobTransitionRequest(BaseModel):
    to_status: str = Field(alias="toStatus")

    model_config = {"populate_by_name": True}


class IntervalScheduleRequest(BaseModel):
    task_type: str = Field(alias="taskType")
    every_seconds: int = Field(alias="everySeconds", ge=1)

    model_config = {"populate_by_name": True}


class CronScheduleRequest(BaseModel):
    task_type: str = Field(alias="taskType")
    cron_expr: str = Field(alias="cronExpr")

    model_config = {"populate_by_name": True}


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _job_payload(job) -> dict[str, Any]:
    return {
        "id": job.id,
        "taskId": job.id,
        "userId": job.user_id,
        "taskType": job.task_type,
        "payload": job.payload,
        "idempotencyKey": job.idempotency_key,
        "status": job.status,
        "result": job.result,
        "error": {
            "code": job.error_code,
            "message": job.error_message,
        }
        if job.error_code or job.error_message
        else None,
        "executor": {
            "name": job.executor_name,
            "dispatchId": job.dispatch_id,
        }
        if job.executor_name or job.dispatch_id
        else None,
        "startedAt": _dt(job.started_at),
        "finishedAt": _dt(job.finished_at),
        "createdAt": _dt(job.created_at),
        "updatedAt": _dt(job.updated_at),
    }


def _schedule_payload(schedule) -> dict[str, Any]:
    return {
        "id": schedule.id,
        "userId": schedule.user_id,
        "namespace": schedule.namespace,
        "taskType": schedule.job_type,
        "scheduleType": schedule.schedule_type,
        "expression": schedule.expression,
        "status": schedule.status,
        "createdAt": _dt(schedule.created_at),
        "updatedAt": _dt(schedule.updated_at),
    }


def _job_access_denied_response() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=error_response(code="JOB_ACCESS_DENIED", message="job access denied"),
    )


def _schedule_access_denied_response() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=error_response(code="SCHEDULE_ACCESS_DENIED", message="schedule access denied"),
    )


def create_router(*, service: JobOrchestrationService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/jobs")
    def submit_job(body: JobSubmitRequest, current_user=Depends(get_current_user)):
        try:
            job = service.submit_job(
                user_id=current_user.id,
                task_type=body.task_type,
                payload=body.payload,
                idempotency_key=body.idempotency_key,
            )
        except IdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(code="INVALID_ARGUMENT", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.get("/jobs")
    def list_jobs(
        status: str | None = Query(default=None),
        task_type: str | None = Query(default=None, alias="taskType"),
        current_user=Depends(get_current_user),
    ):
        jobs = service.list_jobs(user_id=current_user.id, status=status, task_type=task_type)
        return success_response(data=[_job_payload(item) for item in jobs])

    @router.get("/jobs/task-types")
    def list_task_types(current_user=Depends(get_current_user)):
        del current_user
        return success_response(data=service.task_type_registry())

    @router.get("/jobs/runtime")
    def runtime_status(current_user=Depends(get_current_user)):
        del current_user
        return success_response(data=service.runtime_status())

    @router.post("/jobs/schedules/interval")
    def schedule_interval(body: IntervalScheduleRequest, current_user=Depends(get_current_user)):
        try:
            schedule = service.schedule_interval(
                user_id=current_user.id,
                task_type=body.task_type,
                every_seconds=body.every_seconds,
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(code="INVALID_ARGUMENT", message=str(exc)),
            )

        return success_response(data=_schedule_payload(schedule))

    @router.post("/jobs/schedules/cron")
    def schedule_cron(body: CronScheduleRequest, current_user=Depends(get_current_user)):
        try:
            schedule = service.schedule_cron(
                user_id=current_user.id,
                task_type=body.task_type,
                cron_expr=body.cron_expr,
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content=error_response(code="INVALID_ARGUMENT", message=str(exc)),
            )

        return success_response(data=_schedule_payload(schedule))

    @router.get("/jobs/schedules")
    def list_schedules(current_user=Depends(get_current_user)):
        schedules = service.list_schedules(user_id=current_user.id)
        return success_response(
            data={
                "items": [_schedule_payload(item) for item in schedules],
                "runtime": service.runtime_status(),
            }
        )

    @router.get("/jobs/schedules/{schedule_id}")
    def get_schedule(schedule_id: str, current_user=Depends(get_current_user)):
        schedule = service.get_schedule(user_id=current_user.id, schedule_id=schedule_id)
        if schedule is None:
            return _schedule_access_denied_response()
        return success_response(data=_schedule_payload(schedule))

    @router.post("/jobs/schedules/{schedule_id}/stop")
    def stop_schedule(schedule_id: str, current_user=Depends(get_current_user)):
        try:
            schedule = service.stop_schedule(user_id=current_user.id, schedule_id=schedule_id)
        except ScheduleAccessDeniedError:
            return _schedule_access_denied_response()
        return success_response(data=_schedule_payload(schedule))

    @router.get("/jobs/{job_id}")
    def get_job(job_id: str, current_user=Depends(get_current_user)):
        job = service.get_job(user_id=current_user.id, job_id=job_id)
        if job is None:
            return _job_access_denied_response()
        return success_response(data=_job_payload(job))

    @router.post("/jobs/{job_id}/transition")
    def transition_job(
        job_id: str,
        body: JobTransitionRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            job = service.transition_job(
                user_id=current_user.id,
                job_id=job_id,
                to_status=body.to_status,
            )
        except JobAccessDeniedError:
            return _job_access_denied_response()
        except InvalidJobTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(code="INVALID_TRANSITION", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.post("/jobs/{job_id}/cancel")
    def cancel_job(job_id: str, current_user=Depends(get_current_user)):
        try:
            job = service.cancel_job(user_id=current_user.id, job_id=job_id)
        except JobAccessDeniedError:
            return _job_access_denied_response()
        except InvalidJobTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(code="INVALID_TRANSITION", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.post("/jobs/{job_id}/retry")
    def retry_job(job_id: str, current_user=Depends(get_current_user)):
        try:
            job = service.retry_job(user_id=current_user.id, job_id=job_id)
        except JobAccessDeniedError:
            return _job_access_denied_response()
        except InvalidJobTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(code="INVALID_TRANSITION", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    return router
