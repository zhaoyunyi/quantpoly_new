"""risk_control 评估视图与告警读模型测试。"""

from __future__ import annotations


def _build_service():
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import RiskControlService

    return RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )


def test_account_and_strategy_assessment_snapshot_and_dashboard():
    service = _build_service()

    service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="account-drawdown",
        threshold=0.12,
    )
    service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        strategy_id="s-1",
        rule_name="strategy-drawdown",
        threshold=0.20,
    )

    account_assessment = service.assess_account_risk(user_id="u-1", account_id="u-1-account")
    strategy_assessment = service.assess_strategy_risk(
        user_id="u-1",
        account_id="u-1-account",
        strategy_id="s-1",
    )

    assert account_assessment.risk_level in {"low", "medium", "high"}
    assert strategy_assessment.strategy_id == "s-1"

    dashboard = service.get_risk_dashboard(user_id="u-1", account_id="u-1-account")
    assert dashboard["accountId"] == "u-1-account"
    assert dashboard["activeRules"] == 2
    assert dashboard["latestAccountAssessment"]["assessmentId"] == account_assessment.id
    assert dashboard["latestStrategyAssessment"]["assessmentId"] == strategy_assessment.id


def test_alert_list_detail_acknowledge_resolve_flow():
    service = _build_service()

    alert = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )

    open_alerts = service.list_alerts(user_id="u-1", unresolved_only=True)
    assert [item.id for item in open_alerts] == [alert.id]

    acknowledged = service.acknowledge_alert(user_id="u-1", alert_id=alert.id)
    assert acknowledged is not None
    assert acknowledged.status == "acknowledged"

    unresolved_after_ack = service.list_alerts(user_id="u-1", unresolved_only=True)
    assert [item.id for item in unresolved_after_ack] == [alert.id]

    detail = service.get_alert(user_id="u-1", alert_id=alert.id)
    assert detail is not None
    assert detail.status == "acknowledged"

    resolved = service.resolve_alert(user_id="u-1", alert_id=alert.id)
    assert resolved is True

    unresolved_after_resolve = service.list_alerts(user_id="u-1", unresolved_only=True)
    assert unresolved_after_resolve == []

    stats = service.alert_stats(user_id="u-1")
    assert stats.total == 1
    assert stats.resolved == 1
