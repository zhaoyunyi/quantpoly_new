"""backend composition root 测试。"""

from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from apps.backend_app.app import create_app


def _register_and_login(client: TestClient) -> str:
    email = "composition@example.com"
    password = "StrongPass123!"

    register = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert register.status_code == 200

    verify = client.post("/auth/verify-email", json={"email": email})
    assert verify.status_code == 200

    login = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return login.json()["data"]["token"]


def test_composition_root_registers_rest_and_ws_contexts():
    app = create_app()

    paths = {route.path for route in app.routes}

    assert "/auth/login" in paths
    assert "/strategies" in paths
    assert "/backtests" in paths
    assert "/trading/accounts" in paths
    assert "/market/search" in paths
    assert "/risk/rules" in paths
    assert "/signals" in paths
    assert "/users/me/preferences" in paths
    assert "/monitor/summary" in paths
    assert "/ws/monitor" in paths


def test_composition_root_module_switch_disables_selected_contexts():
    app = create_app(enabled_contexts={"user-auth", "strategy-management"})

    paths = {route.path for route in app.routes}

    assert "/auth/login" in paths
    assert "/strategies" in paths
    assert "/market/search" not in paths
    assert "/risk/rules" not in paths
    assert "/ws/monitor" not in paths


def test_single_current_user_dependency_and_error_envelope_are_consistent():
    app = create_app()
    client = TestClient(app)

    unauthorized_strategy = client.get("/strategies")
    unauthorized_backtests = client.get("/backtests")

    assert unauthorized_strategy.status_code == 401
    assert unauthorized_backtests.status_code == 401
    assert unauthorized_strategy.json()["success"] is False
    assert unauthorized_backtests.json()["success"] is False
    assert unauthorized_strategy.json()["error"]["code"] == "UNAUTHORIZED"
    assert unauthorized_backtests.json()["error"]["code"] == "UNAUTHORIZED"

    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    strategies = client.get("/strategies", headers=headers)
    backtests = client.get("/backtests", headers=headers)

    assert strategies.status_code == 200
    assert backtests.status_code == 200
    assert strategies.json()["success"] is True
    assert backtests.json()["success"] is True


def test_composition_auth_log_masks_sensitive_values(caplog):
    app = create_app()
    client = TestClient(app)

    raw_header_token = "super-secret-header-token-123456"
    raw_cookie_token = "another-secret-cookie-token-987654"
    client.cookies.set("session_token", raw_cookie_token)

    with caplog.at_level(logging.WARNING, logger="backend_app.auth"):
        response = client.get(
            "/strategies",
            headers={"Authorization": f"Bearer {raw_header_token}"},
        )

    assert response.status_code == 401
    assert raw_header_token not in caplog.text
    assert raw_cookie_token not in caplog.text
    assert "supe***" in caplog.text


def test_monitoring_ws_is_available_from_composition_root():
    app = create_app()
    client = TestClient(app)
    token = _register_and_login(client)

    with client.websocket_connect("/ws/monitor", headers={"Authorization": f"Bearer {token}"}) as ws:
        heartbeat = ws.receive_json()
        assert heartbeat["type"] == "monitor.heartbeat"
        assert isinstance(heartbeat["timestamp"], int)


def test_composition_metrics_endpoint_collects_http_totals():
    app = create_app(enabled_contexts={"user-auth", "strategy-management"})
    client = TestClient(app)

    client.get("/health")
    client.get("/strategies")

    metrics = client.get("/internal/metrics")

    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload["success"] is True
    assert payload["data"]["httpRequestsTotal"] >= 2
    assert payload["data"]["httpErrorsTotal"] >= 1
