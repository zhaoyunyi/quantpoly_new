"""user-preferences API 路由测试。

覆盖的 BDD 场景（来自 change: move-user-preferences-to-backend）：
- 新用户首次读取偏好得到默认值，并持久化
- 深度合并更新不丢失字段
- 非法字段被拒绝
- reset/export/import
- low-level 用户看不到 advanced、不能写 advanced
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, user_level: int):
    from user_preferences.api import create_router
    from user_preferences.store import InMemoryPreferencesStore

    class _User:
        def __init__(self):
            self.id = "u-1"
            self.level = user_level

    def get_current_user():
        return _User()

    store = InMemoryPreferencesStore()
    app = FastAPI()
    app.include_router(create_router(store=store, get_current_user=get_current_user))
    return app, store


def test_get_returns_default_and_persists():
    app, store = _build_app(user_level=1)
    client = TestClient(app)

    resp = client.get("/users/me/preferences")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["version"] >= 1
    assert "advanced" not in data

    persisted = store.get("u-1")
    assert persisted is not None


def test_patch_deep_merge_keeps_other_fields():
    app, _ = _build_app(user_level=1)
    client = TestClient(app)

    base = client.get("/users/me/preferences").json()["data"]
    resp = client.patch(
        "/users/me/preferences",
        json={"theme": {"primaryColor": "#FF0000"}},
    )
    assert resp.status_code == 200
    patched = resp.json()["data"]
    assert patched["theme"]["primaryColor"] == "#FF0000"
    assert patched["theme"]["darkMode"] == base["theme"]["darkMode"]


def test_patch_unknown_field_rejected():
    app, _ = _build_app(user_level=1)
    client = TestClient(app)

    resp = client.patch("/users/me/preferences", json={"notSupported": True})
    assert resp.status_code in (400, 422)


def test_level_1_cannot_patch_advanced():
    app, _ = _build_app(user_level=1)
    client = TestClient(app)

    resp = client.patch("/users/me/preferences", json={"advanced": {"betaFeatures": True}})
    assert resp.status_code == 403


def test_level_2_can_patch_advanced():
    app, _ = _build_app(user_level=2)
    client = TestClient(app)

    resp = client.patch("/users/me/preferences", json={"advanced": {"betaFeatures": True}})
    assert resp.status_code == 200
    assert resp.json()["data"]["advanced"]["betaFeatures"] is True


def test_reset_export_import_roundtrip():
    app, _ = _build_app(user_level=2)
    client = TestClient(app)

    client.patch("/users/me/preferences", json={"theme": {"darkMode": True}})

    exported = client.get("/users/me/preferences/export").json()["data"]
    assert exported["theme"]["darkMode"] is True

    reset = client.post("/users/me/preferences/reset").json()["data"]
    assert reset["theme"]["darkMode"] is False

    imported = client.post("/users/me/preferences/import", json=exported).json()["data"]
    assert imported["theme"]["darkMode"] is True


def test_import_old_version_is_migrated():
    app, _ = _build_app(user_level=2)
    client = TestClient(app)

    old = {"version": 0, "theme": {"primaryColor": "#000000", "darkMode": False}}
    resp = client.post("/users/me/preferences/import", json=old)
    assert resp.status_code == 200
    assert resp.json()["data"]["version"] >= 1
