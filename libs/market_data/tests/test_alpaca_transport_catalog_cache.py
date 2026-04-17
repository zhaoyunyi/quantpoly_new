from __future__ import annotations

from market_data.alpaca_transport import AlpacaHTTPTransport, resolve_alpaca_transport_config


def test_alpaca_transport_search_reuses_catalog_cache():
    calls: list[tuple[str, str, dict[str, object]]] = []

    def _request_executor(method: str, path: str, params: dict[str, object], headers: dict[str, str], timeout_seconds: float):
        del headers, timeout_seconds
        calls.append((method, path, dict(params)))
        return 200, [
            {"symbol": "AAPL", "name": "Apple", "exchange": "NASDAQ", "class": "us_equity", "tradable": True},
            {"symbol": "MSFT", "name": "Microsoft", "exchange": "NASDAQ", "class": "us_equity", "tradable": True},
        ]

    transport = AlpacaHTTPTransport(
        config=resolve_alpaca_transport_config(api_key="k", api_secret="s"),
        request_executor=_request_executor,
    )

    first = transport("search", keyword="AAP", limit=10)
    second = transport("search", keyword="AAP", limit=10)

    assert len(calls) == 1
    assert first["items"][0]["symbol"] == "AAPL"
    assert second["items"][0]["symbol"] == "AAPL"


def test_alpaca_transport_asset_detail_uses_direct_endpoint():
    calls: list[str] = []

    def _request_executor(method: str, path: str, params: dict[str, object], headers: dict[str, str], timeout_seconds: float):
        del method, params, headers, timeout_seconds
        calls.append(path)
        return 200, {
            "symbol": "AAPL",
            "name": "Apple",
            "exchange": "NASDAQ",
            "currency": "USD",
            "class": "us_equity",
            "tradable": True,
            "fractionable": True,
        }

    transport = AlpacaHTTPTransport(
        config=resolve_alpaca_transport_config(api_key="k", api_secret="s"),
        request_executor=_request_executor,
    )

    payload = transport("asset_detail", symbol="aapl")

    assert calls == ["https://data.alpaca.markets/v2/assets/AAPL"]
    assert payload["symbol"] == "AAPL"
