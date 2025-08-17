"""risk_control CLI。"""

from __future__ import annotations

import argparse
import json
import sys

from risk_control.repository import InMemoryRiskRepository
from risk_control.service import AccountAccessDeniedError, RiskControlService

_repo = InMemoryRiskRepository()
_service = RiskControlService(repository=_repo, account_owner_acl=lambda _user_id, _account_id: True)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _serialize_assessment(snapshot) -> dict:
    return {
        "assessmentId": snapshot.id,
        "accountId": snapshot.account_id,
        "strategyId": snapshot.strategy_id,
        "riskScore": snapshot.risk_score,
        "riskLevel": snapshot.risk_level,
        "triggeredRuleIds": snapshot.triggered_rule_ids,
        "createdAt": snapshot.created_at.isoformat(),
    }


def _cmd_assessment_snapshot(args: argparse.Namespace) -> None:
    try:
        snapshot = _service.get_account_assessment_snapshot(
            user_id=args.user_id,
            account_id=args.account_id,
        )
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "RULE_ACCESS_DENIED",
                    "message": "account does not belong to current user",
                },
            }
        )
        return

    if snapshot is None:
        _output(
            {
                "success": False,
                "error": {
                    "code": "ASSESSMENT_NOT_FOUND",
                    "message": "assessment snapshot not found",
                },
            }
        )
        return

    _output({"success": True, "data": _serialize_assessment(snapshot)})


def _cmd_assessment_evaluate(args: argparse.Namespace) -> None:
    try:
        snapshot = _service.evaluate_account_risk(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "RULE_ACCESS_DENIED",
                    "message": "account does not belong to current user",
                },
            }
        )
        return

    _output({"success": True, "data": _serialize_assessment(snapshot)})


def _cmd_stats(args: argparse.Namespace) -> None:
    try:
        stats = _service.alert_stats(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "ALERT_ACCESS_DENIED",
                    "message": "alert does not belong to current user",
                },
            }
        )
        return

    _output(
        {
            "success": True,
            "data": {
                "total": stats.total,
                "open": stats.open,
                "acknowledged": stats.acknowledged,
                "resolved": stats.resolved,
                "bySeverity": stats.by_severity,
            },
        }
    )


def _cmd_batch_acknowledge(args: argparse.Namespace) -> None:
    alert_ids = [item.strip() for item in args.alert_ids.split(",") if item.strip()]
    try:
        affected = _service.batch_acknowledge(user_id=args.user_id, alert_ids=alert_ids)
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "ALERT_ACCESS_DENIED",
                    "message": "alert does not belong to current user",
                },
            }
        )
        return

    _output({"success": True, "data": {"affected": affected}})


def _cmd_applicable_rules(args: argparse.Namespace) -> None:
    try:
        rules = _service.list_applicable_rules(
            user_id=args.user_id,
            account_id=args.account_id,
            strategy_id=args.strategy_id,
        )
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "RULE_ACCESS_DENIED",
                    "message": "rule does not belong to current user",
                },
            }
        )
        return

    _output(
        {
            "success": True,
            "data": [
                {
                    "id": item.id,
                    "accountId": item.account_id,
                    "strategyId": item.strategy_id,
                    "ruleName": item.rule_name,
                    "threshold": item.threshold,
                    "isActive": item.is_active,
                }
                for item in rules
            ],
        }
    )


def _cmd_dashboard(args: argparse.Namespace) -> None:
    try:
        dashboard = _service.get_risk_dashboard(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "RULE_ACCESS_DENIED",
                    "message": "account does not belong to current user",
                },
            }
        )
        return

    _output({"success": True, "data": dashboard})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="risk-control", description="QuantPoly 风控 CLI")
    sub = parser.add_subparsers(dest="command")

    assessment_snapshot = sub.add_parser("assessment-snapshot", help="查询账户风险评估快照")
    assessment_snapshot.add_argument("--user-id", required=True)
    assessment_snapshot.add_argument("--account-id", required=True)

    assessment_evaluate = sub.add_parser("assessment-evaluate", help="触发账户风险评估")
    assessment_evaluate.add_argument("--user-id", required=True)
    assessment_evaluate.add_argument("--account-id", required=True)

    stats = sub.add_parser("stats", help="统计告警")
    stats.add_argument("--user-id", required=True)
    stats.add_argument("--account-id", default=None)

    batch = sub.add_parser("batch-acknowledge", help="批量确认告警")
    batch.add_argument("--user-id", required=True)
    batch.add_argument("--alert-ids", required=True)

    applicable = sub.add_parser("applicable-rules", help="查询账户适用规则")
    applicable.add_argument("--user-id", required=True)
    applicable.add_argument("--account-id", required=True)
    applicable.add_argument("--strategy-id", default=None)

    dashboard = sub.add_parser("dashboard", help="查询风控仪表盘")
    dashboard.add_argument("--user-id", required=True)
    dashboard.add_argument("--account-id", required=True)

    return parser


_COMMANDS = {
    "assessment-snapshot": _cmd_assessment_snapshot,
    "assessment-evaluate": _cmd_assessment_evaluate,
    "stats": _cmd_stats,
    "batch-acknowledge": _cmd_batch_acknowledge,
    "applicable-rules": _cmd_applicable_rules,
    "dashboard": _cmd_dashboard,
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
