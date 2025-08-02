"""admin_governance CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from admin_governance.audit import InMemoryAuditLog
from admin_governance.catalog import default_action_catalog
from admin_governance.policy import (
    ConfirmationRequiredError,
    GovernanceAccessDeniedError,
    GovernancePolicyEngine,
)
from admin_governance.token import InMemoryConfirmationTokenStore

_token_store = InMemoryConfirmationTokenStore()
_audit_log = InMemoryAuditLog()
_engine = GovernancePolicyEngine(
    action_catalog=default_action_catalog(),
    token_store=_token_store,
    audit_log=_audit_log,
)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _cmd_issue_token(args: argparse.Namespace) -> None:
    token = _token_store.issue(
        actor_id=args.actor_id,
        action=args.action,
        target=args.target,
        ttl_seconds=args.ttl,
    )
    _output({"success": True, "data": {"token": token}})


def _cmd_check_action(args: argparse.Namespace) -> None:
    try:
        result = _engine.authorize(
            actor_id=args.actor_id,
            role=args.role,
            level=args.level,
            action=args.action,
            target=args.target,
            confirmation_token=args.confirmation_token,
        )
    except GovernanceAccessDeniedError:
        _output({"success": False, "error": {"code": "GOVERNANCE_ACCESS_DENIED", "message": "access denied"}})
        return
    except ConfirmationRequiredError:
        _output({"success": False, "error": {"code": "CONFIRMATION_REQUIRED", "message": "confirmation required"}})
        return

    _output({"success": True, "data": {"allowed": result.allowed, "action": result.action}})


def _cmd_audit_list(_args: argparse.Namespace) -> None:
    rows = [
        {
            "actor": item.actor,
            "action": item.action,
            "target": item.target,
            "result": item.result,
            "timestamp": item.timestamp.isoformat(),
            "context": item.context,
        }
        for item in _audit_log.list_records()
    ]
    _output({"success": True, "data": rows})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="admin-governance", description="QuantPoly 管理员治理 CLI")
    sub = parser.add_subparsers(dest="command")

    issue = sub.add_parser("issue-token", help="签发确认令牌")
    issue.add_argument("--actor-id", required=True)
    issue.add_argument("--action", required=True)
    issue.add_argument("--target", required=True)
    issue.add_argument("--ttl", type=int, default=300)

    check = sub.add_parser("check-action", help="执行治理授权检查")
    check.add_argument("--actor-id", required=True)
    check.add_argument("--role", required=True)
    check.add_argument("--level", type=int, required=True)
    check.add_argument("--action", required=True)
    check.add_argument("--target", required=True)
    check.add_argument("--confirmation-token", default=None)

    sub.add_parser("audit-list", help="查看审计日志")

    return parser


_COMMANDS = {
    "issue-token": _cmd_issue_token,
    "check-action": _cmd_check_action,
    "audit-list": _cmd_audit_list,
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
