"""market_data FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from market_data.domain import (
    BatchQuoteItem,
    MarketAsset,
    MarketCandle,
    MarketDataError,
    MarketQuote,
    RateLimitExceededError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from market_data.service import MarketDataService
from platform_core.response import error_response, success_response


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _asset_payload(item: MarketAsset) -> dict[str, Any]:
    return {
        "symbol": item.symbol,
        "name": item.name,
        "exchange": item.exchange,
        "currency": item.currency,
        "assetClass": item.asset_class,
        "tradable": item.tradable,
        "fractionable": item.fractionable,
    }


def _quote_payload(item: MarketQuote) -> dict[str, Any]:
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


def _batch_item_payload(item: BatchQuoteItem) -> dict[str, Any]:
    payload: dict[str, Any] = {
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


def _candle_payload(item: MarketCandle) -> dict[str, Any]:
    return {
        "timestamp": _dt(item.timestamp),
        "openPrice": item.open_price,
        "highPrice": item.high_price,
        "lowPrice": item.low_price,
        "closePrice": item.close_price,
        "volume": item.volume,
    }


def _error_to_response(error: MarketDataError) -> JSONResponse:
    if isinstance(error, RateLimitExceededError):
        status = 429
    elif isinstance(error, UpstreamTimeoutError):
        status = 504
    elif isinstance(error, UpstreamUnavailableError):
        status = 502
    else:
        status = 502

    payload = error_response(code=error.code, message=error.message)
    payload["error"]["retryable"] = error.retryable
    return JSONResponse(status_code=status, content=payload)


def create_router(*, service: MarketDataService, get_current_user: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/market/search")
    def search_assets(
        keyword: str = Query(..., min_length=1),
        limit: int = Query(10, ge=1, le=50),
        current_user=Depends(get_current_user),
    ):
        try:
            items = service.search_assets(user_id=current_user.id, keyword=keyword, limit=limit)
        except MarketDataError as exc:
            return _error_to_response(exc)
        return success_response(data={"items": [_asset_payload(item) for item in items], "query": keyword})

    @router.get("/market/catalog")
    def get_catalog(
        limit: int = Query(100, ge=1, le=200),
        current_user=Depends(get_current_user),
    ):
        try:
            items = service.list_catalog(user_id=current_user.id, limit=limit)
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(
            data={
                "items": [_asset_payload(item) for item in items],
                "total": len(items),
            }
        )

    @router.get("/market/symbols")
    def get_symbols(
        limit: int = Query(100, ge=1, le=200),
        current_user=Depends(get_current_user),
    ):
        try:
            items = service.list_symbols(user_id=current_user.id, limit=limit)
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(
            data={
                "items": items,
                "total": len(items),
            }
        )

    @router.get("/market/quote/{symbol}")
    def get_quote(symbol: str, current_user=Depends(get_current_user)):
        try:
            result = service.get_quote(user_id=current_user.id, symbol=symbol)
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(
            data={
                "quote": _quote_payload(result.quote),
                "metadata": {
                    "cacheHit": result.cache_hit,
                    "source": result.source,
                },
            }
        )

    @router.get("/market/latest/{symbol}")
    def get_latest(symbol: str, current_user=Depends(get_current_user)):
        try:
            result = service.get_latest_quote(user_id=current_user.id, symbol=symbol)
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(
            data={
                "quote": _quote_payload(result.quote),
                "metadata": {
                    "cacheHit": result.cache_hit,
                    "source": result.source,
                },
            }
        )

    @router.post("/market/quotes")
    def get_quotes(
        body: dict[str, Any] = Body(default_factory=dict),
        current_user=Depends(get_current_user),
    ):
        symbols = body.get("symbols") or body.get("stockCodes") or []
        if not isinstance(symbols, list):
            symbols = []

        try:
            result = service.get_quotes(user_id=current_user.id, symbols=[str(item) for item in symbols])
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(
            data={
                "items": [_batch_item_payload(item) for item in result.items],
                "timestamp": result.timestamp,
            }
        )

    @router.get("/market/provider-health")
    def get_provider_health(current_user=Depends(get_current_user)):
        try:
            payload = service.provider_health(user_id=current_user.id)
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(data=payload)

    @router.get("/market/history/{symbol}")
    def get_history(
        symbol: str,
        start_date: str = Query(..., alias="startDate"),
        end_date: str = Query(..., alias="endDate"),
        timeframe: str = Query("1Day"),
        limit: int | None = Query(None),
        current_user=Depends(get_current_user),
    ):
        try:
            rows = service.get_history(
                user_id=current_user.id,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                limit=limit,
            )
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(
            data={
                "items": [_candle_payload(item) for item in rows],
                "symbol": symbol.upper(),
            }
        )

    return router
