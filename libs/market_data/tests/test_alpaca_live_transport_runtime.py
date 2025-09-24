"""alpaca live transport 运行时测试。"""

from __future__ import annotations

import pytest



def test_resolve_alpaca_config_requires_credentials(monkeypatch):
    from market_data.alpaca_transport import resolve_alpaca_transport_config

    monkeypatch.delenv("BACKEND_ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("BACKEND_ALPACA_API_SECRET", raising=False)

    with pytest.raises(ValueError, match="ALPACA_CONFIG_MISSING"):
        resolve_alpaca_transport_config(env_prefixes=("BACKEND_ALPACA",))



def test_alpaca_http_transport_maps_401_429_timeout_to_standard_errors():
    from market_data.alpaca_transport import AlpacaHTTPTransport, AlpacaTransportConfig
    from market_data.domain import UpstreamRateLimitedError, UpstreamTimeoutError, UpstreamUnauthorizedError

    config = AlpacaTransportConfig(
        api_key="key",
        api_secret="secret",
        base_url="https://example.invalid",
        timeout_seconds=1.0,
    )

    def _request_401(*, method, path, params, headers, timeout_seconds):
        del method, path, params, headers, timeout_seconds
        return 401, {"message": "unauthorized"}

    def _request_429(*, method, path, params, headers, timeout_seconds):
        del method, path, params, headers, timeout_seconds
        return 429, {"message": "rate limited"}

    def _request_timeout(*, method, path, params, headers, timeout_seconds):
        del method, path, params, headers, timeout_seconds
        raise TimeoutError("timeout")

    unauthorized_transport = AlpacaHTTPTransport(config=config, request_executor=_request_401)
    with pytest.raises(UpstreamUnauthorizedError):
        unauthorized_transport("quote", symbol="AAPL")

    rate_limited_transport = AlpacaHTTPTransport(config=config, request_executor=_request_429)
    with pytest.raises(UpstreamRateLimitedError):
        rate_limited_transport("quote", symbol="AAPL")

    timeout_transport = AlpacaHTTPTransport(config=config, request_executor=_request_timeout)
    with pytest.raises(UpstreamTimeoutError):
        timeout_transport("quote", symbol="AAPL")



def test_alpaca_transport_health_exposes_last_failure_reason():
    from market_data.alpaca_transport import AlpacaHTTPTransport, AlpacaTransportConfig

    config = AlpacaTransportConfig(
        api_key="key",
        api_secret="secret",
        base_url="https://example.invalid",
        timeout_seconds=1.0,
    )

    def _request_401(*, method, path, params, headers, timeout_seconds):
        del method, path, params, headers, timeout_seconds
        return 401, {"message": "unauthorized"}

    transport = AlpacaHTTPTransport(config=config, request_executor=_request_401)

    with pytest.raises(Exception):
        transport("quote", symbol="AAPL")

    health = transport.health()
    assert health["provider"] == "alpaca"
    assert health["healthy"] is False
    assert health["lastFailureCode"] == "UPSTREAM_AUTH_FAILED"
    assert isinstance(health.get("lastLatencyMs"), int)
