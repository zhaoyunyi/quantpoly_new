"""market_data 库。"""

from market_data.alpaca_provider import AlpacaProvider
from market_data.alpaca_transport import AlpacaHTTPTransport, AlpacaTransportConfig, resolve_alpaca_transport_config
from market_data.cache import InMemoryTTLCache
from market_data.domain import (
    BatchQuoteItem,
    MarketAsset,
    MarketCandle,
    MarketDataError,
    MarketQuote,
    RateLimitExceededError,
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
    UpstreamUnauthorizedError,
    UpstreamUnavailableError,
)
from market_data.rate_limit import SlidingWindowRateLimiter
from market_data.service import BatchQuoteResult, MarketDataService, QuoteResult

__all__ = [
    "AlpacaProvider",
    "AlpacaHTTPTransport",
    "AlpacaTransportConfig",
    "resolve_alpaca_transport_config",
    "InMemoryTTLCache",
    "SlidingWindowRateLimiter",
    "MarketDataService",
    "QuoteResult",
    "BatchQuoteResult",
    "MarketDataError",
    "MarketAsset",
    "MarketQuote",
    "BatchQuoteItem",
    "MarketCandle",
    "RateLimitExceededError",
    "UpstreamTimeoutError",
    "UpstreamUnavailableError",
    "UpstreamUnauthorizedError",
    "UpstreamRateLimitedError",
]
