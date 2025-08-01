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
)

_repo = InMemoryJobRepository()
_scheduler = InMemoryScheduler()
_service = JobOrchestrationService(repository=_repo, scheduler=_scheduler)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _serialize_job(job) -> dict:
    return {
        "id": job.id,
        "userId": job.user_id,
        "taskType": job.task_type,
        "payload": job.payload,
        "idempotencyKey": job.idempotency_key,
        "status": job.status,
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

    _output({"success": True, "data": _serialize_job(job)})


def _cmd_status(args: argparse.Namespace) -> None:
    job = _service.get_job(user_id=args.user_id, job_id=args.job_id)
    if job is None:
        _output({"success": False, "error": {"code": "JOB_NOT_FOUND", "message": "job not found"}})
        return
    _output({"success": True, "data": _serialize_job(job)})


def _cmd_cancel(args: argparse.Namespace) -> None:
    try:
        job = _service.cancel_job(user_id=args.user_id, job_id=args.job_id)
    except JobAccessDeniedError:
        _output({"success": False, "error": {"code": "JOB_ACCESS_DENIED", "message": "job access denied"}})
        return
    except InvalidJobTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_job(job)})


def _cmd_retry(args: argparse.Namespace) -> None:
    try:
        job = _service.retry_job(user_id=args.user_id, job_id=args.job_id)
    except JobAccessDeniedError:
        _output({"success": False, "error": {"code": "JOB_ACCESS_DENIED", "message": "job access denied"}})
        return
    except InvalidJobTransitionError as exc:
        _output({"success": False, "error": {"code": "INVALID_TRANSITION", "message": str(exc)}})
        return

    _output({"success": True, "data": _serialize_job(job)})


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

    cancel = sub.add_parser("cancel", help="取消任务")
    cancel.add_argument("--user-id", required=True)
    cancel.add_argument("--job-id", required=True)

    retry = sub.add_parser("retry", help="重试任务")
    retry.add_argument("--user-id", required=True)
    retry.add_argument("--job-id", required=True)

    return parser


_COMMANDS = {
    "submit": _cmd_submit,
    "status": _cmd_status,
    "cancel": _cmd_cancel,
    "retry": _cmd_retry,
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
