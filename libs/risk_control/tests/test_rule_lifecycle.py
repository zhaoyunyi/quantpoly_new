"""risk_control 规则生命周期测试。"""

from __future__ import annotations

import pytest


@pytest.fixture
def service():
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import RiskControlService

    return RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )


def test_rule_crud_toggle_and_applicable_scope(service):
    account_rule = service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max-loss",
        threshold=0.1,
    )
    strategy_rule = service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        strategy_id="s-1",
        rule_name="strategy-drawdown",
        threshold=0.2,
    )
    service.create_rule(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="foreign-rule",
        threshold=0.3,
    )

    account_only = service.list_applicable_rules(user_id="u-1", account_id="u-1-account")
    assert [item.id for item in account_only] == [account_rule.id]

    strategy_rules = service.list_applicable_rules(
        user_id="u-1",
        account_id="u-1-account",
        strategy_id="s-1",
    )
    assert {item.id for item in strategy_rules} == {account_rule.id, strategy_rule.id}

    toggled = service.toggle_rule_status(user_id="u-1", rule_id=account_rule.id, is_active=False)
    assert toggled is not None
    assert toggled.is_active is False

    strategy_rules_after_toggle = service.list_applicable_rules(
        user_id="u-1",
        account_id="u-1-account",
        strategy_id="s-1",
    )
    assert [item.id for item in strategy_rules_after_toggle] == [strategy_rule.id]

    updated = service.update_rule(
        user_id="u-1",
        rule_id=strategy_rule.id,
        rule_name="strategy-drawdown-v2",
        threshold=0.15,
    )
    assert updated is not None
    assert updated.rule_name == "strategy-drawdown-v2"
    assert updated.threshold == 0.15

    deleted = service.delete_rule(user_id="u-1", rule_id=strategy_rule.id)
    assert deleted is True
    assert service.get_rule(user_id="u-1", rule_id=strategy_rule.id) is None


def test_rule_lifecycle_rejects_foreign_scope(service):
    from risk_control.service import AccountAccessDeniedError

    with pytest.raises(AccountAccessDeniedError):
        service.create_rule(
            user_id="u-1",
            account_id="u-2-account",
            rule_name="max-loss",
            threshold=0.1,
        )

    foreign = service.create_rule(
        user_id="u-2",
        account_id="u-2-account",
        rule_name="foreign",
        threshold=0.2,
    )

    with pytest.raises(AccountAccessDeniedError):
        service.toggle_rule_status(user_id="u-1", rule_id=foreign.id, is_active=False)
