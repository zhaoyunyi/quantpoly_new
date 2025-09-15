"""signal_execution sqlite 仓储测试。"""

from __future__ import annotations

from datetime import timedelta

from signal_execution.domain import ExecutionRecord, TradingSignal
from signal_execution.repository_sqlite import SQLiteSignalRepository


def test_sqlite_repository_persists_signals_executions_and_batch_records(tmp_path):
    db_path = tmp_path / "signal.sqlite3"

    repo = SQLiteSignalRepository(db_path=str(db_path))

    signal = TradingSignal.create(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    repo.save_signal(signal)

    execution = ExecutionRecord.create(
        user_id="u-1",
        signal_id=signal.id,
        strategy_id=signal.strategy_id,
        symbol=signal.symbol,
        status="executed",
        metrics={"pnl": 1.23},
    )
    repo.save_execution(execution)

    repo.save_batch_record(
        user_id="u-1",
        action="execute",
        idempotency_key="k-1",
        fingerprint="fp-1",
        result={"success": 1},
    )

    reopened = SQLiteSignalRepository(db_path=str(db_path))

    got_signal = reopened.get_signal(signal_id=signal.id, user_id="u-1")
    assert got_signal is not None
    assert got_signal.symbol == "AAPL"

    got_execution = reopened.get_execution(execution_id=execution.id, user_id="u-1")
    assert got_execution is not None
    assert got_execution.metrics["pnl"] == 1.23

    batch = reopened.get_batch_record(user_id="u-1", action="execute", idempotency_key="k-1")
    assert batch == ("fp-1", {"success": 1})


def test_sqlite_repository_deletes_executions_before_cutoff(tmp_path):
    db_path = tmp_path / "signal.sqlite3"
    repo = SQLiteSignalRepository(db_path=str(db_path))

    old_execution = ExecutionRecord.create(
        user_id="u-1",
        signal_id="s-1",
        strategy_id="st-1",
        symbol="AAPL",
        status="executed",
    )
    old_execution.created_at = old_execution.created_at - timedelta(days=30)
    repo.save_execution(old_execution)

    recent_execution = ExecutionRecord.create(
        user_id="u-1",
        signal_id="s-2",
        strategy_id="st-1",
        symbol="MSFT",
        status="executed",
    )
    repo.save_execution(recent_execution)

    deleted = repo.delete_executions_before(cutoff=recent_execution.created_at - timedelta(days=1))

    assert deleted == 1
    remaining = repo.list_executions(user_id="u-1")
    assert [item.id for item in remaining] == [recent_execution.id]
