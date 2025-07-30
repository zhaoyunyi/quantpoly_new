"""market_data CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from market_data.alpaca_provider import AlpacaProvider
from market_data.domain import MarketAsset, MarketCandle, MarketDataError, MarketQuote
from market_data.service import MarketDataService


def _default_transport(_operation: str, **_kwargs):
    raise RuntimeError("provider not configured")


_provider = AlpacaProvider(transport=_default_transport)
_service = MarketDataService(provider=_provider)


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


def _candle_payload(item: MarketCandle) -> dict:
    return {
        "timestamp": _dt(item.timestamp),
        "openPrice": item.open_price,
        "highPrice": item.high_price,
        "lowPrice": item.low_price,
        "closePrice": item.close_price,
        "volume": item.volume,
    }


def _cmd_search(args: argparse.Namespace) -> None:
    try:
        items = _service.search_assets(user_id=args.user_id, keyword=args.keyword, limit=args.limit)
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message}})
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


def _cmd_quote(args: argparse.Namespace) -> None:
    try:
        result = _service.get_quote(user_id=args.user_id, symbol=args.symbol)
    except MarketDataError as exc:
        _output({"success": False, "error": {"code": exc.code, "message": exc.message}})
        return

    _output(
        {
            "success": True,
            "data": {
                "quote": _quote_payload(result.quote),
                "metadata": {"cacheHit": result.cache_hit},
            },
        }
    )


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
        _output({"success": False, "error": {"code": exc.code, "message": exc.message}})
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-data", description="QuantPoly 市场数据 CLI")
    sub = parser.add_subparsers(dest="command")

    search = sub.add_parser("search", help="查询股票")
    search.add_argument("--user-id", required=True)
    search.add_argument("--keyword", required=True)
    search.add_argument("--limit", type=int, default=10)

    quote = sub.add_parser("quote", help="查询实时行情")
    quote.add_argument("--user-id", required=True)
    quote.add_argument("--symbol", required=True)

    history = sub.add_parser("history", help="查询历史K线")
    history.add_argument("--user-id", required=True)
    history.add_argument("--symbol", required=True)
    history.add_argument("--start-date", required=True)
    history.add_argument("--end-date", required=True)
    history.add_argument("--timeframe", default="1Day")
    history.add_argument("--limit", type=int, default=None)

    return parser


_COMMANDS = {
    "search": _cmd_search,
    "quote": _cmd_quote,
    "history": _cmd_history,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
