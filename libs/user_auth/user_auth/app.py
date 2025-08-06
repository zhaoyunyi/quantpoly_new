"""FastAPI 应用工厂与鉴权路由。

提供 register/login/logout/me 路由，
并复用单一权威鉴权依赖 `get_current_user`。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from user_auth.deps import build_get_current_user
from user_auth.domain import PasswordTooWeakError, User
from user_auth.password_reset import InMemoryPasswordResetStore
from user_auth.repository import UserRepository
from user_auth.repository_sqlite import SQLiteUserRepository
from user_auth.session import Session, SessionStore
from user_auth.session_sqlite import SQLiteSessionStore
from user_auth.token import extract_session_token


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class VerifyEmailRequest(BaseModel):
    email: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(alias="newPassword")

    model_config = {"populate_by_name": True}


class UpdateMeRequest(BaseModel):
    email: str | None = None
    display_name: str | None = Field(default=None, alias="displayName")

    model_config = {"populate_by_name": True}


class UpdateMyPasswordRequest(BaseModel):
    current_password: str = Field(alias="currentPassword")
    new_password: str = Field(alias="newPassword")
    revoke_all_sessions: bool = Field(default=True, alias="revokeAllSessions")

    model_config = {"populate_by_name": True}


class AdminUserUpdateRequest(BaseModel):
    email: str | None = None
    display_name: str | None = Field(default=None, alias="displayName")
    role: str | None = None
    level: int | None = None
    is_active: bool | None = Field(default=None, alias="isActive")

    model_config = {"populate_by_name": True}


def _error(status_code: int, *, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "displayName": user.display_name,
        "isActive": user.is_active,
        "emailVerified": user.email_verified,
        "role": user.role,
        "level": user.level,
    }


def create_app(
    user_repo: UserRepository | None = None,
    session_store: SessionStore | None = None,
    sqlite_db_path: str | None = None,
    governance_checker: Callable[..., Any] | None = None,
) -> FastAPI:
    """创建 FastAPI 应用实例。"""

    if sqlite_db_path:
        repo = user_repo or SQLiteUserRepository(db_path=sqlite_db_path)
        sessions = session_store or SQLiteSessionStore(db_path=sqlite_db_path)
    else:
        repo = user_repo or UserRepository()
        sessions = session_store or SessionStore()
    app = FastAPI(title="user-auth")
    reset_store = InMemoryPasswordResetStore()

    get_current_user = build_get_current_user(
        user_repo=repo,
        session_store=sessions,
    )

    _register_routes(
        app=app,
        repo=repo,
        sessions=sessions,
        reset_store=reset_store,
        get_current_user=get_current_user,
        governance_checker=governance_checker,
    )

    return app


def _register_routes(
    *,
    app: FastAPI,
    repo: UserRepository,
    sessions: SessionStore,
    reset_store: InMemoryPasswordResetStore,
    get_current_user,
    governance_checker: Callable[..., Any] | None,
):
    def _authorize_admin_action(
        *,
        request: Request,
        current_user: User,
        action: str,
        target: str,
    ) -> JSONResponse | None:
        token = extract_session_token(headers=request.headers, cookies=request.cookies)

        if governance_checker is not None:
            try:
                governance_checker(
                    actor_id=current_user.id,
                    role=current_user.role,
                    level=current_user.level,
                    action=action,
                    target=target,
                    context={
                        "actor": current_user.id,
                        "token": token or "",
                        "target": target,
                    },
                )
            except Exception:  # noqa: BLE001
                return _error(403, code="ADMIN_REQUIRED", message="admin role required")
            return None

        if current_user.role != "admin":
            return _error(403, code="ADMIN_REQUIRED", message="admin role required")

        return None

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
        if not user.email_verified:
            raise HTTPException(status_code=403, detail="EMAIL_NOT_VERIFIED")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="USER_DISABLED")

        session = Session.create(user_id=user.id)
        sessions.save(session)

        response.set_cookie(
            key="session_token",
            value=session.token,
            httponly=True,
            samesite="lax",
        )

        return {"success": True, "data": {"token": session.token}}

    @app.post("/auth/verify-email")
    def verify_email(body: VerifyEmailRequest):
        user = repo.get_by_email(body.email)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user.verify_email()
        repo.save(user)
        return {"success": True, "message": "Email verified"}

    @app.post("/auth/password-reset/request")
    def request_password_reset(body: PasswordResetRequest):
        user = repo.get_by_email(body.email)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        issued = reset_store.issue(user_id=user.id)
        return {
            "success": True,
            "data": {"resetToken": issued.token},
            "message": "Password reset token issued",
        }

    @app.post("/auth/password-reset/confirm")
    def confirm_password_reset(body: PasswordResetConfirmRequest):
        consumed = reset_store.consume(body.token)
        if consumed is None:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        user = repo.get_by_id(consumed.user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        try:
            replacement = User.register(email=user.email, password=body.new_password)
        except PasswordTooWeakError as exc:
            raise HTTPException(status_code=400, detail="Password too weak") from exc

        user.credential = replacement.credential
        repo.save(user)
        sessions.revoke_by_user(user_id=user.id)
        return {"success": True, "message": "Password reset successful"}

    @app.get("/auth/me")
    def me(current_user: User = Depends(get_current_user)):
        return {"success": True, "data": _user_payload(current_user)}

    @app.post("/auth/logout")
    def logout(request: Request, response: Response, _: User = Depends(get_current_user)):
        token = extract_session_token(headers=request.headers, cookies=request.cookies)
        if token:
            sessions.revoke(token)

        response.delete_cookie("session_token")
        return {"success": True, "message": "Logged out"}

    @app.patch("/users/me")
    def update_me(body: UpdateMeRequest, current_user: User = Depends(get_current_user)):
        if body.email is not None and body.email != current_user.email:
            existing = repo.get_by_email(body.email)
            if existing is not None and existing.id != current_user.id:
                return _error(409, code="DUPLICATE_EMAIL", message="email already exists")

        current_user.update_profile(email=body.email, display_name=body.display_name)
        repo.save(current_user)
        return {"success": True, "data": _user_payload(current_user)}

    @app.patch("/users/me/password")
    def update_my_password(
        body: UpdateMyPasswordRequest,
        current_user: User = Depends(get_current_user),
    ):
        try:
            current_user.change_password(
                current_password=body.current_password,
                new_password=body.new_password,
            )
        except PasswordTooWeakError as exc:
            return _error(400, code="WEAK_PASSWORD", message=str(exc))
        except ValueError as exc:
            return _error(400, code="PASSWORD_CHANGE_INVALID", message=str(exc))

        repo.save(current_user)

        revoked = 0
        if body.revoke_all_sessions:
            revoked = sessions.revoke_by_user(user_id=current_user.id)

        return {
            "success": True,
            "data": {
                "revokedSessions": revoked,
            },
            "message": "Password updated",
        }

    @app.get("/admin/users")
    def admin_list_users(
        request: Request,
        status: str | None = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, alias="pageSize"),
        current_user: User = Depends(get_current_user),
    ):
        denied = _authorize_admin_action(
            request=request,
            current_user=current_user,
            action="users.read_all",
            target="users",
        )
        if denied is not None:
            return denied

        result = repo.list_users(status=status, page=page, page_size=page_size)
        return {
            "success": True,
            "data": {
                "items": [_user_payload(item) for item in result["items"]],
                "total": result["total"],
                "page": result["page"],
                "pageSize": result["pageSize"],
            },
        }

    @app.patch("/admin/users/{user_id}")
    def admin_update_user(
        user_id: str,
        body: AdminUserUpdateRequest,
        request: Request,
        current_user: User = Depends(get_current_user),
    ):
        denied = _authorize_admin_action(
            request=request,
            current_user=current_user,
            action="users.update",
            target=user_id,
        )
        if denied is not None:
            return denied

        target = repo.get_by_id(user_id)
        if target is None:
            return _error(404, code="USER_NOT_FOUND", message="user not found")

        if body.email is not None and body.email != target.email:
            existing = repo.get_by_email(body.email)
            if existing is not None and existing.id != target.id:
                return _error(409, code="DUPLICATE_EMAIL", message="email already exists")

        try:
            if body.email is not None or body.display_name is not None:
                target.update_profile(email=body.email, display_name=body.display_name)
            if body.role is not None:
                target.set_role(body.role)
            if body.level is not None:
                target.set_level(body.level)
            if body.is_active is not None:
                if body.is_active:
                    target.enable()
                else:
                    target.disable()
        except ValueError as exc:
            return _error(400, code="USER_UPDATE_INVALID", message=str(exc))

        repo.save(target)

        if body.is_active is False:
            sessions.revoke_by_user(user_id=target.id)

        return {"success": True, "data": _user_payload(target)}
