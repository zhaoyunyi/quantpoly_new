"""FastAPI 应用工厂（实时监控）。

提供 `/ws/monitor` WebSocket 端点，支持：
- 标准消息 envelope：type / payload / data / timestamp
- 鉴权（Bearer 优先，其次 Cookie）
- 订阅协议（subscribe/unsubscribe）
- ping/pong
- signals / alerts 增量推送（按用户过滤）

并提供 `/monitor/summary` REST 摘要端点，统一监控读模型语义。
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect

from platform_core.logging import mask_sensitive
from platform_core.response import error_response, success_response
from user_auth.repository import UserRepository
from user_auth.session import SessionStore
from user_auth.token import extract_session_token

SourceFn = Callable[[str], list[dict[str, Any]]]
SummaryFn = Callable[[str], dict[str, Any]]


def _task_type(item: dict[str, Any]) -> str | None:
    if "taskType" in item:
        value = item.get("taskType")
        return str(value) if value is not None else None
    if "task_type" in item:
        value = item.get("task_type")
        return str(value) if value is not None else None
    return None


def _task_id(item: dict[str, Any]) -> str | None:
    for key in ("taskId", "task_id", "id"):
        value = item.get(key)
        if value:
            return str(value)
    return None


def _envelope(
    *,
    msg_type: str,
    payload: dict[str, Any] | None = None,
    data: Any = None,
    timestamp: int | None = None,
) -> dict[str, Any]:
    ts = int(time.time()) if timestamp is None else int(timestamp)
    return {
        "type": msg_type,
        "payload": payload or {},
        "data": data,
        "timestamp": ts,
    }


def _extract_channels(message: dict[str, Any]) -> list[str]:
    payload = message.get("payload") or {}
    channels = payload.get("channels")
    if isinstance(channels, list):
        return [str(item) for item in channels]
    single = payload.get("channel")
    if single is None:
        return []
    return [str(single)]


def _item_user_id(item: dict[str, Any]) -> str | None:
    if "userId" in item:
        value = item.get("userId")
        return str(value) if value is not None else None
    if "user_id" in item:
        value = item.get("user_id")
        return str(value) if value is not None else None
    return None


def _item_id(item: dict[str, Any]) -> str:
    if "id" in item and item["id"] is not None:
        return str(item["id"])
    return str(item)


def _dedupe_and_truncate(
    *,
    items: list[dict[str, Any]],
    seen_ids: set[str],
    incremental: bool,
    max_items: int,
) -> tuple[list[dict[str, Any]], bool]:
    result: list[dict[str, Any]] = []
    local_seen: set[str] = set()

    for item in items:
        item_id = _item_id(item)
        if item_id in local_seen:
            continue
        local_seen.add(item_id)

        if incremental and item_id in seen_ids:
            continue

        result.append(item)
        seen_ids.add(item_id)

    truncated = len(result) > max_items
    if truncated:
        result = result[:max_items]

    return result, truncated


def _mask_token(token: str) -> str:
    if len(token) <= 4:
        return "***"
    return token[:4] + "***"


def _mask_request_context(websocket: WebSocket, body: Any | None = None) -> str:
    raw = {
        "headers": dict(websocket.headers),
        "cookies": dict(websocket.cookies),
        "body": body,
    }
    return mask_sensitive(str(raw))


def _resolve_user(*, headers: Any, cookies: Any, repo: UserRepository, sessions: SessionStore):
    token = extract_session_token(headers=headers, cookies=cookies)
    if not token:
        return None
    session = sessions.get_by_token(token)
    if session is None:
        return None
    return repo.get_by_id(session.user_id)


def _default_summary(*, user_id: str, signal_source: SourceFn, alert_source: SourceFn) -> dict[str, Any]:
    raw_signals = signal_source(user_id)
    user_signals = [item for item in raw_signals if _item_user_id(item) == user_id]

    raw_alerts = alert_source(user_id)
    user_alerts = [item for item in raw_alerts if _item_user_id(item) == user_id]
    open_alerts = [
        item for item in user_alerts if str(item.get("status", "open")).strip().lower() != "resolved"
    ]
    critical_alerts = [
        item
        for item in user_alerts
        if str(item.get("severity", "")).strip().lower() in {"critical", "high"}
    ]

    pending_signals = [
        item for item in user_signals if str(item.get("status", "pending")).strip().lower() == "pending"
    ]
    expired_signals = [
        item for item in user_signals if str(item.get("status", "")).strip().lower() == "expired"
    ]

    return {
        "type": "monitor.summary",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "signals": {
            "total": len(user_signals),
            "pending": len(pending_signals),
            "expired": len(expired_signals),
        },
        "alerts": {
            "open": len(open_alerts),
            "critical": len(critical_alerts),
        },
        "tasks": {
            "running": 0,
        },
    }


def create_app(
    user_repo: UserRepository | None = None,
    session_store: SessionStore | None = None,
    signal_source: SourceFn | None = None,
    alert_source: SourceFn | None = None,
    alert_task_source: SourceFn | None = None,
    summary_source: SummaryFn | None = None,
    max_items_per_message: int = 100,
) -> FastAPI:
    """创建 FastAPI 应用实例。"""

    repo = user_repo or UserRepository()
    sessions = session_store or SessionStore()
    app = FastAPI(title="monitoring-realtime")

    signals_source = signal_source or (lambda _user_id: [])
    alerts_source = alert_source or (lambda _user_id: [])
    alert_tasks_source = alert_task_source or (lambda _user_id: [])
    auth_logger = logging.getLogger("monitoring_realtime.auth")

    @app.get("/monitor/summary")
    def monitor_summary(request: Request):
        user = _resolve_user(headers=request.headers, cookies=request.cookies, repo=repo, sessions=sessions)
        if user is None:
            return JSONResponse(
                status_code=401,
                content=error_response(code="UNAUTHORIZED", message="unauthorized"),
            )

        if summary_source is not None:
            payload = summary_source(user.id)
        else:
            payload = _default_summary(user_id=user.id, signal_source=signals_source, alert_source=alerts_source)

        return success_response(data=payload)

    @app.websocket("/ws/monitor")
    async def ws_monitor(websocket: WebSocket):
        await websocket.accept()

        token = extract_session_token(headers=websocket.headers, cookies=websocket.cookies)
        if not token:
            auth_logger.warning(
                "ws_auth_failed reason=missing_token context=%s",
                _mask_request_context(websocket, body=None),
            )
            await websocket.close(code=4401)
            return

        session = sessions.get_by_token(token)
        if session is None:
            auth_logger.warning(
                "ws_auth_failed reason=invalid_token token=%s context=%s",
                _mask_token(token),
                _mask_request_context(websocket, body=None),
            )
            await websocket.close(code=4401)
            return

        user = repo.get_by_id(session.user_id)
        if user is None:
            auth_logger.warning(
                "ws_auth_failed reason=user_not_found token=%s context=%s",
                _mask_token(token),
                _mask_request_context(websocket, body=None),
            )
            await websocket.close(code=4401)
            return

        subscriptions = {"signals", "alerts"}
        sent_ids: dict[str, set[str]] = {
            "signals": set(),
            "alerts": set(),
        }

        heartbeat = _envelope(msg_type="monitor.heartbeat", data={"userId": user.id})
        heartbeat["ts"] = heartbeat["timestamp"]
        await websocket.send_json(heartbeat)

        async def _push_updates(*, incremental: bool) -> None:
            if "signals" in subscriptions:
                raw_signals = signals_source(user.id)
                user_signals = [item for item in raw_signals if _item_user_id(item) == user.id]
                signal_items, signal_truncated = _dedupe_and_truncate(
                    items=user_signals,
                    seen_ids=sent_ids["signals"],
                    incremental=incremental,
                    max_items=max_items_per_message,
                )
                if signal_items:
                    await websocket.send_json(
                        _envelope(
                            msg_type="signals_update",
                            payload={
                                "snapshot": not incremental,
                                "truncated": signal_truncated,
                            },
                            data={"items": signal_items},
                        )
                    )

            if "alerts" in subscriptions:
                raw_alerts = alerts_source(user.id)
                user_alerts = [item for item in raw_alerts if _item_user_id(item) == user.id]
                unresolved_alerts = [
                    item
                    for item in user_alerts
                    if str(item.get("status", "open")).strip().lower() != "resolved"
                ]
                alert_items, alert_truncated = _dedupe_and_truncate(
                    items=unresolved_alerts,
                    seen_ids=sent_ids["alerts"],
                    incremental=False,
                    max_items=max_items_per_message,
                )
                if alert_items:
                    raw_tasks = alert_tasks_source(user.id)
                    user_tasks = [item for item in raw_tasks if _item_user_id(item) == user.id]
                    notify_tasks = [item for item in user_tasks if _task_type(item) == "risk_alert_notify"]
                    task_summary: dict[str, Any] | None = None
                    if notify_tasks:
                        latest = notify_tasks[-1]
                        task_summary = {
                            "taskId": _task_id(latest),
                            "taskType": _task_type(latest),
                            "status": latest.get("status"),
                            "result": latest.get("result"),
                        }

                    await websocket.send_json(
                        _envelope(
                            msg_type="risk_alert",
                            payload={
                                "snapshot": True,
                                "truncated": alert_truncated,
                                "counts": {
                                    "openAlerts": len(unresolved_alerts),
                                },
                                "taskSummary": task_summary,
                            },
                            data={"items": alert_items},
                        )
                    )

        while True:
            try:
                message = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            msg_type = message.get("type")

            if msg_type == "ping":
                await websocket.send_json(
                    _envelope(
                        msg_type="pong",
                        payload={"echo": message.get("timestamp")},
                    )
                )
                continue

            if msg_type == "subscribe":
                for channel in _extract_channels(message):
                    if channel in {"signals", "alerts"}:
                        subscriptions.add(channel)

                await websocket.send_json(
                    _envelope(
                        msg_type="subscribed",
                        payload={"channels": sorted(subscriptions)},
                    )
                )
                continue

            if msg_type == "unsubscribe":
                for channel in _extract_channels(message):
                    subscriptions.discard(channel)

                await websocket.send_json(
                    _envelope(
                        msg_type="unsubscribed",
                        payload={"channels": sorted(subscriptions)},
                    )
                )
                continue

            if msg_type == "resync":
                sent_ids = {"signals": set(), "alerts": set()}
                await _push_updates(incremental=False)
                continue

            if msg_type == "poll":
                await _push_updates(incremental=True)
                continue

            await websocket.send_json(
                _envelope(
                    msg_type="unknown_command",
                    payload={"received": msg_type},
                )
            )

    return app
