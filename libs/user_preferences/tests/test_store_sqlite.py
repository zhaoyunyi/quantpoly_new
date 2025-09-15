"""Preferences SQLite 存储测试。"""

from __future__ import annotations

from user_preferences.store_sqlite import SQLitePreferencesStore


def test_sqlite_store_roundtrip_and_reopen(tmp_path):
    db_path = tmp_path / "prefs.sqlite3"

    store = SQLitePreferencesStore(db_path=str(db_path))
    prefs = store.get_or_create(user_id="u-1")
    assert prefs.version >= 1

    updated = prefs.model_copy(deep=True)
    updated.theme.dark_mode = True
    store.set(user_id="u-1", preferences=updated)

    reopened = SQLitePreferencesStore(db_path=str(db_path))
    got = reopened.get(user_id="u-1")

    assert got is not None
    assert got.theme.dark_mode is True
    assert got.version == updated.version
