"""market_data 实时流网关（in-memory 基线）。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from market_data.domain import BatchQuoteItem, MarketDataError
from market_data.service import BatchQuoteResult


class StreamGatewayError(RuntimeError):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class StreamSubscription:
    id: str
    user_id: str
    symbols: list[str]
    channel: str
    timeframe: str
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_payload(self) -> dict[str, Any]:
        return {
            "subscriptionId": self.id,
            "userId": self.user_id,
            "symbols": list(self.symbols),
            "channel": self.channel,
            "timeframe": self.timeframe,
            "status": self.status,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


class MarketDataStreamGateway:
    def __init__(
        self,
        *,
        quote_reader: Callable[[str, list[str]], BatchQuoteResult],
        max_symbols_per_subscription: int = 20,
        max_subscriptions_per_user: int = 5,
        max_connections_per_user: int = 3,
    ) -> None:
        self._quote_reader = quote_reader
        self._max_symbols_per_subscription = max_symbols_per_subscription
        self._max_subscriptions_per_user = max_subscriptions_per_user
        self._max_connections_per_user = max_connections_per_user
        self._subscriptions: dict[str, dict[str, StreamSubscription]] = {}
        self._connections: dict[str, set[str]] = {}
        self._status = "ok"
        self._fallback_hint: str | None = None
        self._last_error_code: str | None = None
        self._last_error_message: str | None = None
        self._updated_at = datetime.now(timezone.utc)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_symbols(symbols: list[str]) -> list[str]:
        normalized: list[str] = []
        for symbol in symbols:
            candidate = str(symbol).strip().upper()
            if not candidate:
                continue
            if candidate not in normalized:
                normalized.append(candidate)
        return normalized

    def open_connection(self, *, user_id: str) -> str:
        active = self._connections.setdefault(user_id, set())
        if len(active) >= self._max_connections_per_user:
            raise StreamGatewayError(
                code="STREAM_CONNECTION_LIMIT_EXCEEDED",
                message="stream connection limit exceeded",
            )
        connection_id = str(uuid.uuid4())
        active.add(connection_id)
        return connection_id

    def close_connection(self, *, user_id: str, connection_id: str) -> None:
        active = self._connections.get(user_id)
        if active is None:
            return
        active.discard(connection_id)
        if not active:
            self._connections.pop(user_id, None)

    def subscribe(
        self,
        *,
        user_id: str,
        symbols: list[str],
        channel: str,
        timeframe: str,
    ) -> StreamSubscription:
        normalized_symbols = self._normalize_symbols(symbols)
        channel_normalized = str(channel or "").strip().lower()
        timeframe_normalized = str(timeframe or "1Min").strip() or "1Min"

        if channel_normalized != "quote":
            raise StreamGatewayError(
                code="STREAM_INVALID_SUBSCRIPTION",
                message="unsupported channel",
            )

        if not normalized_symbols:
            raise StreamGatewayError(
                code="STREAM_INVALID_SUBSCRIPTION",
                message="symbols must not be empty",
            )

        if len(normalized_symbols) > self._max_symbols_per_subscription:
            raise StreamGatewayError(
                code="STREAM_SUBSCRIPTION_LIMIT_EXCEEDED",
                message="subscription symbols exceed limit",
            )

        user_subscriptions = self._subscriptions.setdefault(user_id, {})
        if len(user_subscriptions) >= self._max_subscriptions_per_user:
            raise StreamGatewayError(
                code="STREAM_SUBSCRIPTION_LIMIT_EXCEEDED",
                message="subscription count exceeded",
            )

        now = datetime.now(timezone.utc)
        subscription = StreamSubscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            symbols=normalized_symbols,
            channel=channel_normalized,
            timeframe=timeframe_normalized,
            created_at=now,
            updated_at=now,
        )
        user_subscriptions[subscription.id] = subscription
        return subscription

    def list_subscriptions(self, *, user_id: str) -> list[StreamSubscription]:
        return list(self._subscriptions.get(user_id, {}).values())

    def unsubscribe(self, *, user_id: str, subscription_id: str) -> bool:
        user_subscriptions = self._subscriptions.get(user_id)
        if user_subscriptions is None:
            return False
        removed = user_subscriptions.pop(subscription_id, None)
        if not user_subscriptions:
            self._subscriptions.pop(user_id, None)
        return removed is not None

    def clear_subscriptions(self, *, user_id: str) -> None:
        self._subscriptions.pop(user_id, None)

    def _set_degraded(self, *, error_code: str, error_message: str) -> None:
        self._status = "degraded"
        self._fallback_hint = "use /market/quote polling endpoint"
        self._last_error_code = error_code
        self._last_error_message = error_message
        self._updated_at = datetime.now(timezone.utc)

    def _set_ok(self) -> None:
        self._status = "ok"
        self._fallback_hint = None
        self._last_error_code = None
        self._last_error_message = None
        self._updated_at = datetime.now(timezone.utc)

    @staticmethod
    def _quote_payload(item: BatchQuoteItem) -> dict[str, Any]:
        quote = item.quote
        if quote is None:
            return {}

        return {
            "price": quote.price,
            "previousClose": quote.previous_close,
            "openPrice": quote.open_price,
            "highPrice": quote.high_price,
            "lowPrice": quote.low_price,
            "volume": quote.volume,
            "bidPrice": quote.bid_price,
            "askPrice": quote.ask_price,
        }

    def poll_events(self, *, user_id: str, subscription_id: str) -> list[dict[str, Any]]:
        subscription = self._subscriptions.get(user_id, {}).get(subscription_id)
        if subscription is None:
            raise StreamGatewayError(
                code="STREAM_SUBSCRIPTION_NOT_FOUND",
                message="subscription not found",
            )

        try:
            result = self._quote_reader(user_id, list(subscription.symbols))
        except MarketDataError as exc:
            self._set_degraded(error_code=exc.code, error_message=exc.message)
            return [
                {
                    "type": "stream.degraded",
                    "symbol": "*",
                    "timestamp": self._now_iso(),
                    "channel": subscription.channel,
                    "subscriptionId": subscription.id,
                    "payload": {
                        "status": "degraded",
                        "errorCode": exc.code,
                        "errorMessage": exc.message,
                        "fallbackHint": self._fallback_hint,
                    },
                }
            ]

        events: list[dict[str, Any]] = []
        error_count = 0

        for item in result.items:
            if item.status != "ok" or item.quote is None:
                error_count += 1
                continue

            events.append(
                {
                    "type": "market.quote",
                    "symbol": item.symbol,
                    "timestamp": (item.quote.timestamp.isoformat() if item.quote.timestamp else self._now_iso()),
                    "channel": subscription.channel,
                    "subscriptionId": subscription.id,
                    "payload": self._quote_payload(item),
                }
            )

        if error_count > 0:
            self._set_degraded(
                error_code="STREAM_PARTIAL_DEGRADED",
                error_message="partial quote fetch failure",
            )
            events.append(
                {
                    "type": "stream.degraded",
                    "symbol": "*",
                    "timestamp": self._now_iso(),
                    "channel": subscription.channel,
                    "subscriptionId": subscription.id,
                    "payload": {
                        "status": "degraded",
                        "errorCode": "STREAM_PARTIAL_DEGRADED",
                        "errorMessage": "partial quote fetch failure",
                        "fallbackHint": self._fallback_hint,
                    },
                }
            )
        else:
            self._set_ok()

        return events

    def health(self, *, user_id: str | None = None) -> dict[str, Any]:
        if user_id is None:
            active_connections = sum(len(rows) for rows in self._connections.values())
            active_subscriptions = sum(len(rows) for rows in self._subscriptions.values())
        else:
            active_connections = len(self._connections.get(user_id, set()))
            active_subscriptions = len(self._subscriptions.get(user_id, {}))

        return {
            "status": self._status,
            "activeConnections": active_connections,
            "activeSubscriptions": active_subscriptions,
            "fallbackHint": self._fallback_hint,
            "lastErrorCode": self._last_error_code,
            "lastErrorMessage": self._last_error_message,
            "updatedAt": self._updated_at.isoformat(),
        }


__all__ = [
    "MarketDataStreamGateway",
    "StreamGatewayError",
    "StreamSubscription",
]
