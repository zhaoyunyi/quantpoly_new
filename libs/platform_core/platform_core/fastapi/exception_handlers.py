"""FastAPI 异常处理安装器。

目标：为 standalone app / 组合入口 / 测试 harness 提供一致的错误 envelope。
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from platform_core.response import error_response


def install_exception_handlers(app: FastAPI) -> None:
    """为 FastAPI app 安装统一异常处理。

    处理范围：
    - HTTPException → error_response
    - RequestValidationError → VALIDATION_ERROR
    - 未知异常 → INTERNAL_ERROR
    """

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(_request: Request, exc: HTTPException):
        detail: Any = exc.detail
        if isinstance(detail, Mapping):
            code = str(detail.get("code") or "HTTP_ERROR")
            message = str(detail.get("message") or detail)
        else:
            code = "HTTP_ERROR"
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
        logging.getLogger("platform_core.fastapi").exception("unhandled_exception=%s", exc)
        return JSONResponse(
            status_code=500,
            content=error_response(code="INTERNAL_ERROR", message="internal server error"),
        )

