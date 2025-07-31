"""risk_control in-memory 仓储。"""

from __future__ import annotations

from risk_control.domain import RiskAlert, RiskRule


class InMemoryRiskRepository:
    def __init__(self) -> None:
        self._rules: dict[str, RiskRule] = {}
        self._alerts: dict[str, RiskAlert] = {}

    def save_rule(self, rule: RiskRule) -> None:
        self._rules[rule.id] = rule

    def list_rules(self, *, user_id: str, account_id: str | None = None) -> list[RiskRule]:
        return [
            item
            for item in self._rules.values()
            if item.user_id == user_id and (account_id is None or item.account_id == account_id)
        ]

    def save_alert(self, alert: RiskAlert) -> None:
        self._alerts[alert.id] = alert

    def get_alert(self, *, alert_id: str, user_id: str) -> RiskAlert | None:
        item = self._alerts.get(alert_id)
        if item is None:
            return None
        if item.user_id != user_id:
            return None
        return item

    def list_alerts(
        self,
        *,
        user_id: str,
        account_id: str | None = None,
        status: str | None = None,
    ) -> list[RiskAlert]:
        return [
            item
            for item in self._alerts.values()
            if item.user_id == user_id
            and (account_id is None or item.account_id == account_id)
            and (status is None or item.status == status)
        ]

    def list_alerts_by_ids(self, *, alert_ids: list[str]) -> list[RiskAlert]:
        return [self._alerts[item] for item in alert_ids if item in self._alerts]
