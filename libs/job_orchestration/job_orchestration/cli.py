"""job_orchestration CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from job_orchestration.domain import InvalidJobTransitionError
from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import (
    IdempotencyConflictError,
    JobAccessDeniedError,
    JobOrchestrationService,
    ScheduleAccessDeniedError,
)

_repo = InMemoryJobRepository()
_scheduler = InMemoryScheduler()
_service = JobOrchestrationService(repository=_repo, scheduler=_scheduler)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _dt(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _serialize_job(job) -> dict:
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


def _serialize_schedule(schedule) -> dict:
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


def _cmd_submit(args: argparse.Namespace) -> None:
    try:
        payload = json.loads(args.payload) if args.payload else {}
    except json.JSONDecodeError:
        _output({"success": False, "error": {"code": "INVALID_PAYLOAD", "message": "invalid payload json"}})
        return

    try:
        job = _service.submit_job(
            user_id=args.user_id,
            task_type=args.task_type,
            payload=payload,
            idempotency_key=args.idempotency_key,
        )
    except IdempotencyConflictError:
        _output(
            {
                "success": False,
                "error": {"code": "IDEMPOTENCY_CONFLICT", "message": "idempotency key already exists"},
            }
        )
        return
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_ARGUMENT", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_job(job), "runtime": _service.runtime_status()})


def _cmd_status(args: argparse.Namespace) -> None:
    job = _service.get_job(user_id=args.user_id, job_id=args.job_id)
    if job is None:
        _output({"success": False, "error": {"code": "JOB_NOT_FOUND", "message": "job not found"}})
        return
    _output({"success": True, "data": _serialize_job(job), "runtime": _service.runtime_status()})


def _cmd_transition(args: argparse.Namespace) -> None:
    try:
        job = _service.transition_job(user_id=args.user_id, job_id=args.job_id, to_status=args.to_status)
    except JobAccessDeniedError:
        _output({"success": False, "error": {"code": "JOB_ACCESS_DENIED", "message": "job access denied"}})
        return
    except InvalidJobTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_job(job), "runtime": _service.runtime_status()})


def _cmd_cancel(args: argparse.Namespace) -> None:
    try:
        job = _service.cancel_job(user_id=args.user_id, job_id=args.job_id)
    except JobAccessDeniedError:
        _output({"success": False, "error": {"code": "JOB_ACCESS_DENIED", "message": "job access denied"}})
        return
    except InvalidJobTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_job(job), "runtime": _service.runtime_status()})


def _cmd_retry(args: argparse.Namespace) -> None:
    try:
        job = _service.retry_job(user_id=args.user_id, job_id=args.job_id)
    except JobAccessDeniedError:
        _output({"success": False, "error": {"code": "JOB_ACCESS_DENIED", "message": "job access denied"}})
        return
    except InvalidJobTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_job(job), "runtime": _service.runtime_status()})


def _cmd_types(_args: argparse.Namespace) -> None:
    _output({"success": True, "data": _service.task_type_registry(), "runtime": _service.runtime_status()})


def _cmd_runtime(_args: argparse.Namespace) -> None:
    _output({"success": True, "data": _service.runtime_status()})


def _cmd_schedule_interval(args: argparse.Namespace) -> None:
    try:
        schedule = _service.schedule_interval(
            user_id=args.user_id,
            task_type=args.task_type,
            every_seconds=args.every_seconds,
        )
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_ARGUMENT", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_schedule(schedule), "runtime": _service.runtime_status()})


def _cmd_schedule_cron(args: argparse.Namespace) -> None:
    try:
        schedule = _service.schedule_cron(
            user_id=args.user_id,
            task_type=args.task_type,
            cron_expr=args.cron_expr,
        )
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_ARGUMENT", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_schedule(schedule), "runtime": _service.runtime_status()})


def _cmd_schedules(args: argparse.Namespace) -> None:
    schedules = _service.list_schedules(user_id=args.user_id)
    _output({
        "success": True,
        "data": [_serialize_schedule(item) for item in schedules],
        "runtime": _service.runtime_status(),
    })


def _cmd_schedule_stop(args: argparse.Namespace) -> None:
    try:
        schedule = _service.stop_schedule(user_id=args.user_id, schedule_id=args.schedule_id)
    except ScheduleAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {"code": "SCHEDULE_ACCESS_DENIED", "message": "schedule access denied"},
            }
        )
        return

    _output({"success": True, "data": _serialize_schedule(schedule), "runtime": _service.runtime_status()})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-orchestration", description="QuantPoly 任务编排 CLI")
    sub = parser.add_subparsers(dest="command")

    submit = sub.add_parser("submit", help="提交任务")
    submit.add_argument("--user-id", required=True)
    submit.add_argument("--task-type", required=True)
    submit.add_argument("--payload", default="{}")
    submit.add_argument("--idempotency-key", required=True)

    status = sub.add_parser("status", help="查询任务")
    status.add_argument("--user-id", required=True)
    status.add_argument("--job-id", required=True)

    transition = sub.add_parser("transition", help="任务状态迁移")
    transition.add_argument("--user-id", required=True)
    transition.add_argument("--job-id", required=True)
    transition.add_argument("--to-status", required=True, dest="to_status")

    cancel = sub.add_parser("cancel", help="取消任务")
    cancel.add_argument("--user-id", required=True)
    cancel.add_argument("--job-id", required=True)

    retry = sub.add_parser("retry", help="重试任务")
    retry.add_argument("--user-id", required=True)
    retry.add_argument("--job-id", required=True)

    sub.add_parser("types", help="列出任务类型注册表")
    sub.add_parser("runtime", help="查询执行器与调度恢复状态")

    schedule_interval = sub.add_parser("schedule-interval", help="创建 interval 调度")
    schedule_interval.add_argument("--user-id", required=True)
    schedule_interval.add_argument("--task-type", required=True)
    schedule_interval.add_argument("--every-seconds", required=True, type=int, dest="every_seconds")

    schedule_cron = sub.add_parser("schedule-cron", help="创建 cron 调度")
    schedule_cron.add_argument("--user-id", required=True)
    schedule_cron.add_argument("--task-type", required=True)
    schedule_cron.add_argument("--cron-expr", required=True, dest="cron_expr")

    schedules = sub.add_parser("schedules", help="列出当前用户调度")
    schedules.add_argument("--user-id", required=True)

    schedule_stop = sub.add_parser("schedule-stop", help="停止调度")
    schedule_stop.add_argument("--user-id", required=True)
    schedule_stop.add_argument("--schedule-id", required=True)

    return parser


_COMMANDS = {
    "submit": _cmd_submit,
    "status": _cmd_status,
    "transition": _cmd_transition,
    "cancel": _cmd_cancel,
    "retry": _cmd_retry,
    "types": _cmd_types,
    "runtime": _cmd_runtime,
    "schedule-interval": _cmd_schedule_interval,
    "schedule-cron": _cmd_schedule_cron,
    "schedules": _cmd_schedules,
    "schedule-stop": _cmd_schedule_stop,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
