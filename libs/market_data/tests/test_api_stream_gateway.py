"""market_data 流网关 API 测试。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from market_data.domain import MarketQuote, UpstreamTimeoutError


class _User:
    def __init__(self, user_id: str):
        self.id = user_id


class _StableProvider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        normalized = symbol.upper()
        return MarketQuote(
            symbol=normalized,
            name=normalized,
            price=100.0,
            timestamp=datetime(2026, 2, 12, 9, 0, tzinfo=timezone.utc),
        )

    def history(self, *, symbol: str, start_date: str, end_date: str, timeframe: str, limit: int | None):
        del symbol, start_date, end_date, timeframe, limit
        return []

    def list_assets(self, *, limit: int):
        del limit
        return []

    def batch_quote(self, *, symbols: list[str]):
        return {item.upper(): self.quote(symbol=item) for item in symbols}

    def health(self):
        return {"provider": "stable", "healthy": True, "status": "ok", "message": ""}


class _TimeoutProvider(_StableProvider):
    def quote(self, *, symbol: str):
        del symbol
        raise UpstreamTimeoutError()


def _build_client(*, provider, current_user_id: str = "u-1") -> TestClient:
    from market_data.api import create_router
    from market_data.service import MarketDataService

    def _get_current_user():
        return _User(current_user_id)

    app = FastAPI()
    app.include_router(
        create_router(
            service=MarketDataService(provider=provider),
            get_current_user=_get_current_user,
        )
    )
    return TestClient(app)


def test_stream_websocket_subscribe_receive_event_and_unsubscribe():
    client = _build_client(provider=_StableProvider())

    with client.websocket_connect("/market/stream") as ws:
        ready = ws.receive_json()
        assert ready["type"] == "stream.ready"

        ws.send_json(
            {
                "action": "subscribe",
                "symbols": ["aapl", "msft"],
                "channel": "quote",
                "timeframe": "1Min",
            }
        )
        subscribed = ws.receive_json()
        assert subscribed["type"] == "stream.subscribed"
        assert subscribed["channel"] == "quote"

        event = ws.receive_json()
        assert event["type"] == "market.quote"
        assert event["symbol"] in {"AAPL", "MSFT"}
        assert event["payload"]["price"] == 100.0

        maybe_next = ws.receive_json()
        if maybe_next["type"] == "market.quote":
            assert maybe_next["symbol"] in {"AAPL", "MSFT"}
            assert maybe_next["payload"]["price"] == 100.0

        ws.send_json({"action": "unsubscribe", "subscriptionId": subscribed["subscriptionId"]})
        unsubscribed = ws.receive_json()
        assert unsubscribed["type"] == "stream.unsubscribed"


def test_stream_websocket_rejects_illegal_subscription_without_creating():
    client = _build_client(provider=_StableProvider())

    with client.websocket_connect("/market/stream") as ws:
        _ready = ws.receive_json()

        ws.send_json(
            {
                "action": "subscribe",
                "symbols": ["AAPL"],
                "channel": "illegal",
                "timeframe": "1Min",
            }
        )
        error = ws.receive_json()
        assert error["type"] == "stream.error"
        assert error["code"] == "STREAM_INVALID_SUBSCRIPTION"


def test_stream_websocket_marks_degraded_and_status_endpoint_exposes_fallback_hint():
    client = _build_client(provider=_TimeoutProvider())

    with client.websocket_connect("/market/stream") as ws:
        _ready = ws.receive_json()

        ws.send_json(
            {
                "action": "subscribe",
                "symbols": ["AAPL"],
                "channel": "quote",
                "timeframe": "1Min",
            }
        )
        _subscribed = ws.receive_json()
        degraded = ws.receive_json()
        assert degraded["type"] == "stream.degraded"
        assert degraded["payload"]["fallbackHint"]

    status = client.get("/market/stream/status")
    assert status.status_code == 200
    payload = status.json()
    assert payload["success"] is True
    assert payload["data"]["stream"]["status"] == "degraded"
    assert payload["data"]["stream"]["fallbackHint"]


def test_stream_websocket_auth_failure_closes_connection():
    from market_data.api import create_router
    from market_data.service import MarketDataService

    def _deny_user():
        raise PermissionError("UNAUTHORIZED")

    app = FastAPI()
    app.include_router(
        create_router(
            service=MarketDataService(provider=_StableProvider()),
            get_current_user=_deny_user,
        )
    )
    client = TestClient(app)

    with client.websocket_connect("/market/stream") as ws:
        payload = ws.receive_json()
        assert payload["type"] == "stream.error"
        assert payload["code"] == "STREAM_AUTH_REQUIRED"
