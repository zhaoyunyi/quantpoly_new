"""signal_execution 批处理操作测试。"""

from __future__ import annotations

import pytest


def _build_service():
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    return SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )


def test_batch_execute_supports_partial_success_and_idempotency():
    from signal_execution.service import BatchIdempotencyConflictError

    service = _build_service()

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-s1",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    s2 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-s1",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )
    foreign = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-s1",
        account_id="u-2-account",
        symbol="TSLA",
        side="BUY",
    )

    first = service.batch_execute_signals(
        user_id="u-1",
        signal_ids=[s1.id, s2.id, foreign.id],
        idempotency_key="idem-1",
    )
    assert first["executed"] == 2
    assert first["denied"] == 1
    assert first["idempotent"] is False

    second = service.batch_execute_signals(
        user_id="u-1",
        signal_ids=[s1.id, s2.id, foreign.id],
        idempotency_key="idem-1",
    )
    assert second["idempotent"] is True
    assert second["executed"] == 2
    assert second["denied"] == 1

    with pytest.raises(BatchIdempotencyConflictError):
        service.batch_execute_signals(
            user_id="u-1",
            signal_ids=[s1.id],
            idempotency_key="idem-1",
        )


def test_batch_cancel_returns_status_per_signal():
    service = _build_service()

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-s1",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    s2 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-s1",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=s2.id)

    result = service.batch_cancel_signals(user_id="u-1", signal_ids=[s1.id, s2.id])
    assert result["cancelled"] == 1
    assert result["skipped"] == 1
