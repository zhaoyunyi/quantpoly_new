"""risk_control 应用服务。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from risk_control.domain import RiskAlert, RiskRule
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

    def create_rule(
        self,
        *,
        user_id: str,
        account_id: str,
        rule_name: str,
        threshold: float,
    ) -> RiskRule:
        self._assert_account_scope(user_id=user_id, account_id=account_id)
        rule = RiskRule.create(
            user_id=user_id,
            account_id=account_id,
            rule_name=rule_name,
            threshold=threshold,
        )
        self._repository.save_rule(rule)
        return rule

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

        status = "open" if unresolved_only else None
        return self._repository.list_alerts(
            user_id=user_id,
            account_id=account_id,
            status=status,
        )

    def batch_acknowledge(self, *, user_id: str, alert_ids: list[str]) -> int:
        alerts = self._repository.list_alerts_by_ids(alert_ids=alert_ids)
        if len(alerts) != len(alert_ids):
            raise AccountAccessDeniedError("contains inaccessible alert")

        for alert in alerts:
            if alert.user_id != user_id:
                raise AccountAccessDeniedError("contains inaccessible alert")
            self._assert_account_scope(user_id=user_id, account_id=alert.account_id)

        for alert in alerts:
            alert.acknowledge()
            self._repository.save_alert(alert)

        return len(alerts)

    def resolve_alert(self, *, user_id: str, alert_id: str) -> bool:
        alert = self._repository.get_alert(alert_id=alert_id, user_id=user_id)
        if alert is None:
            raise AccountAccessDeniedError("alert does not belong to current user")

        self._assert_account_scope(user_id=user_id, account_id=alert.account_id)
        alert.resolve()
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
