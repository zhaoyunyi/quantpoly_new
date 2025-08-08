"""后端统一组合入口（Composition Root）。"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apps.backend_app.router_registry import (
    MetricsCollector,
    build_context,
    build_current_user_dependency,
    ensure_demo_account,
    permission_error_to_response,
    register_all_routes,
)
from apps.backend_app.settings import CompositionSettings, normalize_enabled_contexts
from platform_core.logging import mask_sensitive
from platform_core.response import error_response
from user_auth.app import create_app as create_user_auth_app


def _http_error_code(status_code: int) -> str:
    if status_code == 401:
        return "UNAUTHORIZED"
    if status_code == 403:
        return "FORBIDDEN"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 409:
        return "CONFLICT"
    if status_code == 422:
        return "VALIDATION_ERROR"
    if status_code >= 500:
        return "INTERNAL_ERROR"
    return "HTTP_ERROR"


def create_app(*, enabled_contexts: set[str] | None = None) -> FastAPI:
    settings = CompositionSettings(enabled_contexts=normalize_enabled_contexts(enabled_contexts))
    context = build_context()

    app = create_user_auth_app(user_repo=context.user_repo, session_store=context.session_store)
    app.title = "quantpoly-backend-app"

    metrics = MetricsCollector()

    @app.middleware("http")
    async def _access_log_and_metrics(request: Request, call_next):
        logger = logging.getLogger("backend_app.access")
        body = await request.body()

        async def receive():
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        replay_request = Request(request.scope, receive)
        response = await call_next(replay_request)
        metrics.record(status_code=response.status_code)

        logger.info(
            "access method=%s path=%s status=%s context=%s",
            request.method,
            request.url.path,
            response.status_code,
            mask_sensitive(
                str(
                    {
                        "headers": dict(request.headers),
                        "cookies": dict(request.cookies),
                        "body": body.decode("utf-8", errors="ignore")[:500],
                    }
                )
            ),
        )
        return response

    @app.exception_handler(PermissionError)
    async def _permission_error_handler(_request: Request, _exc: PermissionError):
        return permission_error_to_response()

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(_request: Request, exc: HTTPException):
        detail: Any = exc.detail
        if isinstance(detail, dict):
            code = str(detail.get("code") or _http_error_code(exc.status_code))
            message = str(detail.get("message") or detail)
        else:
            code = _http_error_code(exc.status_code)
            message = str(detail)

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code=code, message=message),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_response(code="VALIDATION_ERROR", message=str(exc)),
        )

    @app.exception_handler(Exception)
    async def _unknown_exception_handler(_request: Request, exc: Exception):
        logging.getLogger("backend_app.error").exception("unhandled_exception=%s", exc)
        return JSONResponse(
            status_code=500,
            content=error_response(code="INTERNAL_ERROR", message="internal server error"),
        )

    get_current_user = build_current_user_dependency(context=context)

    register_all_routes(
        app=app,
        context=context,
        enabled_contexts=settings.enabled_contexts,
        get_current_user=get_current_user,
    )

    @app.get("/internal/metrics")
    def get_metrics():
        return {
            "success": True,
            "data": metrics.snapshot(),
        }

    @app.get("/health")
    def health():
        return {
            "success": True,
            "data": {
                "status": "ok",
                "enabledContexts": sorted(settings.enabled_contexts),
            },
        }

    @app.post("/internal/bootstrap-demo")
    def bootstrap_demo(current_user=Depends(get_current_user)):
        ensure_demo_account(context=context, user_id=current_user.id)
        return {"success": True, "message": "bootstrap complete"}

    return app
