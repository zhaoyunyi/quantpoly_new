"""risk_control in-memory 仓储。"""

from __future__ import annotations

from risk_control.domain import RiskAlert, RiskAssessmentSnapshot, RiskRule


class InMemoryRiskRepository:
    def __init__(self) -> None:
        self._rules: dict[str, RiskRule] = {}
        self._alerts: dict[str, RiskAlert] = {}
        self._assessments: dict[str, RiskAssessmentSnapshot] = {}

    def save_rule(self, rule: RiskRule) -> None:
        self._rules[rule.id] = rule

    def get_rule(self, *, rule_id: str, user_id: str) -> RiskRule | None:
        item = self._rules.get(rule_id)
        if item is None or item.user_id != user_id:
            return None
        return item

    def delete_rule(self, *, rule_id: str, user_id: str) -> bool:
        item = self.get_rule(rule_id=rule_id, user_id=user_id)
        if item is None:
            return False
        del self._rules[rule_id]
        return True

    def list_rules(
        self,
        *,
        user_id: str,
        account_id: str | None = None,
        strategy_id: str | None = None,
        is_active: bool | None = None,
    ) -> list[RiskRule]:
        return [
            item
            for item in self._rules.values()
            if item.user_id == user_id
            and (account_id is None or item.account_id == account_id)
            and (strategy_id is None or item.strategy_id == strategy_id)
            and (is_active is None or item.is_active == is_active)
        ]

    def list_applicable_rules(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None = None,
    ) -> list[RiskRule]:
        rules = self.list_rules(user_id=user_id, account_id=account_id, is_active=True)
        if strategy_id is None:
            return [item for item in rules if item.strategy_id is None]

        return [
            item
            for item in rules
            if item.strategy_id is None or item.strategy_id == strategy_id
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

    def save_assessment(self, snapshot: RiskAssessmentSnapshot) -> None:
        self._assessments[snapshot.id] = snapshot

    def list_assessments(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None = None,
    ) -> list[RiskAssessmentSnapshot]:
        result: list[RiskAssessmentSnapshot] = []
        for item in self._assessments.values():
            if item.user_id != user_id or item.account_id != account_id:
                continue
            if strategy_id is None and item.strategy_id is not None:
                continue
            if strategy_id is not None and item.strategy_id != strategy_id:
                continue
            result.append(item)
        return result

    def get_latest_assessment(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None = None,
    ) -> RiskAssessmentSnapshot | None:
        matched = self.list_assessments(
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
        )
        if not matched:
            return None
        return max(matched, key=lambda item: item.created_at)

    def get_latest_strategy_assessment(
        self,
        *,
        user_id: str,
        account_id: str,
    ) -> RiskAssessmentSnapshot | None:
        matched = [
            item
            for item in self._assessments.values()
            if item.user_id == user_id
            and item.account_id == account_id
            and item.strategy_id is not None
        ]
        if not matched:
            return None
        return max(matched, key=lambda item: item.created_at)
