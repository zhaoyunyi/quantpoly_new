"""signal_execution sqlite 服务级持久化适配器回归测试。"""

from __future__ import annotations

import pytest

from signal_execution.repository_sqlite import SQLiteSignalRepository
from signal_execution.service import SignalAccessDeniedError, SignalExecutionService


def _build_service(*, db_path: str) -> SignalExecutionService:
    return SignalExecutionService(
        repository=SQLiteSignalRepository(db_path=db_path),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )


def test_service_should_recover_signal_and_execution_after_restart(tmp_path):
    db_path = tmp_path / "signal.sqlite3"

    service = _build_service(db_path=str(db_path))
    signal = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=signal.id, execution_metrics={"pnl": 1.0})

    reopened = _build_service(db_path=str(db_path))
    signals = reopened.list_signals(user_id="u-1")
    executions = reopened.list_executions(user_id="u-1")

    assert [item.id for item in signals] == [signal.id]
    assert len(executions) == 1
    assert executions[0].signal_id == signal.id


def test_service_should_keep_acl_semantics_with_sqlite_repository(tmp_path):
    db_path = tmp_path / "signal.sqlite3"
    service = _build_service(db_path=str(db_path))

    signal = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="MSFT",
        side="BUY",
    )

    assert service.list_signals(user_id="u-2") == []

    with pytest.raises(SignalAccessDeniedError):
        service.get_signal_detail(user_id="u-2", signal_id=signal.id)
