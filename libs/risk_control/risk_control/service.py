"""risk_control 应用服务。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from risk_control.domain import RiskAlert, RiskAssessmentSnapshot, RiskRule
from risk_control.repository import InMemoryRiskRepository


class AccountAccessDeniedError(PermissionError):
    """账户或报警不属于当前用户。"""


@dataclass
class RiskAlertStats:
    total: int
    open: int
    acknowledged: int
    resolved: int
    by_severity: dict[str, int]


class RiskControlService:
    def __init__(
        self,
        *,
        repository: InMemoryRiskRepository,
        account_owner_acl: Callable[[str, str], bool],
    ) -> None:
        self._repository = repository
        self._account_owner_acl = account_owner_acl

    def _assert_account_scope(self, *, user_id: str, account_id: str) -> None:
        if not self._account_owner_acl(user_id, account_id):
            raise AccountAccessDeniedError("account does not belong to current user")

    def _assert_positive_threshold(self, *, threshold: float) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")

    def _to_risk_level(self, *, score: float) -> str:
        if score >= 70:
            return "high"
        if score >= 30:
            return "medium"
        return "low"

    def _build_assessment(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None,
    ) -> RiskAssessmentSnapshot:
        rules = self.list_applicable_rules(user_id=user_id, account_id=account_id, strategy_id=strategy_id)
        if not rules:
            score = 0.0
            triggered_rule_ids: list[str] = []
        else:
            score = min(100.0, round(sum(item.threshold for item in rules) * 100 / len(rules), 2))
            triggered_rule_ids = [item.id for item in rules if item.threshold >= 0.2]

        snapshot = RiskAssessmentSnapshot.create(
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
            risk_score=score,
            risk_level=self._to_risk_level(score=score),
            triggered_rule_ids=triggered_rule_ids,
        )
        self._repository.save_assessment(snapshot)
        return snapshot

    def create_rule(
        self,
        *,
        user_id: str,
        account_id: str,
        rule_name: str,
        threshold: float,
        strategy_id: str | None = None,
    ) -> RiskRule:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        self._assert_positive_threshold(threshold=threshold)
        rule = RiskRule.create(
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
            rule_name=rule_name,
            threshold=threshold,
        )
        self._repository.save_rule(rule)
        return rule

    def list_rules(
        self,
        *,
        user_id: str,
        account_id: str | None = None,
        strategy_id: str | None = None,
        is_active: bool | None = None,
    ) -> list[RiskRule]:
        if account_id is not None:
            self._assert_account_scope(user_id=user_id, account_id=account_id)

        return self._repository.list_rules(
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
            is_active=is_active,
        )

    def rule_statistics(self, *, user_id: str, account_id: str | None = None) -> dict[str, int | dict[str, int]]:
        rules = self.list_rules(user_id=user_id, account_id=account_id)
        active = sum(1 for item in rules if item.is_active)
        inactive = len(rules) - active
        return {
            "total": len(rules),
            "active": active,
            "inactive": inactive,
            "by_state": {
                "active": active,
                "inactive": inactive,
            },
        }

    def get_rule(self, *, user_id: str, rule_id: str) -> RiskRule | None:
        return self._repository.get_rule(rule_id=rule_id, user_id=user_id)

    def update_rule(
        self,
        *,
        user_id: str,
        rule_id: str,
        rule_name: str | None = None,
        threshold: float | None = None,
        strategy_id: str | None = None,
    ) -> RiskRule | None:
        rule = self._repository.get_rule(rule_id=rule_id, user_id=user_id)
        if rule is None:
            return None

        self._assert_account_scope(user_id=user_id, account_id=rule.account_id)
        if threshold is not None:
            self._assert_positive_threshold(threshold=threshold)

        rule.update(rule_name=rule_name, threshold=threshold, strategy_id=strategy_id)
        self._repository.save_rule(rule)
        return rule

    def toggle_rule_status(self, *, user_id: str, rule_id: str, is_active: bool) -> RiskRule | None:
        rule = self._repository.get_rule(rule_id=rule_id, user_id=user_id)
        if rule is None:
            raise AccountAccessDeniedError("rule does not belong to current user")
        self._assert_account_scope(user_id=user_id, account_id=rule.account_id)
        rule.set_active(is_active=is_active)
        self._repository.save_rule(rule)
        return rule

    def delete_rule(self, *, user_id: str, rule_id: str) -> bool:
        rule = self._repository.get_rule(rule_id=rule_id, user_id=user_id)
        if rule is None:
            return False
        self._assert_account_scope(user_id=user_id, account_id=rule.account_id)
        return self._repository.delete_rule(rule_id=rule_id, user_id=user_id)

    def list_applicable_rules(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None = None,
    ) -> list[RiskRule]:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        return self._repository.list_applicable_rules(
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
        )

    def assess_account_risk(self, *, user_id: str, account_id: str) -> RiskAssessmentSnapshot:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        return self._build_assessment(
            user_id=user_id,
            account_id=account_id,
            strategy_id=None,
        )

    def assess_strategy_risk(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str,
    ) -> RiskAssessmentSnapshot:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        return self._build_assessment(
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
        )

    def get_account_assessment_snapshot(
        self,
        *,
        user_id: str,
        account_id: str,
    ) -> RiskAssessmentSnapshot | None:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        return self._repository.get_latest_assessment(
            user_id=user_id,
            account_id=account_id,
            strategy_id=None,
        )

    def evaluate_account_risk(self, *, user_id: str, account_id: str) -> RiskAssessmentSnapshot:
        return self.assess_account_risk(user_id=user_id, account_id=account_id)

    def get_risk_dashboard(self, *, user_id: str, account_id: str) -> dict:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        latest_account = self._repository.get_latest_assessment(
            user_id=user_id,
            account_id=account_id,
            strategy_id=None,
        )
        latest_strategy = self._repository.get_latest_strategy_assessment(
            user_id=user_id,
            account_id=account_id,
        )
        stats = self.alert_stats(user_id=user_id, account_id=account_id)
        active_rules = self._repository.list_rules(
            user_id=user_id,
            account_id=account_id,
            is_active=True,
        )

        def _snapshot_payload(snapshot: RiskAssessmentSnapshot | None) -> dict | None:
            if snapshot is None:
                return None
            return {
                "assessmentId": snapshot.id,
                "accountId": snapshot.account_id,
                "strategyId": snapshot.strategy_id,
                "riskScore": snapshot.risk_score,
                "riskLevel": snapshot.risk_level,
                "triggeredRuleIds": snapshot.triggered_rule_ids,
                "createdAt": snapshot.created_at.isoformat(),
            }

        return {
            "accountId": account_id,
            "activeRules": len(active_rules),
            "alertSummary": {
                "total": stats.total,
                "open": stats.open,
                "acknowledged": stats.acknowledged,
                "resolved": stats.resolved,
            },
            "latestAccountAssessment": _snapshot_payload(latest_account),
            "latestStrategyAssessment": _snapshot_payload(latest_strategy),
        }

    def create_alert(
        self,
        *,
        user_id: str,
        account_id: str,
        rule_name: str,
        severity: str,
        message: str,
    ) -> RiskAlert:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        alert = RiskAlert.create(
            user_id=user_id,
            account_id=account_id,
            rule_name=rule_name,
            severity=severity,
            message=message,
        )
        self._repository.save_alert(alert)
        return alert

    def get_alert(self, *, user_id: str, alert_id: str) -> RiskAlert | None:
        return self._repository.get_alert(alert_id=alert_id, user_id=user_id)

    def list_alerts(
        self,
        *,
        user_id: str,
        account_id: str | None = None,
        unresolved_only: bool = False,
    ) -> list[RiskAlert]:
        if account_id is not None:
            self._assert_account_scope(user_id=user_id, account_id=account_id)

        alerts = self._repository.list_alerts(
            user_id=user_id,
            account_id=account_id,
            status=None,
        )
        if not unresolved_only:
            return alerts
        return [item for item in alerts if item.status != "resolved"]

    def recent_alerts(
        self,
        *,
        user_id: str,
        account_id: str | None = None,
        limit: int = 20,
    ) -> list[RiskAlert]:
        if limit <= 0:
            raise ValueError("limit must be positive")

        alerts = self.list_alerts(user_id=user_id, account_id=account_id, unresolved_only=False)
        return sorted(alerts, key=lambda item: item.created_at, reverse=True)[:limit]

    def unresolved_alerts(
        self,
        *,
        user_id: str,
        account_id: str | None = None,
        limit: int = 20,
    ) -> list[RiskAlert]:
        if limit <= 0:
            raise ValueError("limit must be positive")

        alerts = self.list_alerts(user_id=user_id, account_id=account_id, unresolved_only=True)
        return sorted(alerts, key=lambda item: item.created_at, reverse=True)[:limit]

    def acknowledge_alert(self, *, user_id: str, alert_id: str) -> RiskAlert | None:
        alert = self._repository.get_alert(alert_id=alert_id, user_id=user_id)
        if alert is None:
            raise AccountAccessDeniedError("alert does not belong to current user")
        self._assert_account_scope(user_id=user_id, account_id=alert.account_id)
        alert.acknowledge(actor_id=user_id)
        self._repository.save_alert(alert)
        return alert

    def batch_acknowledge(self, *, user_id: str, alert_ids: list[str]) -> int:
        alerts = self._repository.list_alerts_by_ids(alert_ids=alert_ids)
        if len(alerts) != len(alert_ids):
            raise AccountAccessDeniedError("contains inaccessible alert")

        for alert in alerts:
            if alert.user_id != user_id:
                raise AccountAccessDeniedError("contains inaccessible alert")
            self._assert_account_scope(user_id=user_id, account_id=alert.account_id)

        for alert in alerts:
            alert.acknowledge(actor_id=user_id)
            self._repository.save_alert(alert)

        return len(alerts)

    def resolve_alert(self, *, user_id: str, alert_id: str) -> bool:
        alert = self._repository.get_alert(alert_id=alert_id, user_id=user_id)
        if alert is None:
            raise AccountAccessDeniedError("alert does not belong to current user")

        self._assert_account_scope(user_id=user_id, account_id=alert.account_id)
        alert.resolve(actor_id=user_id)
        self._repository.save_alert(alert)
        return True

    def alert_stats(self, *, user_id: str, account_id: str | None = None) -> RiskAlertStats:
        if account_id is not None:
            self._assert_account_scope(user_id=user_id, account_id=account_id)

        alerts = self._repository.list_alerts(user_id=user_id, account_id=account_id)
        by_severity: dict[str, int] = {}
        for item in alerts:
            by_severity[item.severity] = by_severity.get(item.severity, 0) + 1

        return RiskAlertStats(
            total=len(alerts),
            open=sum(1 for item in alerts if item.status == "open"),
            acknowledged=sum(1 for item in alerts if item.status == "acknowledged"),
            resolved=sum(1 for item in alerts if item.status == "resolved"),
            by_severity=by_severity,
        )

    def batch_check_accounts(self, *, user_id: str, account_ids: list[str]) -> dict:
        checked: list[dict] = []
        for account_id in account_ids:
            self._assert_account_scope(user_id=user_id, account_id=account_id)
            snapshot = self.evaluate_account_risk(user_id=user_id, account_id=account_id)
            checked.append(
                {
                    "accountId": account_id,
                    "assessmentId": snapshot.id,
                    "riskLevel": snapshot.risk_level,
                    "riskScore": snapshot.risk_score,
                }
            )

        return {"total": len(checked), "items": checked}

    def generate_risk_report(self, *, user_id: str, report_type: str) -> dict:
        report_type = (report_type or "").strip() or "daily"
        alerts = self.list_alerts(user_id=user_id, account_id=None, unresolved_only=False)
        total = len(alerts)
        critical = sum(1 for item in alerts if str(item.severity).strip().lower() == "critical")
        return {
            "reportType": report_type,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "totalAlerts": total,
                "criticalAlerts": critical,
            },
        }

    def notify_pending_alerts(self, *, user_id: str, actor_id: str) -> tuple[dict, str]:
        alerts = self.list_alerts(user_id=user_id, account_id=None, unresolved_only=True)
        pending = [item for item in alerts if item.notification_status != "sent"]
        audit_id = f"audit-{datetime.now(timezone.utc).timestamp()}"

        success = 0
        for alert in pending:
            alert.mark_notified(actor_id=actor_id, notification_status="sent")
            self._repository.save_alert(alert)
            success += 1

        return {"total": len(pending), "success": success, "failed": len(pending) - success, "auditId": audit_id}, audit_id

    def submit_continuous_monitor(self, *, user_id: str, account_ids: list[str]) -> dict:
        for account_id in account_ids:
            self._assert_account_scope(user_id=user_id, account_id=account_id)
            self.assess_account_risk(user_id=user_id, account_id=account_id)

        return {"monitoredAccounts": len(account_ids)}

    def generate_all_snapshots(self, *, user_id: str, account_ids: list[str]) -> dict:
        total = 0
        success = 0
        for account_id in account_ids:
            total += 1
            self._assert_account_scope(user_id=user_id, account_id=account_id)
            self.evaluate_account_risk(user_id=user_id, account_id=account_id)
            success += 1
        return {"totalAccounts": total, "successCount": success}

    def generate_account_snapshot(self, *, user_id: str, account_id: str) -> RiskAssessmentSnapshot:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        return self.evaluate_account_risk(user_id=user_id, account_id=account_id)

    def cleanup_resolved_alerts(self, *, user_id: str, retention_days: int) -> tuple[int, str]:
        retention_days = int(retention_days)
        if retention_days <= 0:
            raise ValueError("retentionDays must be positive")
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted = self._repository.delete_resolved_alerts_older_than(user_id=user_id, cutoff=cutoff)
        audit_id = f"audit-{datetime.now(timezone.utc).timestamp()}"
        return deleted, audit_id
