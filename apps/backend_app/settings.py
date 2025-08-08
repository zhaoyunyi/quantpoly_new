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


    @classmethod
    def from_env(cls) -> "CompositionSettings":
        raw = os.getenv("BACKEND_ENABLED_CONTEXTS", "").strip()
        if not raw:
            return cls(enabled_contexts=set(_DEFAULT_CONTEXTS))

        selected = {item.strip() for item in raw.split(",") if item.strip()}
        if "user-auth" not in selected:
            selected.add("user-auth")
        return cls(enabled_contexts=selected)


def normalize_enabled_contexts(enabled_contexts: set[str] | None) -> set[str]:
    if enabled_contexts is None:
        return set(_DEFAULT_CONTEXTS)

    normalized = {item.strip() for item in enabled_contexts if item.strip()}
    normalized.add("user-auth")
    return normalized
