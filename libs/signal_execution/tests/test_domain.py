"""signal_execution 领域测试。"""

from __future__ import annotations

import pytest


def test_execute_foreign_signal_rejected_and_status_unchanged():
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalAccessDeniedError, SignalExecutionService

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    signal = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy",
        account_id="u-2-account",
        symbol="AAPL",
        side="BUY",
    )

    with pytest.raises(SignalAccessDeniedError):
        service.execute_signal(user_id="u-1", signal_id=signal.id)

    mine = service.get_signal(user_id="u-2", signal_id=signal.id)
    assert mine is not None
    assert mine.status == "pending"


def test_execution_trend_is_user_scoped():
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=s1.id)

    s2 = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy",
        account_id="u-2-account",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-2", signal_id=s2.id)

    trend = service.execution_trend(user_id="u-1")
    assert trend["total"] == 1
    assert trend["executed"] == 1


def test_global_cleanup_requires_admin():
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import AdminRequiredError, SignalExecutionService

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy",
        account_id="u-2-account",
        symbol="MSFT",
        side="BUY",
    )

    with pytest.raises(AdminRequiredError):
        service.cleanup_all_signals(user_id="u-1", is_admin=False)


def test_public_methods_require_user_id():
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda _user_id, _strategy_id: True,
        account_owner_acl=lambda _user_id, _account_id: True,
    )

    with pytest.raises(TypeError):
        service.list_signals()  # type: ignore[misc]

