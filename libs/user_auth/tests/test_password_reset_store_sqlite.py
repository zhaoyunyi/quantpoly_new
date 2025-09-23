"""密码找回 token SQLite 持久化测试。"""

from __future__ import annotations

from pathlib import Path


def _sqlite_store(db_path: Path):
    from user_auth.password_reset_sqlite import SQLitePasswordResetStore

    return SQLitePasswordResetStore(db_path=str(db_path), ttl_seconds=3600)


def test_sqlite_password_reset_store_persists_token_across_restarts(tmp_path: Path):
    db_path = tmp_path / "reset-store.sqlite3"

    store1 = _sqlite_store(db_path)
    issued = store1.issue(user_id="u-1")

    store2 = _sqlite_store(db_path)
    consumed = store2.consume(issued.token)

    assert consumed is not None
    assert consumed.user_id == "u-1"


def test_sqlite_password_reset_store_token_single_use(tmp_path: Path):
    db_path = tmp_path / "reset-store.sqlite3"

    store = _sqlite_store(db_path)
    issued = store.issue(user_id="u-1")

    first = store.consume(issued.token)
    second = store.consume(issued.token)

    assert first is not None
    assert second is None
