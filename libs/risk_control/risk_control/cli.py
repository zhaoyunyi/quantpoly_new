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


def _serialize_alert(alert) -> dict:
    return {
        "id": alert.id,
        "userId": alert.user_id,
        "accountId": alert.account_id,
        "ruleName": alert.rule_name,
        "severity": alert.severity,
        "message": alert.message,
        "status": alert.status,
        "createdAt": alert.created_at.isoformat(),
        "acknowledgedAt": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "acknowledgedBy": alert.acknowledged_by,
        "resolvedAt": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "resolvedBy": alert.resolved_by,
        "notificationStatus": alert.notification_status,
        "notifiedAt": alert.notified_at.isoformat() if alert.notified_at else None,
        "notifiedBy": alert.notified_by,
    }


def _cmd_report_generate(args: argparse.Namespace) -> None:
    report = _service.generate_risk_report(user_id=args.user_id, report_type=args.report_type)
    _output({"success": True, "data": report})


def _cmd_alert_cleanup(args: argparse.Namespace) -> None:
    try:
        deleted, audit_id = _service.cleanup_resolved_alerts(user_id=args.user_id, retention_days=args.retention_days)
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_ARGUMENT", "message": str(exc)}})
        return

    _output({"success": True, "data": {"deleted": deleted, "auditId": audit_id}})


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


def _cmd_rule_statistics(args: argparse.Namespace) -> None:
    try:
        stats = _service.rule_statistics(user_id=args.user_id, account_id=args.account_id)
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
            "data": {
                "total": stats["total"],
                "active": stats["active"],
                "inactive": stats["inactive"],
                "byState": stats["by_state"],
            },
        }
    )


def _cmd_recent_alerts(args: argparse.Namespace) -> None:
    try:
        alerts = _service.recent_alerts(
            user_id=args.user_id,
            account_id=args.account_id,
            limit=args.limit,
        )
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
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_ARGUMENT", "message": str(exc)}})
        return

    _output({"success": True, "data": [_serialize_alert(item) for item in alerts]})


def _cmd_unresolved_alerts(args: argparse.Namespace) -> None:
    try:
        alerts = _service.unresolved_alerts(
            user_id=args.user_id,
            account_id=args.account_id,
            limit=args.limit,
        )
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
    except ValueError as exc:
        _output({"success": False, "error": {"code": "INVALID_ARGUMENT", "message": str(exc)}})
        return

    _output({"success": True, "data": [_serialize_alert(item) for item in alerts]})


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

    rule_statistics = sub.add_parser("rule-statistics", help="统计规则状态")
    rule_statistics.add_argument("--user-id", required=True)
    rule_statistics.add_argument("--account-id", default=None)

    recent_alerts = sub.add_parser("recent-alerts", help="查询近期告警")
    recent_alerts.add_argument("--user-id", required=True)
    recent_alerts.add_argument("--account-id", default=None)
    recent_alerts.add_argument("--limit", type=int, default=20)

    unresolved_alerts = sub.add_parser("unresolved-alerts", help="查询未解决告警")
    unresolved_alerts.add_argument("--user-id", required=True)
    unresolved_alerts.add_argument("--account-id", default=None)
    unresolved_alerts.add_argument("--limit", type=int, default=20)

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

    report_generate = sub.add_parser("report-generate", help="生成风险报告")
    report_generate.add_argument("--user-id", required=True)
    report_generate.add_argument("--report-type", required=True)

    alert_cleanup = sub.add_parser("alert-cleanup", help="清理历史告警")
    alert_cleanup.add_argument("--user-id", required=True)
    alert_cleanup.add_argument("--retention-days", required=True, type=int, dest="retention_days")

    return parser


_COMMANDS = {
    "assessment-snapshot": _cmd_assessment_snapshot,
    "assessment-evaluate": _cmd_assessment_evaluate,
    "stats": _cmd_stats,
    "rule-statistics": _cmd_rule_statistics,
    "recent-alerts": _cmd_recent_alerts,
    "unresolved-alerts": _cmd_unresolved_alerts,
    "batch-acknowledge": _cmd_batch_acknowledge,
    "applicable-rules": _cmd_applicable_rules,
    "dashboard": _cmd_dashboard,
    "report-generate": _cmd_report_generate,
    "alert-cleanup": _cmd_alert_cleanup,
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
