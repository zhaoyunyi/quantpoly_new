"""risk_control 领域测试。"""

from __future__ import annotations

import pytest


def test_batch_acknowledge_rejects_foreign_alerts_without_side_effects():
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import AccountAccessDeniedError, RiskControlService

    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    mine = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )
    other = service.create_alert(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )

    with pytest.raises(AccountAccessDeniedError):
        service.batch_acknowledge(user_id="u-1", alert_ids=[mine.id, other.id])

    mine_after = service.get_alert(user_id="u-1", alert_id=mine.id)
    other_after = service.get_alert(user_id="u-2", alert_id=other.id)
    assert mine_after is not None
    assert mine_after.status == "open"
    assert other_after is not None
    assert other_after.status == "open"


def test_alert_stats_rejects_foreign_account_scope():
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import AccountAccessDeniedError, RiskControlService

    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    service.create_alert(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="max-loss",
        severity="high",
        message="loss breach",
    )

    with pytest.raises(AccountAccessDeniedError):
        service.alert_stats(user_id="u-1", account_id="u-2-account")


def test_public_methods_require_user_id():
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import RiskControlService

    service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda _user_id, _account_id: True,
    )

    with pytest.raises(TypeError):
        service.list_alerts()  # type: ignore[misc]

