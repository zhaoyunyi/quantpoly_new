"""市场数据领域模型与错误定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


class MarketDataError(RuntimeError):
    def __init__(self, *, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


class UpstreamTimeoutError(MarketDataError):
    def __init__(self, message: str = "upstream market data timeout") -> None:
        super().__init__(code="UPSTREAM_TIMEOUT", message=message, retryable=True)


class UpstreamUnavailableError(MarketDataError):
    def __init__(self, message: str = "upstream market data unavailable") -> None:
        super().__init__(code="UPSTREAM_UNAVAILABLE", message=message, retryable=True)


class RateLimitExceededError(MarketDataError):
    def __init__(self, message: str = "quote rate limit exceeded") -> None:
        super().__init__(code="RATE_LIMIT_EXCEEDED", message=message, retryable=True)


@dataclass
class MarketAsset:
    symbol: str
    name: str
    exchange: str | None = None
    currency: str = "USD"
    asset_class: str = "us_equity"
    tradable: bool = True
    fractionable: bool = False


@dataclass
class MarketQuote:
    symbol: str
    name: str
    price: float | None = None
    previous_close: float | None = None
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    volume: float | None = None
    bid_price: float | None = None
    ask_price: float | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BatchQuoteItem:
    symbol: str
    status: str
    quote: MarketQuote | None = None
    error_code: str | None = None
    error_message: str | None = None
    cache_hit: bool = False
    source: str = "provider"


@dataclass
class MarketCandle:
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
