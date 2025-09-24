"""Alpaca HTTP transport 与配置装配。"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from market_data.domain import (
    MarketDataError,
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
    UpstreamUnauthorizedError,
    UpstreamUnavailableError,
)

RequestExecutor = Callable[
    [
        str,
        str,
        dict[str, Any],
        dict[str, str],
        float,
    ],
    tuple[int, Any],
]


@dataclass(frozen=True)
class AlpacaTransportConfig:
    api_key: str
    api_secret: str
    base_url: str = "https://data.alpaca.markets"
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "api_key", self.api_key.strip())
        object.__setattr__(self, "api_secret", self.api_secret.strip())
        object.__setattr__(self, "base_url", self.base_url.strip().rstrip("/"))

        if not self.api_key or not self.api_secret:
            raise ValueError("ALPACA_CONFIG_MISSING: api key/secret are required")
        if self.timeout_seconds <= 0:
            raise ValueError("ALPACA_CONFIG_INVALID_TIMEOUT: timeout_seconds must be > 0")

    def auth_headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Accept": "application/json",
        }


_DEFAULT_ENV_PREFIXES = ("BACKEND_ALPACA", "MARKET_DATA_ALPACA")


def _first_non_empty(values: list[str | None]) -> str | None:
    for value in values:
        if value is None:
            continue
        normalized = value.strip()
        if normalized:
            return normalized
    return None


def _resolve_env_value(*, env: Mapping[str, str], env_prefixes: tuple[str, ...], suffix: str) -> str | None:
    for prefix in env_prefixes:
        value = env.get(f"{prefix}_{suffix}")
        if value is not None and value.strip():
            return value.strip()
    return None


def resolve_alpaca_transport_config(
    *,
    api_key: str | None = None,
    api_secret: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float | None = None,
    env: Mapping[str, str] | None = None,
    env_prefixes: tuple[str, ...] = _DEFAULT_ENV_PREFIXES,
) -> AlpacaTransportConfig:
    """从显式参数/环境变量解析 Alpaca transport 配置。"""

    source_env = env if env is not None else os.environ

    resolved_api_key = _first_non_empty(
        [
            api_key,
            _resolve_env_value(env=source_env, env_prefixes=env_prefixes, suffix="API_KEY"),
        ]
    )
    resolved_api_secret = _first_non_empty(
        [
            api_secret,
            _resolve_env_value(env=source_env, env_prefixes=env_prefixes, suffix="API_SECRET"),
        ]
    )

    if not resolved_api_key or not resolved_api_secret:
        raise ValueError("ALPACA_CONFIG_MISSING: api key/secret are required")

    resolved_base_url = _first_non_empty(
        [
            base_url,
            _resolve_env_value(env=source_env, env_prefixes=env_prefixes, suffix="BASE_URL"),
            "https://data.alpaca.markets",
        ]
    )

    timeout_text = _first_non_empty(
        [
            str(timeout_seconds) if timeout_seconds is not None else None,
            _resolve_env_value(env=source_env, env_prefixes=env_prefixes, suffix="TIMEOUT_SECONDS"),
            "5",
        ]
    )

    try:
        resolved_timeout = float(timeout_text or "5")
    except ValueError as exc:
        raise ValueError("ALPACA_CONFIG_INVALID_TIMEOUT: timeout_seconds must be numeric") from exc

    return AlpacaTransportConfig(
        api_key=resolved_api_key,
        api_secret=resolved_api_secret,
        base_url=resolved_base_url or "https://data.alpaca.markets",
        timeout_seconds=resolved_timeout,
    )


def _decode_json_payload(raw: bytes) -> Any:
    if not raw:
        return {}
    text = raw.decode("utf-8", errors="ignore").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _default_request_executor(
    method: str,
    path: str,
    params: dict[str, Any],
    headers: dict[str, str],
    timeout_seconds: float,
) -> tuple[int, Any]:
    query = urlencode({key: value for key, value in params.items() if value is not None})
    full_url = f"{path}?{query}" if query else path
    req = Request(full_url, headers=headers, method=method)

    try:
        with urlopen(req, timeout=timeout_seconds) as resp:  # noqa: S310
            status = int(resp.status)
            body = resp.read()
            return status, _decode_json_payload(body)
    except HTTPError as exc:
        status = int(exc.code)
        body = exc.read() if hasattr(exc, "read") else b""
        return status, _decode_json_payload(body)
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError):
            raise TimeoutError("alpaca request timeout") from exc
        raise RuntimeError(f"alpaca request failed: {reason or exc}") from exc


class AlpacaHTTPTransport:
    """可运行的 Alpaca HTTP transport。"""

    def __init__(
        self,
        *,
        config: AlpacaTransportConfig,
        request_executor: Callable[..., tuple[int, Any]] | None = None,
    ) -> None:
        self._config = config
        self._request_executor = request_executor or _default_request_executor

        self._healthy = True
        self._status = "ok"
        self._message = ""
        self._last_latency_ms = 0
        self._last_failure_code: str | None = None

    def _record_success(self, *, latency_ms: int) -> None:
        self._healthy = True
        self._status = "ok"
        self._message = ""
        self._last_latency_ms = latency_ms
        self._last_failure_code = None

    def _record_failure(self, *, latency_ms: int, code: str, message: str) -> None:
        self._healthy = False
        self._status = "degraded"
        self._message = message
        self._last_latency_ms = latency_ms
        self._last_failure_code = code

    def _request_json(self, *, path: str, params: dict[str, Any]) -> Any:
        started = time.perf_counter()
        url = f"{self._config.base_url}{path}"

        try:
            status, payload = self._request_executor(
                method="GET",
                path=url,
                params=params,
                headers=self._config.auth_headers(),
                timeout_seconds=self._config.timeout_seconds,
            )
        except TimeoutError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._record_failure(latency_ms=latency_ms, code="UPSTREAM_TIMEOUT", message="alpaca request timeout")
            raise UpstreamTimeoutError("alpaca request timeout") from exc
        except MarketDataError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._record_failure(latency_ms=latency_ms, code=exc.code, message=exc.message)
            raise
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._record_failure(latency_ms=latency_ms, code="UPSTREAM_UNAVAILABLE", message=str(exc))
            raise UpstreamUnavailableError(str(exc)) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        if status in {401, 403}:
            self._record_failure(latency_ms=latency_ms, code="UPSTREAM_AUTH_FAILED", message="alpaca auth failed")
            raise UpstreamUnauthorizedError("alpaca auth failed")
        if status == 429:
            self._record_failure(latency_ms=latency_ms, code="UPSTREAM_RATE_LIMITED", message="alpaca rate limited")
            raise UpstreamRateLimitedError("alpaca rate limited")
        if status >= 500:
            self._record_failure(
                latency_ms=latency_ms,
                code="UPSTREAM_UNAVAILABLE",
                message=f"alpaca upstream unavailable: status={status}",
            )
            raise UpstreamUnavailableError(f"alpaca upstream unavailable: status={status}")
        if status >= 400:
            self._record_failure(
                latency_ms=latency_ms,
                code="UPSTREAM_UNAVAILABLE",
                message=f"alpaca request failed: status={status}",
            )
            raise UpstreamUnavailableError(f"alpaca request failed: status={status}")

        self._record_success(latency_ms=latency_ms)
        return payload

    @staticmethod
    def _contains_keyword(*, item: dict[str, Any], keyword: str) -> bool:
        if not keyword:
            return True
        lowered = keyword.lower()
        symbol = str(item.get("symbol", "")).lower()
        name = str(item.get("name", "")).lower()
        return lowered in symbol or lowered in name

    def _search_assets(self, *, keyword: str, limit: int) -> dict[str, Any]:
        payload = self._request_json(
            path="/v2/assets",
            params={
                "status": "active",
                "asset_class": "us_equity",
            },
        )
        raw_items = payload if isinstance(payload, list) else payload.get("assets", [])
        items: list[dict[str, Any]] = []

        for item in raw_items:
            if not isinstance(item, dict):
                continue
            if not self._contains_keyword(item=item, keyword=keyword):
                continue
            symbol = str(item.get("symbol", "")).upper().strip()
            if not symbol:
                continue
            items.append(
                {
                    "symbol": symbol,
                    "name": str(item.get("name") or symbol),
                    "exchange": item.get("exchange"),
                    "currency": item.get("currency", "USD"),
                    "assetClass": item.get("class", item.get("assetClass", "us_equity")),
                    "tradable": bool(item.get("tradable", True)),
                    "fractionable": bool(item.get("fractionable", False)),
                }
            )
            if len(items) >= max(1, limit):
                break

        return {"items": items}

    def _quote_snapshot(self, *, symbol: str) -> dict[str, Any]:
        payload = self._request_json(
            path=f"/v2/stocks/{symbol}/snapshot",
            params={"feed": "iex"},
        )

        snapshot = payload.get("snapshot") if isinstance(payload, dict) and isinstance(payload.get("snapshot"), dict) else payload
        if not isinstance(snapshot, dict):
            snapshot = {}

        latest_trade = snapshot.get("latestTrade") if isinstance(snapshot.get("latestTrade"), dict) else {}
        latest_quote = snapshot.get("latestQuote") if isinstance(snapshot.get("latestQuote"), dict) else {}
        daily_bar = snapshot.get("dailyBar") if isinstance(snapshot.get("dailyBar"), dict) else {}
        prev_daily_bar = snapshot.get("prevDailyBar") if isinstance(snapshot.get("prevDailyBar"), dict) else {}

        return {
            "name": symbol,
            "price": latest_trade.get("p"),
            "previousClose": prev_daily_bar.get("c"),
            "open": daily_bar.get("o"),
            "high": daily_bar.get("h"),
            "low": daily_bar.get("l"),
            "volume": daily_bar.get("v"),
            "bidPrice": latest_quote.get("bp"),
            "askPrice": latest_quote.get("ap"),
            "timestamp": latest_trade.get("t") or daily_bar.get("t"),
        }

    def _history_bars(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ) -> dict[str, Any]:
        payload = self._request_json(
            path=f"/v2/stocks/{symbol}/bars",
            params={
                "start": start_date,
                "end": end_date,
                "timeframe": timeframe,
                "limit": limit,
                "feed": "iex",
            },
        )

        raw_bars = payload.get("bars", []) if isinstance(payload, dict) else []
        items: list[dict[str, Any]] = []
        for bar in raw_bars:
            if not isinstance(bar, dict):
                continue
            items.append(
                {
                    "timestamp": bar.get("t"),
                    "open": bar.get("o"),
                    "high": bar.get("h"),
                    "low": bar.get("l"),
                    "close": bar.get("c"),
                    "volume": bar.get("v"),
                }
            )

        return {"items": items}

    def __call__(self, operation: str, **kwargs):
        op = operation.strip().lower()
        if op == "search":
            keyword = str(kwargs.get("keyword", ""))
            limit = int(kwargs.get("limit", 10))
            return self._search_assets(keyword=keyword, limit=limit)
        if op == "quote":
            symbol = str(kwargs.get("symbol", "")).upper().strip()
            return self._quote_snapshot(symbol=symbol)
        if op == "history":
            symbol = str(kwargs.get("symbol", "")).upper().strip()
            return self._history_bars(
                symbol=symbol,
                start_date=str(kwargs.get("start_date", "")),
                end_date=str(kwargs.get("end_date", "")),
                timeframe=str(kwargs.get("timeframe", "1Day")),
                limit=int(kwargs["limit"]) if kwargs.get("limit") is not None else None,
            )
        raise ValueError(f"unsupported alpaca operation: {operation}")

    def health(self) -> dict[str, Any]:
        return {
            "provider": "alpaca",
            "transport": "alpaca-http",
            "healthy": self._healthy,
            "status": self._status,
            "message": self._message,
            "baseUrl": self._config.base_url,
            "timeoutSeconds": self._config.timeout_seconds,
            "lastLatencyMs": self._last_latency_ms,
            "lastFailureCode": self._last_failure_code,
        }
