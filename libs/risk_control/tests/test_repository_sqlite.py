"""risk_control sqlite 仓储测试。"""

from __future__ import annotations

from datetime import timedelta

from risk_control.domain import RiskAlert, RiskAssessmentSnapshot, RiskRule
from risk_control.repository_sqlite import SQLiteRiskRepository


def test_sqlite_repository_persists_rule_alert_and_assessment(tmp_path):
    db_path = tmp_path / "risk.sqlite3"

    repo = SQLiteRiskRepository(db_path=str(db_path))

    rule = RiskRule.create(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="drawdown",
        threshold=0.2,
    )
    repo.save_rule(rule)

    alert = RiskAlert.create(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="drawdown",
        severity="high",
        message="triggered",
    )
    repo.save_alert(alert)

    snapshot = RiskAssessmentSnapshot.create(
        user_id="u-1",
        account_id="u-1-account",
        strategy_id=None,
        risk_score=88.5,
        risk_level="high",
        triggered_rule_ids=[rule.id],
    )
    repo.save_assessment(snapshot)

    reopened = SQLiteRiskRepository(db_path=str(db_path))

    got_rule = reopened.get_rule(rule_id=rule.id, user_id="u-1")
    assert got_rule is not None
    assert got_rule.rule_name == "drawdown"

    alerts = reopened.list_alerts(user_id="u-1")
    assert [item.id for item in alerts] == [alert.id]

    latest = reopened.get_latest_assessment(user_id="u-1", account_id="u-1-account")
    assert latest is not None
    assert latest.id == snapshot.id


def test_sqlite_repository_deletes_resolved_alerts_by_cutoff(tmp_path):
    db_path = tmp_path / "risk.sqlite3"
    repo = SQLiteRiskRepository(db_path=str(db_path))

    old_alert = RiskAlert.create(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="volatility",
        severity="medium",
        message="old",
    )
    old_alert.resolve(actor_id="u-1")
    old_alert.resolved_at = old_alert.resolved_at - timedelta(days=10)  # type: ignore[operator]
    repo.save_alert(old_alert)

    recent_alert = RiskAlert.create(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="volatility",
        severity="medium",
        message="recent",
    )
    recent_alert.resolve(actor_id="u-1")
    repo.save_alert(recent_alert)

    deleted = repo.delete_resolved_alerts_older_than(
        user_id="u-1",
        cutoff=recent_alert.resolved_at - timedelta(days=1),  # type: ignore[operator]
    )

    assert deleted == 1
    remaining_ids = {item.id for item in repo.list_alerts(user_id="u-1")}
    assert old_alert.id not in remaining_ids
    assert recent_alert.id in remaining_ids
