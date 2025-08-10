"""backend composition root 配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass


_DEFAULT_CONTEXTS = {
    "user-auth",
    "user-preferences",
    "strategy-management",
    "backtest-runner",
    "trading-account",
    "market-data",
    "risk-control",
    "signal-execution",
    "monitoring-realtime",
}


@dataclass(frozen=True)
class CompositionSettings:
    enabled_contexts: set[str]
    storage_backend: str
    sqlite_db_path: str | None = None


    @classmethod
    def from_env(cls) -> "CompositionSettings":
        raw = os.getenv("BACKEND_ENABLED_CONTEXTS", "").strip()
        storage_backend = normalize_storage_backend(os.getenv("BACKEND_STORAGE_BACKEND"))
        sqlite_db_path = os.getenv("BACKEND_SQLITE_DB_PATH", "").strip() or None
        if not raw:
            return cls(
                enabled_contexts=set(_DEFAULT_CONTEXTS),
                storage_backend=storage_backend,
                sqlite_db_path=sqlite_db_path,
            )

        selected = {item.strip() for item in raw.split(",") if item.strip()}
        if "user-auth" not in selected:
            selected.add("user-auth")
        return cls(
            enabled_contexts=selected,
            storage_backend=storage_backend,
            sqlite_db_path=sqlite_db_path,
        )


def normalize_storage_backend(storage_backend: str | None) -> str:
    normalized = (storage_backend or "sqlite").strip().lower()
    if normalized not in {"sqlite", "memory"}:
        raise ValueError("storage_backend must be one of: sqlite, memory")
    return normalized


def normalize_enabled_contexts(enabled_contexts: set[str] | None) -> set[str]:
    if enabled_contexts is None:
        return set(_DEFAULT_CONTEXTS)

    normalized = {item.strip() for item in enabled_contexts if item.strip()}
    normalized.add("user-auth")
    return normalized
