"""用户偏好（preferences）领域模型与纯函数操作。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field


CURRENT_VERSION = 1


def _to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class PreferencesValidationError(ValueError):
    pass


class AdvancedPreferencesPermissionError(PermissionError):
    pass


class ThemePreferences(BaseModel):
    primary_color: str = Field(default="#1677ff")
    dark_mode: bool = Field(default=False)

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class Preferences(BaseModel):
    version: int
    theme: ThemePreferences
    advanced: dict[str, Any] | None = None

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


def default_preferences() -> Preferences:
    return Preferences(
        version=CURRENT_VERSION,
        theme=ThemePreferences(),
        advanced={"betaFeatures": False},
    )


def migrate_preferences(preferences: Preferences) -> Preferences:
    if preferences.version >= CURRENT_VERSION:
        return preferences
    merged = deep_merge(
        default_preferences().model_dump(by_alias=True),
        preferences.model_dump(by_alias=True),
    )
    merged["version"] = CURRENT_VERSION
    return Preferences.model_validate(merged)


def filter_for_user(preferences: Preferences, user_level: int) -> Preferences:
    if user_level < 2:
        data = preferences.model_dump(by_alias=True)
        data["advanced"] = None
        return Preferences.model_validate(data)
    return preferences


def apply_patch(
    preferences: Preferences,
    patch: Mapping[str, Any],
    *,
    user_level: int,
) -> Preferences:
    if "advanced" in patch and user_level < 2:
        raise AdvancedPreferencesPermissionError("advanced requires elevated user level")

    merged = deep_merge(preferences.model_dump(by_alias=True), patch)
    merged["version"] = preferences.version

    try:
        return Preferences.model_validate(merged)
    except Exception as e:  # pragma: no cover
        raise PreferencesValidationError(str(e)) from e


def deep_merge(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = deepcopy(dict(base))
    for key, value in patch.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = deep_merge(result[key], value)  # type: ignore[arg-type]
        else:
            result[key] = value
    return result

