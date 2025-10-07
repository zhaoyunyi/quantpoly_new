"""FastAPI 异常信封安装器测试（TDD Red）。

覆盖的 BDD 场景（来自 change: refactor-api-error-envelope-unification）：
- HTTPException 映射为 error_response
- RequestValidationError 映射为 VALIDATION_ERROR
- 未知异常映射为 INTERNAL_ERROR
"""

from __future__ import annotations

from typing import Callable

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

import platform_core.fastapi


def _install() -> Callable[[FastAPI], None]:
    install_exception_handlers = getattr(platform_core.fastapi, "install_exception_handlers", None)
    assert callable(install_exception_handlers)
    return install_exception_handlers


def test_http_exception_is_wrapped_as_error_response():
    app = FastAPI()
    _install()(app)

    @app.get("/forbidden")
    def forbidden():
        raise HTTPException(
            status_code=403,
            detail={"code": "EMAIL_NOT_VERIFIED", "message": "email not verified"},
        )

    client = TestClient(app)
    resp = client.get("/forbidden")
    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_request_validation_error_is_wrapped_as_validation_error():
    class Payload(BaseModel):
        value: int

    app = FastAPI()
    _install()(app)

    @app.post("/payload")
    def create_payload(body: Payload):
        return {"success": True, "data": {"value": body.value}}

    client = TestClient(app)
    resp = client.post("/payload", json={})
    assert resp.status_code == 422
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_exception_is_wrapped_as_internal_error():
    app = FastAPI()
    _install()(app)

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 500
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INTERNAL_ERROR"
    assert payload["error"]["message"] == "internal server error"
