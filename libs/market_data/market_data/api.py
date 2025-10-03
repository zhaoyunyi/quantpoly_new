"""market_data FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.requests import Request

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
from market_data.service import MarketDataService
from market_data.stream_gateway import MarketDataStreamGateway, StreamGatewayError
from platform_core.response import error_response, success_response

from job_orchestration.service import (
    IdempotencyConflictError as JobIdempotencyConflictError,
    JobExecutionFailure,
    JobOrchestrationService,
)
from pydantic import BaseModel, Field


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
        "status": "active" if item.tradable else "inactive",
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
    if error.code == "ASSET_NOT_FOUND":
        status = 404
    elif isinstance(error, RateLimitExceededError):
        status = 429
    elif isinstance(error, UpstreamTimeoutError):
        status = 504
    elif isinstance(error, UpstreamRateLimitedError):
        status = 429
    elif isinstance(error, UpstreamUnauthorizedError):
        status = 502
    elif isinstance(error, UpstreamUnavailableError):
        status = 502
    else:
        status = 502

    payload = error_response(code=error.code, message=error.message)
    payload["error"]["retryable"] = error.retryable
    return JSONResponse(status_code=status, content=payload)


class SyncTaskRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    timeframe: str = Field(default="1Day")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class IndicatorSpec(BaseModel):
    name: str
    period: int | None = None
    fast: int | None = None
    slow: int | None = None
    signal: int | None = None
    std_dev: float | None = Field(default=None, alias="stdDev")

    model_config = {"populate_by_name": True}


class IndicatorsTaskRequest(BaseModel):
    symbol: str
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    timeframe: str = Field(default="1Day")
    indicators: list[IndicatorSpec] = Field(default_factory=list)
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class BoundaryCheckRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)


def _job_payload(job) -> dict[str, Any]:
    return {
        "taskId": job.id,
        "taskType": job.task_type,
        "status": job.status,
        "result": job.result,
        "error": {"code": job.error_code, "message": job.error_message}
        if job.error_code or job.error_message
        else None,
    }


def create_router(
    *,
    service: MarketDataService,
    get_current_user: Any,
    job_service: JobOrchestrationService | None = None,
) -> APIRouter:
    router = APIRouter()
    stream_gateway = MarketDataStreamGateway(
        quote_reader=lambda user_id, symbols: service.get_quotes(user_id=user_id, symbols=symbols),
    )

    def _stream_now() -> str:
        return f"{datetime.utcnow().isoformat()}Z"

    def _stream_error_event(*, code: str, message: str) -> dict[str, Any]:
        return {
            "type": "stream.error",
            "code": code,
            "message": message,
            "timestamp": _stream_now(),
        }

    def _resolve_ws_current_user(*, websocket: WebSocket):
        try:
            return get_current_user()
        except TypeError:
            pass

        request = Request(websocket.scope)
        try:
            return get_current_user(request)
        except TypeError:
            return get_current_user(websocket)

    @router.websocket("/market/stream")
    async def stream_gateway_socket(websocket: WebSocket):
        try:
            current_user = _resolve_ws_current_user(websocket=websocket)
        except PermissionError:
            await websocket.accept()
            await websocket.send_json(
                _stream_error_event(
                    code="STREAM_AUTH_REQUIRED",
                    message="stream auth required",
                )
            )
            await websocket.close(code=4401)
            return

        try:
            connection_id = stream_gateway.open_connection(user_id=current_user.id)
        except StreamGatewayError as exc:
            await websocket.accept()
            await websocket.send_json(_stream_error_event(code=exc.code, message=exc.message))
            await websocket.close(code=4408)
            return

        await websocket.accept()
        await websocket.send_json(
            {
                "type": "stream.ready",
                "timestamp": _stream_now(),
                "payload": {
                    "status": stream_gateway.health(user_id=current_user.id)["status"],
                },
            }
        )

        try:
            while True:
                message = await websocket.receive_json()
                action = str(message.get("action") or "").strip().lower()

                if action == "subscribe":
                    try:
                        symbols = [str(item) for item in list(message.get("symbols") or [])]
                        channel = str(message.get("channel") or "quote")
                        timeframe = str(message.get("timeframe") or "1Min")
                        subscription = stream_gateway.subscribe(
                            user_id=current_user.id,
                            symbols=symbols,
                            channel=channel,
                            timeframe=timeframe,
                        )
                    except StreamGatewayError as exc:
                        await websocket.send_json(_stream_error_event(code=exc.code, message=exc.message))
                        continue

                    await websocket.send_json(
                        {
                            "type": "stream.subscribed",
                            "subscriptionId": subscription.id,
                            "symbols": list(subscription.symbols),
                            "channel": subscription.channel,
                            "timeframe": subscription.timeframe,
                            "timestamp": _stream_now(),
                        }
                    )

                    events = stream_gateway.poll_events(
                        user_id=current_user.id,
                        subscription_id=subscription.id,
                    )
                    for event in events:
                        await websocket.send_json(event)
                    continue

                if action == "unsubscribe":
                    subscription_id = str(message.get("subscriptionId") or "")
                    removed = stream_gateway.unsubscribe(
                        user_id=current_user.id,
                        subscription_id=subscription_id,
                    )
                    if not removed:
                        await websocket.send_json(
                            _stream_error_event(
                                code="STREAM_SUBSCRIPTION_NOT_FOUND",
                                message="subscription not found",
                            )
                        )
                        continue

                    await websocket.send_json(
                        {
                            "type": "stream.unsubscribed",
                            "subscriptionId": subscription_id,
                            "timestamp": _stream_now(),
                        }
                    )
                    continue

                if action == "status":
                    await websocket.send_json(
                        {
                            "type": "stream.status",
                            "timestamp": _stream_now(),
                            "payload": {
                                "stream": stream_gateway.health(user_id=current_user.id),
                                "subscriptions": [
                                    row.to_payload()
                                    for row in stream_gateway.list_subscriptions(user_id=current_user.id)
                                ],
                            },
                        }
                    )
                    continue

                await websocket.send_json(
                    _stream_error_event(
                        code="STREAM_INVALID_SUBSCRIPTION",
                        message="invalid stream action",
                    )
                )
        except WebSocketDisconnect:
            pass
        finally:
            stream_gateway.clear_subscriptions(user_id=current_user.id)
            stream_gateway.close_connection(user_id=current_user.id, connection_id=connection_id)

    @router.get("/market/stream/status")
    def stream_status(current_user=Depends(get_current_user)):
        return success_response(
            data={
                "stream": stream_gateway.health(user_id=current_user.id),
                "provider": service.provider_health(user_id=current_user.id),
                "subscriptions": [
                    row.to_payload() for row in stream_gateway.list_subscriptions(user_id=current_user.id)
                ],
            }
        )

    @router.post("/market/sync-task")
    def submit_sync_task(body: SyncTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or f"market-data-sync:{','.join(body.symbols)}:{body.start_date}:{body.end_date}:{body.timeframe}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="market_data_sync",
                payload={
                    "symbols": body.symbols,
                    "startDate": body.start_date,
                    "endDate": body.end_date,
                    "timeframe": body.timeframe,
                },
                idempotency_key=job_idempotency_key,
            )

            def _sync_runner(payload: dict[str, Any]) -> dict[str, Any]:
                result = service.sync_market_data(
                    user_id=current_user.id,
                    symbols=list(payload.get("symbols") or []),
                    start_date=str(payload.get("startDate") or ""),
                    end_date=str(payload.get("endDate") or ""),
                    timeframe=str(payload.get("timeframe") or "1Day"),
                )
                service.record_sync_result(user_id=current_user.id, task_id=job.id, result=result)
                if int(result.get("summary", {}).get("failureCount", 0)) > 0:
                    raise JobExecutionFailure(
                        error_code="MARKET_DATA_SYNC_FAILED",
                        error_message="market data sync completed with failures",
                        result=result,
                    )
                return result

            job = job_service.dispatch_job_with_callable(
                user_id=current_user.id,
                job_id=job.id,
                runner=_sync_runner,
            )
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.get("/market/sync-task/{task_id}")
    def sync_task_status(task_id: str, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job = job_service.get_job(user_id=current_user.id, job_id=task_id)
        if job is None:
            return JSONResponse(status_code=404, content=error_response(code="TASK_NOT_FOUND", message="task not found"))

        result = job.result
        if result is None:
            stored = service.get_sync_result(user_id=current_user.id, task_id=task_id)
            if stored is not None:
                result = stored
                job.result = stored

        return success_response(data=_job_payload(job))

    @router.post("/market/sync-task/{task_id}/retry")
    def retry_sync_task(task_id: str, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job = job_service.get_job(user_id=current_user.id, job_id=task_id)
        if job is None:
            return JSONResponse(status_code=404, content=error_response(code="TASK_NOT_FOUND", message="task not found"))

        try:
            job_service.retry_job(user_id=current_user.id, job_id=task_id)

            def _retry_runner(payload: dict[str, Any]) -> dict[str, Any]:
                result = service.sync_market_data(
                    user_id=current_user.id,
                    symbols=list(payload.get("symbols") or []),
                    start_date=str(payload.get("startDate") or ""),
                    end_date=str(payload.get("endDate") or ""),
                    timeframe=str(payload.get("timeframe") or "1Day"),
                )
                service.record_sync_result(user_id=current_user.id, task_id=task_id, result=result)
                if int(result.get("summary", {}).get("failureCount", 0)) > 0:
                    raise JobExecutionFailure(
                        error_code="MARKET_DATA_SYNC_FAILED",
                        error_message="market data sync completed with failures",
                        result=result,
                    )
                return result

            job = job_service.dispatch_job_with_callable(
                user_id=current_user.id,
                job_id=task_id,
                runner=_retry_runner,
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.post("/market/indicators/calculate-task")
    def submit_indicators_task(body: IndicatorsTaskRequest, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        job_idempotency_key = body.idempotency_key or f"market-indicators:{body.symbol}:{body.start_date}:{body.end_date}:{body.timeframe}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="market_indicators_calculate",
                payload={
                    "symbol": body.symbol,
                    "startDate": body.start_date,
                    "endDate": body.end_date,
                    "timeframe": body.timeframe,
                    "indicators": [spec.model_dump(by_alias=True, exclude_none=True) for spec in body.indicators],
                },
                idempotency_key=job_idempotency_key,
            )

            def _indicators_runner(payload: dict[str, Any]) -> dict[str, Any]:
                return service.calculate_indicators(
                    user_id=current_user.id,
                    symbol=str(payload.get("symbol") or ""),
                    start_date=str(payload.get("startDate") or ""),
                    end_date=str(payload.get("endDate") or ""),
                    timeframe=str(payload.get("timeframe") or "1Day"),
                    indicators=list(payload.get("indicators") or []),
                )

            job = job_service.dispatch_job_with_callable(
                user_id=current_user.id,
                job_id=job.id,
                runner=_indicators_runner,
            )
        except JobIdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(data=_job_payload(job))

    @router.get("/market/indicators/calculate-task/{task_id}")
    def indicators_task_status(task_id: str, current_user=Depends(get_current_user)):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )
        job = job_service.get_job(user_id=current_user.id, job_id=task_id)
        if job is None:
            return JSONResponse(status_code=404, content=error_response(code="TASK_NOT_FOUND", message="task not found"))
        return success_response(data=_job_payload(job))

    @router.post("/market/boundary/check")
    def boundary_check(body: BoundaryCheckRequest, current_user=Depends(get_current_user)):
        report = service.boundary_check(user_id=current_user.id, symbols=body.symbols)
        return success_response(data=report)

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
        market: str | None = Query(default=None),
        asset_class: str | None = Query(default=None, alias="assetClass"),
        current_user=Depends(get_current_user),
    ):
        try:
            items = service.list_catalog(
                user_id=current_user.id,
                limit=limit,
                market=market,
                asset_class=asset_class,
            )
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(
            data={
                "items": [_asset_payload(item) for item in items],
                "total": len(items),
            }
        )

    @router.get("/market/catalog/{symbol}")
    def get_catalog_asset_detail(
        symbol: str,
        market: str | None = Query(default=None),
        asset_class: str | None = Query(default=None, alias="assetClass"),
        current_user=Depends(get_current_user),
    ):
        try:
            asset = service.get_catalog_asset_detail(
                user_id=current_user.id,
                symbol=symbol,
                market=market,
                asset_class=asset_class,
            )
        except MarketDataError as exc:
            return _error_to_response(exc)

        return success_response(data={"asset": _asset_payload(asset)})

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
