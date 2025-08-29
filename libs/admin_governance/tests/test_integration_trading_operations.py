"""admin_governance 与 trading_account 交易运维动作集成测试。"""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("action", "call"),
    [
        (
            "trading.process_pending",
            lambda service, **kwargs: service.process_pending_trades(
                user_id=kwargs["user_id"],
                is_admin=kwargs["is_admin"],
                admin_decision_source=kwargs.get("admin_decision_source", "none"),
                max_trades=10,
                confirmation_token=kwargs.get("confirmation_token"),
                audit_id="audit-pp",
            ),
        ),
        (
            "trading.calculate_daily_stats",
            lambda service, **kwargs: service.calculate_daily_stats(
                user_id=kwargs["user_id"],
                is_admin=kwargs["is_admin"],
                admin_decision_source=kwargs.get("admin_decision_source", "none"),
                account_ids=[kwargs["account_id"]],
                target_date="2026-02-10",
                confirmation_token=kwargs.get("confirmation_token"),
                audit_id="audit-ds",
            ),
        ),
        (
            "trading.batch_execute",
            lambda service, **kwargs: service.batch_execute_trades(
                user_id=kwargs["user_id"],
                is_admin=kwargs["is_admin"],
                admin_decision_source=kwargs.get("admin_decision_source", "none"),
                trade_requests=[
                    {
                        "accountId": kwargs["account_id"],
                        "symbol": "AAPL",
                        "side": "BUY",
                        "quantity": 1,
                        "price": 100,
                    }
                ],
                confirmation_token=kwargs.get("confirmation_token"),
                audit_id="audit-batch",
            ),
        ),
        (
            "trading.risk_monitor",
            lambda service, **kwargs: service.monitor_risk(
                user_id=kwargs["user_id"],
                is_admin=kwargs["is_admin"],
                admin_decision_source=kwargs.get("admin_decision_source", "none"),
                account_ids=[kwargs["account_id"]],
                confirmation_token=kwargs.get("confirmation_token"),
                audit_id="audit-risk",
            ),
        ),
        (
            "trading.account_cleanup",
            lambda service, **kwargs: service.cleanup_account_history(
                user_id=kwargs["user_id"],
                is_admin=kwargs["is_admin"],
                admin_decision_source=kwargs.get("admin_decision_source", "none"),
                account_ids=[kwargs["account_id"]],
                days_threshold=90,
                confirmation_token=kwargs.get("confirmation_token"),
                audit_id="audit-clean",
            ),
        ),
    ],
)
def test_trading_ops_actions_require_confirmation_and_emit_audit_record(action, call):
    from admin_governance.audit import InMemoryAuditLog
    from admin_governance.catalog import default_action_catalog
    from admin_governance.policy import GovernancePolicyEngine
    from admin_governance.token import InMemoryConfirmationTokenStore
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService, TradingAdminRequiredError

    token_store = InMemoryConfirmationTokenStore()
    audit_log = InMemoryAuditLog()
    engine = GovernancePolicyEngine(
        action_catalog=default_action_catalog(),
        token_store=token_store,
        audit_log=audit_log,
    )

    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(
        repository=repo,
        governance_checker=engine.authorize,
    )
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.deposit(user_id="admin-1", account_id=account.id, amount=1000)

    with pytest.raises(TradingAdminRequiredError):
        call(
            service,
            user_id="u-1",
            is_admin=False,
            admin_decision_source="none",
            account_id=account.id,
        )

    token = token_store.issue(actor_id="admin-1", action=action, target="trading", ttl_seconds=60)
    result = call(
        service,
        user_id="admin-1",
        is_admin=True,
        admin_decision_source="role",
        confirmation_token=token,
        account_id=account.id,
    )
    assert result["auditId"]

    records = audit_log.list_records()
    assert any(item.action == action and item.result == "allowed" for item in records)

    last = records[-1]
    assert last.context.get("adminDecisionSource") == "role"
    assert token not in str(last.context)

