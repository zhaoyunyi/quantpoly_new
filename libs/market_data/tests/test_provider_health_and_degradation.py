"""market_data provider 健康与降级语义测试。"""

from __future__ import annotations

import pytest

from market_data.domain import MarketQuote, UpstreamTimeoutError
from market_data.service import MarketDataService


class _TimeoutProvider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        del symbol
        raise TimeoutError("provider timeout")

    def history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ):
        del symbol, start_date, end_date, timeframe, limit
        return []

    def list_assets(self, *, limit: int):
        del limit
        return []

    def batch_quote(self, *, symbols: list[str]):
        del symbols
        raise TimeoutError("provider timeout")

    def health(self):
        return {
            "provider": "fake",
            "healthy": False,
            "status": "degraded",
            "message": "upstream timeout",
        }


class _HealthyProvider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        return MarketQuote(symbol=symbol, name=symbol, price=1.0)

    def history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ):
        del symbol, start_date, end_date, timeframe, limit
        return []

    def list_assets(self, *, limit: int):
        del limit
        return []

    def batch_quote(self, *, symbols: list[str]):
        return {symbol: MarketQuote(symbol=symbol, name=symbol, price=1.0) for symbol in symbols}

    def health(self):
        return {
            "provider": "fake",
            "healthy": True,
            "status": "ok",
            "message": "",
        }


def test_quote_timeout_maps_to_upstream_timeout_error():
    service = MarketDataService(provider=_TimeoutProvider())

    with pytest.raises(UpstreamTimeoutError) as exc_info:
        service.get_latest_quote(user_id="u-1", symbol="AAPL")

    assert exc_info.value.code == "UPSTREAM_TIMEOUT"
    assert exc_info.value.retryable is True


def test_batch_quote_timeout_maps_to_upstream_timeout_error():
    service = MarketDataService(provider=_TimeoutProvider())

    with pytest.raises(UpstreamTimeoutError) as exc_info:
        service.get_quotes(user_id="u-1", symbols=["AAPL", "MSFT"])

    assert exc_info.value.code == "UPSTREAM_TIMEOUT"
    assert exc_info.value.retryable is True


def test_provider_health_is_exposed():
    service = MarketDataService(provider=_HealthyProvider())

    payload = service.provider_health(user_id="u-1")

    assert payload["provider"] == "fake"
    assert payload["healthy"] is True
    assert payload["status"] == "ok"
    assert isinstance(payload["timestamp"], int)
