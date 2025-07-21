"""FastAPI 应用工厂与鉴权路由。

提供 register/login/logout/me 路由，
以及单一鉴权依赖 get_current_user（Cookie + Bearer 双通道）。
"""
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from user_auth.domain import User, PasswordTooWeakError
from user_auth.session import Session, SessionStore
from user_auth.repository import UserRepository


# ── 请求/响应模型 ──

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


_bearer_scheme = HTTPBearer(auto_error=False)


def create_app(
    user_repo: UserRepository | None = None,
    session_store: SessionStore | None = None,
) -> FastAPI:
    """创建 FastAPI 应用实例。"""
    repo = user_repo or UserRepository()
    sessions = session_store or SessionStore()
    app = FastAPI(title="user-auth")

    # ── 鉴权依赖 ──

    def _extract_token(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    ) -> str | None:
        """从 Bearer header 或 Cookie 提取 token。"""
        if credentials and credentials.credentials:
            return credentials.credentials
        return request.cookies.get("session_token")

    def get_current_user(token: str | None = Depends(_extract_token)) -> User:
        """单一鉴权依赖：解析 token 并返回当前用户。"""
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        session = sessions.get_by_token(token)
        if session is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        user = repo.get_by_id(session.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    # ── 路由注册（分段添加） ──
    _register_routes(app, repo, sessions, get_current_user)

    return app


def _register_routes(app, repo, sessions, get_current_user):
    """注册所有鉴权路由。"""

    @app.post("/auth/register")
    def register(body: RegisterRequest):
        if repo.email_exists(body.email):
            raise HTTPException(status_code=409, detail="Email already registered")
        try:
            user = User.register(email=body.email, password=body.password)
        except PasswordTooWeakError:
            raise HTTPException(status_code=400, detail="Password too weak")
        repo.save(user)
        return {"success": True, "message": "User registered"}

    @app.post("/auth/login")
    def login(body: LoginRequest):
        user = repo.get_by_email(body.email)
        if user is None or not user.authenticate(body.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        session = Session.create(user_id=user.id)
        sessions.save(session)
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
    def logout(current_user: User = Depends(get_current_user), request: Request = None):
        token = None
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:]
        if not token:
            token = request.cookies.get("session_token")
        if token:
            sessions.revoke(token)
        return {"success": True, "message": "Logged out"}
