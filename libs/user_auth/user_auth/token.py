"""Token 提取与解析工具。

该模块用于复用 HTTP / WebSocket 的 session token 提取规则。
"""

from __future__ import annotations

from typing import Mapping


def extract_session_token(
    *,
    headers: Mapping[str, str] | None,
    cookies: Mapping[str, str] | None,
) -> str | None:
    """从请求中提取 session token。

    优先级：Authorization Bearer > Cookie(session_token)
    """

    if headers:
        raw = headers.get("Authorization") or headers.get("authorization")
        if raw:
            lower = raw.lower()
            if lower.startswith("bearer "):
                token = raw[7:].strip()
                if token:
                    return token

    if cookies:
        token = cookies.get("session_token")
        if token:
            return token

    return None

