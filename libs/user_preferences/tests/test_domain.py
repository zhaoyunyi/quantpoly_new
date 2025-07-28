"""user-preferences 领域逻辑测试。

BDD Scenarios:
- 新用户偏好默认值包含 version
- 深度合并更新不丢失字段
- 非法字段被拒绝
- low-level 用户看不到 advanced
- low-level 用户不能写 advanced
"""

import pytest


def test_default_preferences_has_version():
    from user_preferences.domain import default_preferences, CURRENT_VERSION

    prefs = default_preferences()
    assert prefs.version == CURRENT_VERSION


def test_default_preferences_contains_contract_fields():
    from user_preferences.domain import default_preferences

    prefs = default_preferences()

    assert prefs.theme is not None
    assert prefs.account is not None
    assert prefs.notifications is not None
    assert prefs.data is not None
    assert isinstance(prefs.sync_enabled, bool)
    assert prefs.last_updated is not None


def test_migrate_legacy_partial_preferences_payload():
    from user_preferences.domain import migrate_preferences, CURRENT_VERSION

    migrated = migrate_preferences(
        {
            "version": 0,
            "theme": {"primaryColor": "#000000", "darkMode": False},
            "syncEnabled": False,
        }
    )

    assert migrated.version == CURRENT_VERSION
    assert migrated.theme.primary_color == "#000000"
    assert migrated.account is not None
    assert migrated.notifications is not None
    assert migrated.data is not None
    assert migrated.sync_enabled is False


def test_deep_merge_keeps_unpatched_fields():
    from user_preferences.domain import default_preferences, apply_patch

    base = default_preferences()

    patched = apply_patch(
        base,
        {
            "theme": {
                "primaryColor": "#FF0000",
            },
        },
        user_level=1,
    )

    assert patched.theme.primary_color == "#FF0000"
    assert patched.theme.dark_mode == base.theme.dark_mode


def test_unknown_field_rejected():
    from user_preferences.domain import default_preferences, apply_patch, PreferencesValidationError

    with pytest.raises(PreferencesValidationError):
        apply_patch(
            default_preferences(),
            {"notSupported": True},
            user_level=1,
        )


def test_level_1_user_filters_out_advanced():
    from user_preferences.domain import default_preferences, filter_for_user

    prefs = default_preferences()
    filtered = filter_for_user(prefs, user_level=1)
    assert filtered.advanced is None


def test_level_1_user_cannot_patch_advanced():
    from user_preferences.domain import default_preferences, apply_patch, AdvancedPreferencesPermissionError

    with pytest.raises(AdvancedPreferencesPermissionError):
        apply_patch(
            default_preferences(),
            {"advanced": {"betaFeatures": True}},
            user_level=1,
        )


def test_apply_patch_updates_last_updated_with_server_merge_rule():
    from user_preferences.domain import apply_patch, default_preferences

    base = default_preferences()
    patched = apply_patch(
        base,
        {
            "theme": {
                "primaryColor": "#123456",
            },
            "notifications": {
                "browser": {"enabled": False},
            },
        },
        user_level=2,
    )

    assert patched.version == base.version
    assert patched.theme.primary_color == "#123456"
    assert patched.notifications.browser.enabled is False
    assert patched.last_updated is not None
