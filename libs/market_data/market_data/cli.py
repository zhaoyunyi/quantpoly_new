"""market_data CLI。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

from market_data.alpaca_provider import AlpacaProvider
from market_data.alpaca_transport import AlpacaHTTPTransport, resolve_alpaca_transport_config
from market_data.domain import BatchQuoteItem, MarketAsset, MarketCandle, MarketDataError, MarketQuote
from market_data.service import MarketDataService
from market_data.stream_gateway import MarketDataStreamGateway, StreamGatewayError


class _InMemoryProvider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        normalized = symbol.upper()
        return MarketQuote(symbol=normalized, name=normalized, price=0.0)

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
        return {
            symbol.upper(): MarketQuote(symbol=symbol.upper(), name=symbol.upper(), price=0.0)
            for symbol in symbols
        }

    def health(self):
        return {
            "provider": "inmemory",
            "healthy": True,
            "status": "ok",
            "message": "",
        }


_service = MarketDataService(provider=_InMemoryProvider())
_stream_gateway: MarketDataStreamGateway | None = None


def _build_stream_gateway() -> MarketDataStreamGateway:
    return MarketDataStreamGateway(
        quote_reader=lambda user_id, symbols: _service.get_quotes(user_id=user_id, symbols=symbols),
    )


def _get_stream_gateway() -> MarketDataStreamGateway:
    global _stream_gateway

    if _stream_gateway is None:
        _stream_gateway = _build_stream_gateway()
    return _stream_gateway


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _asset_payload(item: MarketAsset) -> dict:
    return {
        "symbol": item.symbol,
        "name": item.name,
        "exchange": item.exchange,
        "currency": item.currency,
        "assetClass": item.asset_class,
        "status": "active" if item.tradable else "inactive",
        "tradable": item.tradable,
        "fractionable": item.fractionable,
    }


def _quote_payload(item: MarketQuote) -> dict:
    return {
        "symbol": item.symbol,
        "name": item.name,
        "price": item.price,
        "previousClose": item.previous_close,
        "openPrice": item.open_price,
        "highPrice": item.high_price,
        "lowPrice": item.low_price,
        "volume": item.volume,
        "bidPrice": item.bid_price,
        "askPrice": item.ask_price,
        "timestamp": _dt(item.timestamp),
    }


def _batch_item_payload(item: BatchQuoteItem) -> dict:
    payload: dict = {
        "symbol": item.symbol,
        "status": item.status,
        "metadata": {
            "cacheHit": item.cache_hit,
            "source": item.source,
        },
    }
    if item.quote is not None:
        payload["quote"] = _quote_payload(item.quote)
    if item.error_code is not None:
        payload["errorCode"] = item.error_code
    if item.error_message is not None:
        payload["errorMessage"] = item.error_message
    return payload


def _candle_payload(item: MarketCandle) -> dict:
    return {
        "timestamp": _dt(item.timestamp),
        "openPrice": item.open_price,
        "highPrice": item.high_price,
        "lowPrice": item.low_price,
        "closePrice": item.close_price,
        "volume": item.volume,
    }


def _parse_symbols(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def _parse_json(text: str) -> object:
    if not text:
        return None
    return json.loads(text)


def _runtime_error_payload(exc: ValueError) -> dict[str, Any]:
    message = str(exc)
    code = "INVALID_RUNTIME_CONFIG"

    prefix, _sep, _rest = message.partition(":")
    if prefix.startswith("ALPACA_"):
        code = prefix
    elif "provider must be one of" in message:
        code = "INVALID_PROVIDER"

    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _build_service_from_runtime_args(args: argparse.Namespace, *, env: dict[str, str] | None = None) -> MarketDataService:
    source_env = env if env is not None else os.environ
    provider_raw = str(getattr(args, "provider", "") or source_env.get("MARKET_DATA_PROVIDER") or "inmemory")
    provider = provider_raw.strip().lower()

    if provider == "inmemory":
        return MarketDataService(provider=_InMemoryProvider())

    if provider == "alpaca":
        config = resolve_alpaca_transport_config(
            api_key=getattr(args, "alpaca_api_key", None),
            api_secret=getattr(args, "alpaca_api_secret", None),
            base_url=getattr(args, "alpaca_base_url", None),
            timeout_seconds=getattr(args, "alpaca_timeout_seconds", None),
            env=source_env,
            env_prefixes=("MARKET_DATA_ALPACA", "BACKEND_ALPACA"),
        )
        transport = AlpacaHTTPTransport(config=config)
        return MarketDataService(provider=AlpacaProvider(transport=transport))

    raise ValueError("provider must be one of: inmemory, alpaca")


def _configure_runtime(args: argparse.Namespace) -> dict[str, Any] | None:
    global _service, _stream_gateway

    try:
        _service = _build_service_from_runtime_args(args)
        _stream_gateway = None
    except ValueError as exc:
        return _runtime_error_payload(exc)

    return None


def _cmd_search(args: argparse.Namespace) -> None:
    try:
        items = _service.search_assets(user_id=args.user_id, keyword=args.keyword, limit=args.limit)
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output(
        {
            "success": True,
            "data": {
                "items": [_asset_payload(item) for item in items],
                "query": args.keyword,
            },
        }
    )


def _cmd_catalog(args: argparse.Namespace) -> None:
    try:
        items = _service.list_catalog(
            user_id=args.user_id,
            limit=args.limit,
            market=getattr(args, "market", None),
            asset_class=getattr(args, "asset_class", None),
        )
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output(
        {
            "success": True,
            "data": {
                "items": [_asset_payload(item) for item in items],
                "total": len(items),
            },
        }
    )


def _cmd_catalog_detail(args: argparse.Namespace) -> None:
    try:
        asset = _service.get_catalog_asset_detail(
            user_id=args.user_id,
            symbol=args.symbol,
            market=getattr(args, "market", None),
            asset_class=getattr(args, "asset_class", None),
        )
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output({"success": True, "data": {"asset": _asset_payload(asset)}})


def _cmd_symbols(args: argparse.Namespace) -> None:
    try:
        items = _service.list_symbols(user_id=args.user_id, limit=args.limit)
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output({"success": True, "data": {"items": items, "total": len(items)}})


def _cmd_latest(args: argparse.Namespace) -> None:
    try:
        result = _service.get_latest_quote(user_id=args.user_id, symbol=args.symbol)
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output(
        {
            "success": True,
            "data": {
                "quote": _quote_payload(result.quote),
                "metadata": {
                    "cacheHit": result.cache_hit,
                    "source": result.source,
                },
            },
        }
    )


def _cmd_quote(args: argparse.Namespace) -> None:
    _cmd_latest(args)


def _cmd_quotes(args: argparse.Namespace) -> None:
    symbols = _parse_symbols(args.symbols)
    try:
        result = _service.get_quotes(user_id=args.user_id, symbols=symbols)
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output(
        {
            "success": True,
            "data": {
                "items": [_batch_item_payload(item) for item in result.items],
                "timestamp": result.timestamp,
            },
        }
    )


def _cmd_provider_health(args: argparse.Namespace) -> None:
    try:
        payload = _service.provider_health(user_id=args.user_id)
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output({"success": True, "data": payload})


def _cmd_history(args: argparse.Namespace) -> None:
    try:
        rows = _service.get_history(
            user_id=args.user_id,
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            timeframe=args.timeframe,
            limit=args.limit,
        )
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output(
        {
            "success": True,
            "data": {
                "symbol": args.symbol.upper(),
                "items": [_candle_payload(item) for item in rows],
            },
        }
    )


def _cmd_sync(args: argparse.Namespace) -> None:
    symbols = _parse_symbols(args.symbols)
    try:
        result = _service.sync_market_data(
            user_id=args.user_id,
            symbols=symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            timeframe=args.timeframe,
        )
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output({"success": True, "data": result})


def _cmd_indicators_calculate(args: argparse.Namespace) -> None:
    raw = _parse_json(args.indicators)
    indicators: list[dict[str, Any]] = []
    if isinstance(raw, list):
        indicators = [item for item in raw if isinstance(item, dict)]

    try:
        result = _service.calculate_indicators(
            user_id=args.user_id,
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            timeframe=args.timeframe,
            indicators=indicators,
        )
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable}})
        return

    _output({"success": True, "data": result})


def _cmd_boundary_check(args: argparse.Namespace) -> None:
    symbols = _parse_symbols(args.symbols)
    report = _service.boundary_check(user_id=args.user_id, symbols=symbols)
    _output({"success": True, "data": report})


def _cmd_stream_subscribe(args: argparse.Namespace) -> None:
    gateway = _get_stream_gateway()
    symbols = _parse_symbols(args.symbols)

    try:
        subscription = gateway.subscribe(
            user_id=args.user_id,
            symbols=symbols,
            channel=args.channel,
            timeframe=args.timeframe,
        )
    except StreamGatewayError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message}})
        return

    _output({"success": True, "data": subscription.to_payload()})



def _cmd_stream_unsubscribe(args: argparse.Namespace) -> None:
    gateway = _get_stream_gateway()
    removed = gateway.unsubscribe(user_id=args.user_id, subscription_id=args.subscription_id)
    _output({"success": True, "data": {"subscriptionId": args.subscription_id, "removed": removed}})



def _cmd_stream_poll(args: argparse.Namespace) -> None:
    gateway = _get_stream_gateway()

    try:
        events = gateway.poll_events(user_id=args.user_id, subscription_id=args.subscription_id)
    except StreamGatewayError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message}})
        return

    _output({"success": True, "data": {"subscriptionId": args.subscription_id, "items": events}})



def _cmd_stream_status(args: argparse.Namespace) -> None:
    gateway = _get_stream_gateway()
    _output(
        {
            "success": True,
            "data": {
                "stream": gateway.health(user_id=args.user_id),
                "subscriptions": [row.to_payload() for row in gateway.list_subscriptions(user_id=args.user_id)],
            },
        }
    )


def _add_runtime_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--provider", choices=["inmemory", "alpaca"], default=None)
    command.add_argument("--alpaca-api-key", default=None)
    command.add_argument("--alpaca-api-secret", default=None)
    command.add_argument("--alpaca-base-url", default=None)
    command.add_argument("--alpaca-timeout-seconds", type=float, default=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-data", description="QuantPoly 市场数据 CLI")
    sub = parser.add_subparsers(dest="command")

    search = sub.add_parser("search", help="查询股票")
    search.add_argument("--user-id", required=True)
    search.add_argument("--keyword", required=True)
    search.add_argument("--limit", type=int, default=10)
    _add_runtime_args(search)

    catalog = sub.add_parser("catalog", help="查询标的目录")
    catalog.add_argument("--user-id", required=True)
    catalog.add_argument("--limit", type=int, default=100)
    catalog.add_argument("--market", default=None)
    catalog.add_argument("--asset-class", default=None)
    _add_runtime_args(catalog)

    catalog_detail = sub.add_parser("catalog-detail", help="查询单个标的详情")
    catalog_detail.add_argument("--user-id", required=True)
    catalog_detail.add_argument("--symbol", required=True)
    catalog_detail.add_argument("--market", default=None)
    catalog_detail.add_argument("--asset-class", default=None)
    _add_runtime_args(catalog_detail)

    symbols = sub.add_parser("symbols", help="查询可用标的代码")
    symbols.add_argument("--user-id", required=True)
    symbols.add_argument("--limit", type=int, default=100)
    _add_runtime_args(symbols)

    quote = sub.add_parser("quote", help="查询实时行情")
    quote.add_argument("--user-id", required=True)
    quote.add_argument("--symbol", required=True)
    _add_runtime_args(quote)

    latest = sub.add_parser("latest", help="查询最新行情")
    latest.add_argument("--user-id", required=True)
    latest.add_argument("--symbol", required=True)
    _add_runtime_args(latest)

    quotes = sub.add_parser("quotes", help="批量查询实时行情")
    quotes.add_argument("--user-id", required=True)
    quotes.add_argument("--symbols", required=True, help="逗号分隔的 symbol 列表")
    _add_runtime_args(quotes)

    provider_health = sub.add_parser("provider-health", help="查询 provider 健康状态")
    provider_health.add_argument("--user-id", required=True)
    _add_runtime_args(provider_health)

    history = sub.add_parser("history", help="查询历史K线")
    history.add_argument("--user-id", required=True)
    history.add_argument("--symbol", required=True)
    history.add_argument("--start-date", required=True)
    history.add_argument("--end-date", required=True)
    history.add_argument("--timeframe", default="1Day")
    history.add_argument("--limit", type=int, default=None)
    _add_runtime_args(history)

    sync = sub.add_parser("sync", help="同步行情数据")
    sync.add_argument("--user-id", required=True)
    sync.add_argument("--symbols", required=True, help="逗号分隔的 symbol 列表")
    sync.add_argument("--start-date", required=True)
    sync.add_argument("--end-date", required=True)
    sync.add_argument("--timeframe", default="1Day")
    _add_runtime_args(sync)

    indicators = sub.add_parser("indicators", help="技术指标")
    indicators_sub = indicators.add_subparsers(dest="indicators_command")
    calculate = indicators_sub.add_parser("calculate", help="计算技术指标")
    calculate.add_argument("--user-id", required=True)
    calculate.add_argument("--symbol", required=True)
    calculate.add_argument("--start-date", required=True)
    calculate.add_argument("--end-date", required=True)
    calculate.add_argument("--timeframe", default="1Day")
    calculate.add_argument("--indicators", required=True, help='JSON: [{"name":"sma","period":3}]')
    _add_runtime_args(calculate)

    boundary = sub.add_parser("boundary", help="同步后边界一致性")
    boundary_sub = boundary.add_subparsers(dest="boundary_command")
    boundary_check = boundary_sub.add_parser("check", help="执行边界一致性校验")
    boundary_check.add_argument("--user-id", required=True)
    boundary_check.add_argument("--symbols", required=True, help="逗号分隔的 symbol 列表")
    _add_runtime_args(boundary_check)

    stream = sub.add_parser("stream", help="实时流网关订阅管理")
    stream_sub = stream.add_subparsers(dest="stream_command")

    stream_subscribe = stream_sub.add_parser("subscribe", help="创建订阅")
    stream_subscribe.add_argument("--user-id", required=True)
    stream_subscribe.add_argument("--symbols", required=True, help="逗号分隔的 symbol 列表")
    stream_subscribe.add_argument("--channel", default="quote")
    stream_subscribe.add_argument("--timeframe", default="1Min")
    _add_runtime_args(stream_subscribe)

    stream_unsubscribe = stream_sub.add_parser("unsubscribe", help="取消订阅")
    stream_unsubscribe.add_argument("--user-id", required=True)
    stream_unsubscribe.add_argument("--subscription-id", required=True)
    _add_runtime_args(stream_unsubscribe)

    stream_poll = stream_sub.add_parser("poll", help="拉取订阅事件")
    stream_poll.add_argument("--user-id", required=True)
    stream_poll.add_argument("--subscription-id", required=True)
    _add_runtime_args(stream_poll)

    stream_status = stream_sub.add_parser("status", help="查看流网关状态")
    stream_status.add_argument("--user-id", required=True)
    _add_runtime_args(stream_status)

    return parser


_COMMANDS = {
    "search": _cmd_search,
    "catalog": _cmd_catalog,
    "catalog-detail": _cmd_catalog_detail,
    "symbols": _cmd_symbols,
    "quote": _cmd_quote,
    "latest": _cmd_latest,
    "quotes": _cmd_quotes,
    "provider-health": _cmd_provider_health,
    "history": _cmd_history,
    "sync": _cmd_sync,
}


_NESTED_COMMANDS: dict[str, dict[str, Any]] = {
    "indicators": {
        "calculate": _cmd_indicators_calculate,
    },
    "boundary": {
        "check": _cmd_boundary_check,
    },
    "stream": {
        "subscribe": _cmd_stream_subscribe,
        "unsubscribe": _cmd_stream_unsubscribe,
        "poll": _cmd_stream_poll,
        "status": _cmd_stream_status,
    },
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    runtime_error = _configure_runtime(args)
    if runtime_error is not None:
        _output(runtime_error)
        return

    handler = _COMMANDS.get(args.command)
    if handler is None:
        nested = _NESTED_COMMANDS.get(args.command)
        if nested is None:
            parser.print_help()
            sys.exit(1)

        nested_key = None
        if args.command == "indicators":
            nested_key = getattr(args, "indicators_command", None)
        elif args.command == "boundary":
            nested_key = getattr(args, "boundary_command", None)
        elif args.command == "stream":
            nested_key = getattr(args, "stream_command", None)

        nested_handler = nested.get(str(nested_key or "")) if nested_key else None
        if nested_handler is None:
            parser.print_help()
            sys.exit(1)
        nested_handler(args)
        return

    handler(args)


if __name__ == "__main__":
    main()
