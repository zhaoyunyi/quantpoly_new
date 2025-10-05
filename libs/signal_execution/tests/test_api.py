"""signal_execution API 路由测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(
    *,
    current_user_id: str,
    is_admin: bool | None = False,
    role: str | None = None,
    level: int | None = None,
):
    from signal_execution.api import create_router
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    class _User:
        def __init__(
            self,
            user_id: str,
            admin: bool | None,
            user_role: str | None,
            user_level: int | None,
        ):
            self.id = user_id
            if admin is not None:
                self.is_admin = admin
            if user_role is not None:
                self.role = user_role
            if user_level is not None:
                self.level = user_level

    def _get_current_user():
        return _User(current_user_id, is_admin, role, level)

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return app, service


def test_execute_foreign_signal_returns_403_and_keeps_status():
    app, service = _build_app(current_user_id="u-1")

    foreign = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy",
        account_id="u-2-account",
        symbol="AAPL",
        side="BUY",
    )

    client = TestClient(app)
    resp = client.post(f"/signals/{foreign.id}/execute")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_ACCESS_DENIED"

    after = service.get_signal(user_id="u-2", signal_id=foreign.id)
    assert after is not None
    assert after.status == "pending"


def test_cleanup_all_requires_admin():
    app, service = _build_app(current_user_id="u-1", is_admin=False)

    service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )

    client = TestClient(app)
    resp = client.post("/signals/maintenance/cleanup-all")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"


def test_execution_trend_is_user_scoped():
    app, service = _build_app(current_user_id="u-1", is_admin=False)

    s1 = service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )
    service.execute_signal(user_id="u-1", signal_id=s1.id)

    s2 = service.create_signal(
        user_id="u-2",
        strategy_id="u-2-strategy",
        account_id="u-2-account",
        symbol="MSFT",
        side="BUY",
    )
    service.execute_signal(user_id="u-2", signal_id=s2.id)

    client = TestClient(app)
    resp = client.get("/signals/executions/trend")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 1


def test_cleanup_all_accepts_role_admin_without_is_admin_flag():
    app, service = _build_app(current_user_id="admin-1", is_admin=None, role="admin")

    service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )

    client = TestClient(app)
    resp = client.post("/signals/maintenance/cleanup-all")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["deleted"] >= 1


def test_cleanup_all_rejects_legacy_is_admin_without_role():
    app, service = _build_app(current_user_id="admin-legacy", is_admin=True, role=None)

    service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )

    client = TestClient(app)
    resp = client.post("/signals/maintenance/cleanup-all")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"


def test_cleanup_all_rejects_role_user_without_is_admin_flag():
    app, service = _build_app(current_user_id="u-1", is_admin=None, role="user")

    service.create_signal(
        user_id="u-1",
        strategy_id="u-1-strategy",
        account_id="u-1-account",
        symbol="AAPL",
        side="BUY",
    )

    client = TestClient(app)
    resp = client.post("/signals/maintenance/cleanup-all")

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ADMIN_REQUIRED"
