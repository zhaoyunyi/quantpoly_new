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
    postgres_dsn: str | None = None
    market_data_provider: str = "inmemory"
    job_executor_mode: str = "inprocess"
    cors_allowed_origins: tuple[str, ...] = ()
    cors_allow_credentials: bool = True
    cors_allow_methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    cors_allow_headers: tuple[str, ...] = ("*",)

    @classmethod
    def from_env(cls) -> "CompositionSettings":
        raw = os.getenv("BACKEND_ENABLED_CONTEXTS", "").strip()
        storage_backend = normalize_storage_backend(os.getenv("BACKEND_STORAGE_BACKEND"))
        postgres_dsn = os.getenv("BACKEND_POSTGRES_DSN", "").strip() or None
        market_data_provider = normalize_market_data_provider(os.getenv("BACKEND_MARKET_DATA_PROVIDER"))
        job_executor_mode = normalize_job_executor_mode(os.getenv("BACKEND_JOB_EXECUTOR_MODE"))
        cors_allowed_origins = normalize_cors_allowed_origins(os.getenv("BACKEND_CORS_ALLOWED_ORIGINS"))
        cors_allow_credentials = normalize_cors_allow_credentials(os.getenv("BACKEND_CORS_ALLOW_CREDENTIALS"))
        cors_allow_methods = normalize_cors_allow_methods(os.getenv("BACKEND_CORS_ALLOW_METHODS"))
        cors_allow_headers = normalize_cors_allow_headers(os.getenv("BACKEND_CORS_ALLOW_HEADERS"))
        if not raw:
            return cls(
                enabled_contexts=set(_DEFAULT_CONTEXTS),
                storage_backend=storage_backend,
                postgres_dsn=postgres_dsn,
                market_data_provider=market_data_provider,
                job_executor_mode=job_executor_mode,
                cors_allowed_origins=cors_allowed_origins,
                cors_allow_credentials=cors_allow_credentials,
                cors_allow_methods=cors_allow_methods,
                cors_allow_headers=cors_allow_headers,
            )

        selected = {item.strip() for item in raw.split(",") if item.strip()}
        if "user-auth" not in selected:
            selected.add("user-auth")
        return cls(
            enabled_contexts=selected,
            storage_backend=storage_backend,
            postgres_dsn=postgres_dsn,
            market_data_provider=market_data_provider,
            job_executor_mode=job_executor_mode,
            cors_allowed_origins=cors_allowed_origins,
            cors_allow_credentials=cors_allow_credentials,
            cors_allow_methods=cors_allow_methods,
            cors_allow_headers=cors_allow_headers,
        )


def normalize_storage_backend(storage_backend: str | None) -> str:
    normalized = (storage_backend or "postgres").strip().lower()
    if normalized not in {"postgres", "memory"}:
        raise ValueError("storage_backend must be one of: postgres, memory")
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


def _parse_csv(value: str | None) -> tuple[str, ...]:
    raw = (value or "").strip()
    if not raw:
        return ()
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    raw = value.strip()
    if not raw:
        return default
    lowered = raw.lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError("cors allow_credentials must be a boolean")


def normalize_cors_allowed_origins(value: str | None) -> tuple[str, ...]:
    origins = _parse_csv(value)
    if not origins:
        return ()
    if "*" in origins:
        raise ValueError("cors allowed_origins must not include '*' when credentials are enabled")
    return origins


def normalize_cors_allow_credentials(value: str | None) -> bool:
    return _parse_bool(value, default=True)


def normalize_cors_allow_methods(value: str | None) -> tuple[str, ...]:
    methods = _parse_csv(value)
    if not methods:
        return ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    return tuple(item.upper() for item in methods)


def normalize_cors_allow_headers(value: str | None) -> tuple[str, ...]:
    headers = _parse_csv(value)
    if not headers:
        return ("*",)
    return headers
