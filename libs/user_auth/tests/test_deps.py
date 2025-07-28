"""单一鉴权依赖测试。"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from user_auth.deps import build_get_current_user
from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore


def _build_auth_app(*, repo: UserRepository, sessions: SessionStore):
    app = FastAPI()
    get_current_user = build_get_current_user(user_repo=repo, session_store=sessions)

    @app.get("/me")
    def me(current_user=Depends(get_current_user)):
        return {"email": current_user.email}

    return app


def test_get_current_user_supports_configurable_token_extractor():
    repo = UserRepository()
    sessions = SessionStore()

    user = User.register(email="dep@example.com", password="StrongPass123!")
    repo.save(user)
    session = Session.create(user_id=user.id)
    sessions.save(session)

    app = FastAPI()

    def custom_token_extractor(*, headers, cookies):
        return cookies.get("alt_session_token")

    get_current_user = build_get_current_user(
        user_repo=repo,
        session_store=sessions,
        token_extractor=custom_token_extractor,
    )

    @app.get("/me")
    def me(current_user=Depends(get_current_user)):
        return {"email": current_user.email}

    client = TestClient(app)
    client.cookies.set("alt_session_token", session.token)
    resp = client.get("/me")

    assert resp.status_code == 200
    assert resp.json()["email"] == "dep@example.com"


def test_get_current_user_logs_do_not_leak_raw_token(caplog):
    repo = UserRepository()
    sessions = SessionStore()

    app = FastAPI()
    get_current_user = build_get_current_user(user_repo=repo, session_store=sessions)

    @app.get("/me")
    def me(current_user=Depends(get_current_user)):
        return {"email": current_user.email}

    client = TestClient(app)
    raw_token = "super-secret-token-abcdefg"

    with caplog.at_level("WARNING", logger="user_auth.auth"):
        resp = client.get("/me", headers={"Authorization": f"Bearer {raw_token}"})

    assert resp.status_code == 401
    assert raw_token not in caplog.text
    assert raw_token[:4] in caplog.text


def test_get_current_user_returns_missing_token_code():
    repo = UserRepository()
    sessions = SessionStore()
    app = _build_auth_app(repo=repo, sessions=sessions)
    client = TestClient(app)

    resp = client.get("/me")

    assert resp.status_code == 401
    detail = resp.json()["detail"]
    assert detail["code"] == "MISSING_TOKEN"


def test_get_current_user_returns_invalid_token_code():
    repo = UserRepository()
    sessions = SessionStore()
    app = _build_auth_app(repo=repo, sessions=sessions)
    client = TestClient(app)

    resp = client.get("/me", headers={"Authorization": "Bearer invalid-token"})

    assert resp.status_code == 401
    detail = resp.json()["detail"]
    assert detail["code"] == "INVALID_TOKEN"


def test_get_current_user_returns_user_not_found_code():
    repo = UserRepository()
    sessions = SessionStore()
    orphan_session = Session.create(user_id="ghost-user")
    sessions.save(orphan_session)

    app = _build_auth_app(repo=repo, sessions=sessions)
    client = TestClient(app)

    resp = client.get(
        "/me",
        headers={"Authorization": f"Bearer {orphan_session.token}"},
    )

    assert resp.status_code == 401
    detail = resp.json()["detail"]
    assert detail["code"] == "USER_NOT_FOUND"
