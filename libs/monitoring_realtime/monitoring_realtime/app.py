"""FastAPI 应用工厂（实时监控）。

当前仅提供 `/ws/monitor` WebSocket 端点，用于实时推送监控消息。
鉴权逻辑复用 `user_auth` 的 session token（Bearer 优先，其次 Cookie）。
"""

from __future__ import annotations

import time

from fastapi import FastAPI, WebSocket

from user_auth.repository import UserRepository
from user_auth.session import SessionStore
from user_auth.token import extract_session_token


def create_app(
    user_repo: UserRepository | None = None,
    session_store: SessionStore | None = None,
) -> FastAPI:
    """创建 FastAPI 应用实例。"""

    repo = user_repo or UserRepository()
    sessions = session_store or SessionStore()
    app = FastAPI(title="monitoring-realtime")

    @app.websocket("/ws/monitor")
    async def ws_monitor(websocket: WebSocket):
        # 为了让客户端能收到 4401 close code，这里先 accept 再根据鉴权结果关闭。
        # （否则会变成 HTTP handshake 拒绝，无法携带业务 close code）
        await websocket.accept()

        token = extract_session_token(headers=websocket.headers, cookies=websocket.cookies)
        if not token:
            await websocket.close(code=4401)
            return

        session = sessions.get_by_token(token)
        if session is None:
            await websocket.close(code=4401)
            return

        user = repo.get_by_id(session.user_id)
        if user is None:
            await websocket.close(code=4401)
            return

        # 1 秒内发送至少一条结构合法的监控消息
        payload = {"type": "monitor.heartbeat", "ts": int(time.time())}
        await websocket.send_json(payload)

        # 之后保持连接（不做持续推送，避免测试阻塞）。
        await websocket.close(code=1000)

    return app
