"""Preferences InMemory 存储测试。"""

from __future__ import annotations


def test_get_or_create_persists_default():
    from user_preferences.store import InMemoryPreferencesStore
    from user_preferences.domain import CURRENT_VERSION

    store = InMemoryPreferencesStore()

    prefs = store.get_or_create(user_id="u-1")
    assert prefs.version == CURRENT_VERSION

    prefs2 = store.get_or_create(user_id="u-1")
    assert prefs2 == prefs


def test_get_or_create_migrates_old_version_and_writes_back():
    from user_preferences.store import InMemoryPreferencesStore
    from user_preferences.domain import Preferences, ThemePreferences, CURRENT_VERSION

    store = InMemoryPreferencesStore()

    old = Preferences(
        version=0,
        theme=ThemePreferences(primary_color="#000000", dark_mode=False),
        advanced={"betaFeatures": True},
    )
    store.set(user_id="u-1", preferences=old)

    migrated = store.get_or_create(user_id="u-1")
    assert migrated.version == CURRENT_VERSION
    persisted = store.get(user_id="u-1")
    assert persisted is not None
    assert persisted.version == CURRENT_VERSION

