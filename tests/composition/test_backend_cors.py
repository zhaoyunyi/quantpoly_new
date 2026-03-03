from __future__ import annotations

from fastapi.testclient import TestClient

from apps.backend_app.app import create_app


def test_cors_is_disabled_by_default() -> None:
    origin = "http://localhost:3000"
    app = create_app(storage_backend="memory")
    client = TestClient(app)

    resp = client.get("/health", headers={"Origin": origin})

    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") is None


def test_cors_preflight_is_accepted_for_allowed_origin(monkeypatch) -> None:
    # 前端浏览器直连后端时会触发预检（OPTIONS）。未开启 CORS 会导致浏览器阻止请求。
    allowed_origin = "http://localhost:3000"
    monkeypatch.setenv("BACKEND_CORS_ALLOWED_ORIGINS", allowed_origin)

    app = create_app(storage_backend="memory")
    client = TestClient(app)

    resp = client.options(
        "/health",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert resp.status_code in {200, 204}
    assert resp.headers.get("access-control-allow-origin") == allowed_origin
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_cors_allows_cross_origin_health_with_cookie(monkeypatch) -> None:
    allowed_origin = "http://localhost:3000"
    monkeypatch.setenv("BACKEND_CORS_ALLOWED_ORIGINS", allowed_origin)

    app = create_app(storage_backend="memory")
    client = TestClient(app)
    client.cookies.set("session_token", "test-session-token")

    resp = client.get("/health", headers={"Origin": allowed_origin})

    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == allowed_origin
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_unauthorized_protected_endpoint_still_includes_cors_headers(monkeypatch) -> None:
    allowed_origin = "http://localhost:3000"
    monkeypatch.setenv("BACKEND_CORS_ALLOWED_ORIGINS", allowed_origin)

    app = create_app(storage_backend="memory")
    client = TestClient(app)

    resp = client.get("/users/me", headers={"Origin": allowed_origin})

    assert resp.status_code == 401
    assert resp.headers.get("access-control-allow-origin") == allowed_origin
    assert resp.headers.get("access-control-allow-credentials") == "true"
