"""用户偏好（preferences）领域模型与纯函数操作。"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
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


class AccountPreferences(BaseModel):
    default_trading_account_id: str | None = None
    risk_tolerance: str = "moderate"
    default_currency: str = "USD"
    auto_select_account: bool = True

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class NotificationEmailPreferences(BaseModel):
    enabled: bool = True
    trading_alerts: bool = True
    risk_alerts: bool = True
    system_updates: bool = False
    market_summary: bool = False

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class NotificationBrowserPreferences(BaseModel):
    enabled: bool = True
    permission: str = "default"
    trading_signals: bool = True
    risk_warnings: bool = True

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class NotificationAlertThresholds(BaseModel):
    profit_threshold: float = 10
    loss_threshold: float = 5
    risk_level: str = "medium"

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class NotificationPreferences(BaseModel):
    email: NotificationEmailPreferences = Field(default_factory=NotificationEmailPreferences)
    browser: NotificationBrowserPreferences = Field(default_factory=NotificationBrowserPreferences)
    alert_thresholds: NotificationAlertThresholds = Field(default_factory=NotificationAlertThresholds)

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class DataChartPreferences(BaseModel):
    default_chart_type: str = "line"
    show_volume: bool = True
    show_indicators: bool = False
    auto_scale: bool = True

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class DataTablePreferences(BaseModel):
    page_size: int = 20
    compact_rows: bool = False
    show_decimals: int = 2

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class DataPreferences(BaseModel):
    default_time_range: str = "1M"
    refresh_interval: str = "5s"
    chart_preferences: DataChartPreferences = Field(default_factory=DataChartPreferences)
    table_preferences: DataTablePreferences = Field(default_factory=DataTablePreferences)

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class Preferences(BaseModel):
    version: int
    theme: ThemePreferences
    account: AccountPreferences
    notifications: NotificationPreferences
    data: DataPreferences
    advanced: dict[str, Any] | None = None
    last_updated: str
    sync_enabled: bool = True

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


def default_preferences() -> Preferences:
    return Preferences(
        version=CURRENT_VERSION,
        theme=ThemePreferences(),
        account=AccountPreferences(),
        notifications=NotificationPreferences(),
        data=DataPreferences(),
        advanced={"betaFeatures": False},
        last_updated=datetime.now(timezone.utc).isoformat(),
        sync_enabled=True,
    )


def migrate_preferences(preferences: Preferences | Mapping[str, Any]) -> Preferences:
    incoming = preferences
    if isinstance(preferences, Mapping):
        incoming = Preferences.model_validate(
            deep_merge(default_preferences().model_dump(by_alias=True), preferences)
        )

    if incoming.version >= CURRENT_VERSION:
        return incoming

    merged = deep_merge(
        default_preferences().model_dump(by_alias=True),
        incoming.model_dump(by_alias=True),
    )
    merged["version"] = CURRENT_VERSION
    merged["lastUpdated"] = datetime.now(timezone.utc).isoformat()
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
    merged["lastUpdated"] = datetime.now(timezone.utc).isoformat()

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
