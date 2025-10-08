"""后端统一组合入口（Composition Root）。"""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, Request

from apps.backend_app.router_registry import (
    MetricsCollector,
    build_context,
    build_current_user_dependency,
    ensure_demo_account,
    permission_error_to_response,
    register_all_routes,
)
from apps.backend_app.settings import (
    CompositionSettings,
    normalize_enabled_contexts,
    normalize_job_executor_mode,
    normalize_market_data_provider,
    normalize_storage_backend,
)
from platform_core.logging import mask_sensitive
from platform_core.response import error_response
from platform_core.fastapi import install_exception_handlers
from platform_core.response import success_response
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


def create_app(
    *,
    enabled_contexts: set[str] | None = None,
    storage_backend: str | None = None,
    sqlite_db_path: str | None = None,
    market_data_provider: str | None = None,
    job_executor_mode: str | None = None,
) -> FastAPI:
    env_settings = CompositionSettings.from_env()
    settings = CompositionSettings(
        enabled_contexts=normalize_enabled_contexts(enabled_contexts),
        storage_backend=normalize_storage_backend(storage_backend or env_settings.storage_backend),
        sqlite_db_path=sqlite_db_path or env_settings.sqlite_db_path,
        market_data_provider=normalize_market_data_provider(market_data_provider or env_settings.market_data_provider),
        job_executor_mode=normalize_job_executor_mode(job_executor_mode or env_settings.job_executor_mode),
    )
    context = build_context(
        storage_backend=settings.storage_backend,
        sqlite_db_path=settings.sqlite_db_path,
        market_data_provider=settings.market_data_provider,
    )

    app = create_user_auth_app(user_repo=context.user_repo, session_store=context.session_store)
    app.title = "quantpoly-backend-app"

    install_exception_handlers(app)

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

    # install_exception_handlers 已覆盖 HTTPException/ValidationError/Exception
    # backend_app 仅保留 PermissionError 的映射，确保缺少 token 等场景返回稳定错误。

    get_current_user = build_current_user_dependency(context=context)

    register_all_routes(
        app=app,
        context=context,
        enabled_contexts=settings.enabled_contexts,
        get_current_user=get_current_user,
        job_executor_mode=settings.job_executor_mode,
    )

    @app.get("/internal/metrics")
    def get_metrics():
        return success_response(data=metrics.snapshot())

    @app.get("/health")
    def health():
        return success_response(
            data={
                "status": "ok",
                "enabledContexts": sorted(settings.enabled_contexts),
            }
        )

    @app.post("/internal/bootstrap-demo")
    def bootstrap_demo(current_user=Depends(get_current_user)):
        ensure_demo_account(context=context, user_id=current_user.id)
        return success_response(message="bootstrap complete")

    return app
