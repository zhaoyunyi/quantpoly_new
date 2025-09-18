"""user-preferences sqlite 持久化适配器 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from user_preferences.store_sqlite import SQLitePreferencesStore


def _build_app(*, db_path: str, user_level: int):
    from user_preferences.api import create_router

    class _User:
        def __init__(self):
            self.id = "u-1"
            self.level = user_level

    def get_current_user():
        return _User()

    app = FastAPI()
    app.include_router(
        create_router(
            store=SQLitePreferencesStore(db_path=db_path),
            get_current_user=get_current_user,
        )
    )
    return app


def test_api_should_keep_preferences_after_restart_with_sqlite_store(tmp_path):
    db_path = str(tmp_path / "prefs.sqlite3")

    app = _build_app(db_path=db_path, user_level=2)
    client = TestClient(app)

    patch_resp = client.patch(
        "/users/me/preferences",
        json={"theme": {"darkMode": True}},
    )
    assert patch_resp.status_code == 200

    restarted_app = _build_app(db_path=db_path, user_level=2)
    restarted_client = TestClient(restarted_app)
    get_resp = restarted_client.get("/users/me/preferences")

    assert get_resp.status_code == 200
    data = get_resp.json()["data"]
    assert data["theme"]["darkMode"] is True
    assert data["version"] >= 1


def test_api_should_keep_advanced_permission_with_sqlite_store(tmp_path):
    db_path = str(tmp_path / "prefs.sqlite3")

    app = _build_app(db_path=db_path, user_level=1)
    client = TestClient(app)

    resp = client.patch("/users/me/preferences", json={"advanced": {"betaFeatures": True}})

    assert resp.status_code == 403
