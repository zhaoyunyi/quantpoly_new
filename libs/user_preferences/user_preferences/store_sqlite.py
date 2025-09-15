"""Preferences SQLite 存储实现。"""

from __future__ import annotations

import json
import sqlite3

from user_preferences.domain import Preferences, default_preferences, migrate_preferences


class SQLitePreferencesStore:
    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences_store (
                    user_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def get(self, user_id: str) -> Preferences | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM user_preferences_store WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        if row is None:
            return None
        return Preferences.model_validate(json.loads(row[0]))

    def set(self, user_id: str, preferences: Preferences) -> None:
        payload = json.dumps(preferences.model_dump(by_alias=True), ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_preferences_store (user_id, payload_json)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET payload_json = excluded.payload_json
                """,
                (user_id, payload),
            )

    def reset(self, user_id: str) -> Preferences:
        prefs = default_preferences()
        self.set(user_id, prefs)
        return prefs

    def get_or_create(self, user_id: str) -> Preferences:
        existing = self.get(user_id)
        if existing is None:
            prefs = default_preferences()
            self.set(user_id, prefs)
            return prefs

        migrated = migrate_preferences(existing)
        if migrated != existing:
            self.set(user_id, migrated)
        return migrated
