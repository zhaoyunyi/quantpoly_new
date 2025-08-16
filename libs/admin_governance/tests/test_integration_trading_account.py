"""admin_governance 与 trading_account 集成测试。"""

from __future__ import annotations

import pytest


def test_trading_refresh_prices_uses_governance_checker():
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

    service = TradingAccountService(
        repository=InMemoryTradingAccountRepository(),
        governance_checker=engine.authorize,
    )
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.upsert_position(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=100,
        last_price=110,
    )

    with pytest.raises(TradingAdminRequiredError):
        service.refresh_market_prices(
            user_id="u-1",
            is_admin=False,
            admin_decision_source="none",
            price_updates={"AAPL": 130},
        )

    token = token_store.issue(
        actor_id="admin-1",
        action="trading.refresh_prices",
        target="trading",
        ttl_seconds=60,
    )

    refreshed = service.refresh_market_prices(
        user_id="admin-1",
        is_admin=True,
        admin_decision_source="role",
        price_updates={"AAPL": 130},
        confirmation_token=token,
    )

    assert refreshed["updatedPositions"] == 1
    records = audit_log.list_records()
    assert any(item.action == "trading.refresh_prices" and item.result == "allowed" for item in records)

    last = records[-1]
    assert last.context.get("adminDecisionSource") == "role"
    assert token not in str(last.context)
