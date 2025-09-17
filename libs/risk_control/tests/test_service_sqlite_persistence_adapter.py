"""risk_control sqlite 服务级持久化适配器回归测试。"""

from __future__ import annotations

import pytest

from risk_control.repository_sqlite import SQLiteRiskRepository
from risk_control.service import AccountAccessDeniedError, RiskControlService


def _build_service(*, db_path: str) -> RiskControlService:
    return RiskControlService(
        repository=SQLiteRiskRepository(db_path=db_path),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )


def test_service_should_recover_rule_and_assessment_after_restart(tmp_path):
    db_path = tmp_path / "risk.sqlite3"

    service = _build_service(db_path=str(db_path))
    rule = service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="drawdown",
        threshold=0.35,
    )
    snapshot = service.assess_account_risk(user_id="u-1", account_id="u-1-account")

    reopened = _build_service(db_path=str(db_path))
    rules = reopened.list_rules(user_id="u-1", account_id="u-1-account")
    latest = reopened.get_account_assessment_snapshot(user_id="u-1", account_id="u-1-account")

    assert [item.id for item in rules] == [rule.id]
    assert latest is not None
    assert latest.id == snapshot.id


def test_service_should_keep_acl_semantics_with_sqlite_repository(tmp_path):
    db_path = tmp_path / "risk.sqlite3"
    service = _build_service(db_path=str(db_path))

    service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="volatility",
        threshold=0.2,
    )

    assert service.list_rules(user_id="u-2") == []

    with pytest.raises(AccountAccessDeniedError):
        service.list_rules(user_id="u-2", account_id="u-1-account")
