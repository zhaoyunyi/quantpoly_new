"""FastAPI 鉴权依赖。

提供单一权威 `get_current_user` 依赖构建器，
并统一 Bearer/Cookie token 提取与错误日志脱敏。
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import HTTPException, Request

from user_auth.domain import User
from user_auth.repository import UserRepository
from user_auth.session import SessionStore
from user_auth.token import extract_session_token


def _mask_token(token: str) -> str:
    if len(token) <= 4:
        return "***"
    return token[:4] + "***"


def build_get_current_user(
    *,
    user_repo: UserRepository,
    session_store: SessionStore,
    logger: logging.Logger | None = None,
    token_extractor: Callable[..., str | None] = extract_session_token,
):
    """构建单一 `get_current_user` 依赖。"""

    auth_logger = logger or logging.getLogger("user_auth.auth")

    def _auth_error(*, code: str, message: str) -> HTTPException:
        return HTTPException(
            status_code=401,
            detail={
                "code": code,
                "message": message,
            },
        )

    def get_current_user(request: Request) -> User:
        token = token_extractor(
            headers=request.headers,
            cookies=request.cookies,
        )
        if not token:
            auth_logger.warning("auth_failed reason=missing_token")
            raise _auth_error(code="MISSING_TOKEN", message="Not authenticated")

        session = session_store.get_by_token(token)
        if session is None:
            auth_logger.warning("auth_failed reason=invalid_or_expired token=%s", _mask_token(token))
            raise _auth_error(code="INVALID_TOKEN", message="Invalid or expired token")

        user = user_repo.get_by_id(session.user_id)
        if user is None:
            auth_logger.warning("auth_failed reason=user_not_found token=%s", _mask_token(token))
            raise _auth_error(code="USER_NOT_FOUND", message="User not found")

        return user

    return get_current_user
