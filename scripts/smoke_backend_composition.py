"""组合入口切换前冒烟校验脚本（REST + WS）。

输出 JSON，供 CI 或人工切换前校验使用。
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def _request_json(*, method: str, url: str, body: dict | None = None, headers: dict | None = None):
    data = None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload), dict(response.headers)
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = {"raw": payload}
        return exc.code, parsed, dict(exc.headers)


def run_smoke(*, base_url: str, email: str, password: str) -> dict:
    summary: dict = {
        "success": True,
        "checks": [],
    }

    def _add(name: str, ok: bool, detail: dict | None = None):
        summary["checks"].append({"name": name, "ok": ok, "detail": detail or {}})
        if not ok:
            summary["success"] = False

    health_status, health_body, _ = _request_json(method="GET", url=f"{base_url}/health")
    _add("health", health_status == 200 and bool(health_body.get("success")), {"status": health_status})

    register_status, _register_body, _ = _request_json(
        method="POST",
        url=f"{base_url}/auth/register",
        body={"email": email, "password": password},
    )
    _add("auth_register", register_status in {200, 409}, {"status": register_status})

    verify_status, _verify_body, _ = _request_json(
        method="POST",
        url=f"{base_url}/auth/verify-email",
        body={"email": email},
    )
    _add("auth_verify_email", verify_status == 200, {"status": verify_status})

    login_status, login_body, _ = _request_json(
        method="POST",
        url=f"{base_url}/auth/login",
        body={"email": email, "password": password},
    )
    token = login_body.get("data", {}).get("token") if isinstance(login_body, dict) else None
    _add("auth_login", login_status == 200 and bool(token), {"status": login_status})

    if token:
        headers = {"Authorization": f"Bearer {token}"}
        strategy_status, strategy_body, _ = _request_json(
            method="GET",
            url=f"{base_url}/strategies",
            headers=headers,
        )
        _add(
            "strategy_list",
            strategy_status == 200 and bool(strategy_body.get("success")),
            {"status": strategy_status},
        )

        monitor_status, monitor_body, _ = _request_json(
            method="GET",
            url=f"{base_url}/monitor/summary",
            headers=headers,
        )
        _add(
            "monitor_summary",
            monitor_status == 200 and bool(monitor_body.get("success")),
            {"status": monitor_status},
        )

    ws_supported = False
    ws_ok = False
    ws_message = "websocket client not installed"
    try:
        from websocket import create_connection  # type: ignore

        ws_supported = True
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/monitor"
        ws = create_connection(ws_url, timeout=5, header=[f"Authorization: Bearer {token}"])
        raw = ws.recv()
        ws.close()

        payload = json.loads(raw)
        ws_ok = payload.get("type") == "monitor.heartbeat"
        ws_message = payload.get("type", "unknown")
    except Exception as exc:  # noqa: BLE001
        ws_message = str(exc)

    _add(
        "ws_monitor",
        (not ws_supported) or ws_ok,
        {
            "supported": ws_supported,
            "message": ws_message,
        },
    )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="组合入口切换前冒烟校验")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", default="smoke@example.com")
    parser.add_argument("--password", default="StrongPass123!")
    args = parser.parse_args()

    result = run_smoke(base_url=args.base_url.rstrip("/"), email=args.email, password=args.password)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
