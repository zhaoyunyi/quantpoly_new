"""backend composition root 配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass


_DEFAULT_CONTEXTS = {
    "user-auth",
    "user-preferences",
    "strategy-management",
    "job-orchestration",
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
    market_data_provider: str = "inmemory"
    job_executor_mode: str = "inprocess"

    @classmethod
    def from_env(cls) -> "CompositionSettings":
        raw = os.getenv("BACKEND_ENABLED_CONTEXTS", "").strip()
        storage_backend = normalize_storage_backend(os.getenv("BACKEND_STORAGE_BACKEND"))
        sqlite_db_path = os.getenv("BACKEND_SQLITE_DB_PATH", "").strip() or None
        market_data_provider = normalize_market_data_provider(os.getenv("BACKEND_MARKET_DATA_PROVIDER"))
        job_executor_mode = normalize_job_executor_mode(os.getenv("BACKEND_JOB_EXECUTOR_MODE"))
        if not raw:
            return cls(
                enabled_contexts=set(_DEFAULT_CONTEXTS),
                storage_backend=storage_backend,
                sqlite_db_path=sqlite_db_path,
                market_data_provider=market_data_provider,
                job_executor_mode=job_executor_mode,
            )

        selected = {item.strip() for item in raw.split(",") if item.strip()}
        if "user-auth" not in selected:
            selected.add("user-auth")
        return cls(
            enabled_contexts=selected,
            storage_backend=storage_backend,
            sqlite_db_path=sqlite_db_path,
            market_data_provider=market_data_provider,
            job_executor_mode=job_executor_mode,
        )


def normalize_storage_backend(storage_backend: str | None) -> str:
    normalized = (storage_backend or "sqlite").strip().lower()
    if normalized not in {"sqlite", "memory"}:
        raise ValueError("storage_backend must be one of: sqlite, memory")
    return normalized


def normalize_market_data_provider(provider: str | None) -> str:
    normalized = (provider or "inmemory").strip().lower()
    if normalized not in {"inmemory", "alpaca"}:
        raise ValueError("market_data_provider must be one of: inmemory, alpaca")
    return normalized


def normalize_job_executor_mode(mode: str | None) -> str:
    normalized = (mode or "inprocess").strip().lower()
    if normalized not in {"inprocess", "celery-adapter"}:
        raise ValueError("job_executor_mode must be one of: inprocess, celery-adapter")
    return normalized


def normalize_enabled_contexts(enabled_contexts: set[str] | None) -> set[str]:
    if enabled_contexts is None:
        return set(_DEFAULT_CONTEXTS)

    normalized = {item.strip() for item in enabled_contexts if item.strip()}
    normalized.add("user-auth")
    return normalized
