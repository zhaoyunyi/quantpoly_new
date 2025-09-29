"""market_data 流网关库测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from market_data.domain import BatchQuoteItem, MarketQuote, UpstreamTimeoutError
from market_data.service import BatchQuoteResult
from market_data.stream_gateway import MarketDataStreamGateway, StreamGatewayError


def _quote_result(*symbols: str) -> BatchQuoteResult:
    now = datetime(2026, 2, 12, 9, 0, tzinfo=timezone.utc)
    return BatchQuoteResult(
        items=[
            BatchQuoteItem(
                symbol=symbol,
                status="ok",
                quote=MarketQuote(symbol=symbol, name=symbol, price=123.45, timestamp=now),
                cache_hit=False,
                source="provider",
            )
            for symbol in symbols
        ],
        timestamp=int(now.timestamp()),
    )


def test_stream_gateway_subscribe_and_poll_quote_events_with_envelope():
    gateway = MarketDataStreamGateway(
        quote_reader=lambda user_id, symbols: _quote_result(*symbols),
    )

    subscription = gateway.subscribe(
        user_id="u-1",
        symbols=["aapl", "msft"],
        channel="quote",
        timeframe="1Min",
    )

    events = gateway.poll_events(user_id="u-1", subscription_id=subscription.id)

    assert len(events) == 2
    first = events[0]
    assert first["type"] == "market.quote"
    assert first["symbol"] in {"AAPL", "MSFT"}
    assert first["timestamp"]
    assert first["payload"]["price"] == 123.45


def test_stream_gateway_rejects_illegal_channel():
    gateway = MarketDataStreamGateway(
        quote_reader=lambda user_id, symbols: _quote_result(*symbols),
    )

    with pytest.raises(StreamGatewayError) as exc_info:
        gateway.subscribe(
            user_id="u-1",
            symbols=["AAPL"],
            channel="illegal",
            timeframe="1Min",
        )

    assert exc_info.value.code == "STREAM_INVALID_SUBSCRIPTION"


def test_stream_gateway_enforces_subscription_limit():
    gateway = MarketDataStreamGateway(
        quote_reader=lambda user_id, symbols: _quote_result(*symbols),
        max_subscriptions_per_user=1,
    )

    gateway.subscribe(user_id="u-1", symbols=["AAPL"], channel="quote", timeframe="1Min")

    with pytest.raises(StreamGatewayError) as exc_info:
        gateway.subscribe(user_id="u-1", symbols=["MSFT"], channel="quote", timeframe="1Min")

    assert exc_info.value.code == "STREAM_SUBSCRIPTION_LIMIT_EXCEEDED"


def test_stream_gateway_marks_degraded_and_returns_fallback_hint_when_upstream_fails():
    gateway = MarketDataStreamGateway(
        quote_reader=lambda user_id, symbols: (_ for _ in ()).throw(UpstreamTimeoutError()),
    )

    subscription = gateway.subscribe(
        user_id="u-1",
        symbols=["AAPL"],
        channel="quote",
        timeframe="1Min",
    )

    events = gateway.poll_events(user_id="u-1", subscription_id=subscription.id)
    health = gateway.health(user_id="u-1")

    assert len(events) == 1
    assert events[0]["type"] == "stream.degraded"
    assert events[0]["payload"]["fallbackHint"]
    assert health["status"] == "degraded"
    assert health["fallbackHint"]
