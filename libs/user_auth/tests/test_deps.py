"""单一鉴权依赖测试。"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from user_auth.deps import build_get_current_user
from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore


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
