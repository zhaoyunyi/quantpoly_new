"""FastAPI 应用工厂与鉴权路由。

提供 register/login/logout/me 路由，
并复用单一权威鉴权依赖 `get_current_user`。
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

from user_auth.deps import build_get_current_user
from user_auth.domain import PasswordTooWeakError, User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore
from user_auth.token import extract_session_token


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def create_app(
    user_repo: UserRepository | None = None,
    session_store: SessionStore | None = None,
) -> FastAPI:
    """创建 FastAPI 应用实例。"""

    repo = user_repo or UserRepository()
    sessions = session_store or SessionStore()
    app = FastAPI(title="user-auth")

    get_current_user = build_get_current_user(
        user_repo=repo,
        session_store=sessions,
    )

    _register_routes(
        app=app,
        repo=repo,
        sessions=sessions,
        get_current_user=get_current_user,
    )

    return app


def _register_routes(*, app: FastAPI, repo: UserRepository, sessions: SessionStore, get_current_user):
    @app.post("/auth/register")
    def register(body: RegisterRequest):
        if repo.email_exists(body.email):
            raise HTTPException(status_code=409, detail="Email already registered")

        try:
            user = User.register(email=body.email, password=body.password)
        except PasswordTooWeakError as exc:
            raise HTTPException(status_code=400, detail="Password too weak") from exc

        repo.save(user)
        return {"success": True, "message": "User registered"}

    @app.post("/auth/login")
    def login(body: LoginRequest, response: Response):
        user = repo.get_by_email(body.email)
        if user is None or not user.authenticate(body.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        session = Session.create(user_id=user.id)
        sessions.save(session)

        response.set_cookie(
            key="session_token",
            value=session.token,
            httponly=True,
            samesite="lax",
        )

        return {"success": True, "data": {"token": session.token}}

    @app.get("/auth/me")
    def me(current_user: User = Depends(get_current_user)):
        return {
            "success": True,
            "data": {
                "id": current_user.id,
                "email": current_user.email,
                "isActive": current_user.is_active,
            },
        }

    @app.post("/auth/logout")
    def logout(request: Request, response: Response, _: User = Depends(get_current_user)):
        token = extract_session_token(headers=request.headers, cookies=request.cookies)
        if token:
            sessions.revoke(token)

        response.delete_cookie("session_token")
        return {"success": True, "message": "Logged out"}
