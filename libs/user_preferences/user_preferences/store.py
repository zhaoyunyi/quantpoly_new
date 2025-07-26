"""Preferences 存储抽象与实现。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from user_preferences.domain import Preferences, default_preferences, migrate_preferences


class PreferencesStore(Protocol):
    """Preferences 存储协议。

    用于让 API 层同时支持 InMemory / Postgres 等实现。
    """

    def get(self, user_id: str) -> Preferences | None: ...

    def set(self, user_id: str, preferences: Preferences) -> None: ...

    def reset(self, user_id: str) -> Preferences: ...

    def get_or_create(self, user_id: str) -> Preferences: ...


@dataclass
class InMemoryPreferencesStore:
    _data: dict[str, Preferences]

    def __init__(self) -> None:
        self._data = {}

    def get(self, user_id: str) -> Preferences | None:
        return self._data.get(user_id)

    def set(self, user_id: str, preferences: Preferences) -> None:
        self._data[user_id] = preferences

    def reset(self, user_id: str) -> Preferences:
        prefs = default_preferences()
        self._data[user_id] = prefs
        return prefs

    def get_or_create(self, user_id: str) -> Preferences:
        existing = self._data.get(user_id)
        if existing is None:
            prefs = default_preferences()
            self._data[user_id] = prefs
            return prefs

        migrated = migrate_preferences(existing)
        if migrated != existing:
            self._data[user_id] = migrated
        return migrated


class PostgresPreferencesStore:
    """Postgres 存储实现（依赖 SQLAlchemy Engine）。

    说明：该实现将 SQLAlchemy 作为可选依赖。
    - 单元测试与纯领域逻辑不需要安装 SQLAlchemy。
    - 使用该存储时需安装 `sqlalchemy` 与对应驱动（例如 `psycopg`）。
    """

    def __init__(self, *, engine: Any) -> None:
        self._engine = engine

    @staticmethod
    def _text():
        try:
            from sqlalchemy import text
        except ModuleNotFoundError as e:  # pragma: no cover
            raise RuntimeError(
                "PostgresPreferencesStore requires SQLAlchemy. "
                "Please install `sqlalchemy` (and a Postgres driver such as `psycopg`)."
            ) from e
        return text

    def ensure_schema(self) -> None:
        text = self._text()
        ddl = """
        create table if not exists user_preferences (
            user_id text primary key,
            preferences jsonb not null
        );
        """
        with self._engine.begin() as conn:
            conn.execute(text(ddl))

    def get(self, user_id: str) -> Preferences | None:
        text = self._text()
        sql = "select preferences from user_preferences where user_id=:user_id"
        with self._engine.begin() as conn:
            row = conn.execute(text(sql), {"user_id": user_id}).fetchone()
            if row is None:
                return None
            payload = row[0]
            if isinstance(payload, str):
                data = json.loads(payload)
            else:
                data = payload
            return Preferences.model_validate(data)

    def set(self, user_id: str, preferences: Preferences) -> None:
        text = self._text()
        sql = """
        insert into user_preferences (user_id, preferences)
        values (:user_id, cast(:preferences as jsonb))
        on conflict (user_id) do update set preferences=excluded.preferences;
        """
        payload = json.dumps(preferences.model_dump(by_alias=True), ensure_ascii=False)
        with self._engine.begin() as conn:
            conn.execute(text(sql), {"user_id": user_id, "preferences": payload})

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
