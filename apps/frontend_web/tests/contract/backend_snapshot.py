"""Contract tests backend snapshot harness.

此脚本通过 FastAPI TestClient 调用后端 composition root，
生成用于前端 contract tests 的真实响应快照（JSON）。

注意：它不依赖 uvicorn，不需要启动独立 HTTP 服务；
但会走完整的路由/依赖/序列化逻辑，属于真实后端代码路径。
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "apps").exists() and (candidate / "libs").exists():
            return candidate
    raise RuntimeError("repo root not found (expected dirs: apps/, libs/)")


def _add_lib_to_sys_path(repo_root: Path, lib_name: str) -> None:
    lib_root = repo_root / "libs" / lib_name
    if lib_root.exists():
        sys.path.insert(0, str(lib_root))


def _bootstrap_sys_path() -> Path:
    repo_root = _find_repo_root(Path(__file__).resolve())
    sys.path.insert(0, str(repo_root))

    # Keep in sync with repo root `conftest.py` (pytest sys.path bootstrap)
    for lib in [
        "platform_core",
        "user_auth",
        "monitoring_realtime",
        "strategy_management",
        "backtest_runner",
        "trading_account",
        "market_data",
        "risk_control",
        "signal_execution",
        "data_topology_boundary",
        "job_orchestration",
        "admin_governance",
        "user_preferences",
    ]:
        _add_lib_to_sys_path(repo_root, lib)

    return repo_root


def _register_and_login(client) -> str:
    email = "frontend-contract@example.com"
    password = "StrongPass123!"

    register = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    if register.status_code not in {200, 409}:
        raise RuntimeError(f"register failed: {register.status_code} {register.text}")

    verify = client.post("/auth/verify-email", json={"email": email})
    if verify.status_code != 200:
        raise RuntimeError(f"verify-email failed: {verify.status_code} {verify.text}")

    login = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    if login.status_code != 200:
        raise RuntimeError(f"login failed: {login.status_code} {login.text}")
    return str(login.json()["data"]["token"])


def main() -> None:
    logging.basicConfig(level=logging.CRITICAL)

    repo_root = _bootstrap_sys_path()
    del repo_root

    from fastapi.testclient import TestClient

    from apps.backend_app.app import create_app

    app = create_app(storage_backend="memory")
    client = TestClient(app)

    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed minimal data to validate non-empty list item schemas.
    created_strategy = client.post(
        "/strategies",
        headers=headers,
        json={
            "name": "MA策略",
            "template": "moving_average",
            "parameters": {"shortWindow": 5, "longWindow": 20},
        },
    )
    if created_strategy.status_code != 200:
        raise RuntimeError(
            f"create strategy failed: {created_strategy.status_code} {created_strategy.text}"
        )
    strategy_id = str(created_strategy.json()["data"]["id"])

    created_account = client.post(
        "/trading/accounts",
        headers=headers,
        json={"accountName": "主账户", "initialCapital": 1000},
    )
    if created_account.status_code != 200:
        raise RuntimeError(
            f"create trading account failed: {created_account.status_code} {created_account.text}"
        )

    created_backtest = client.post(
        "/backtests",
        headers=headers,
        json={
            "strategyId": strategy_id,
            "config": {
                "symbol": "AAPL",
                "prices": [100, 101, 102, 101, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115],
                "startDate": "2026-01-01",
                "endDate": "2026-01-20",
                "timeframe": "1Day",
                "initialCapital": 100000,
                "commissionRate": 0.0,
            },
        },
    )
    if created_backtest.status_code != 200:
        raise RuntimeError(
            f"create backtest failed: {created_backtest.status_code} {created_backtest.text}"
        )

    unauth_client = TestClient(app)

    def _capture(client_: TestClient, method: str, path: str, *, auth: bool = True):
        req_headers = headers if auth else {}
        resp = client_.request(method, path, headers=req_headers)
        payload = None
        try:
            payload = resp.json()
        except Exception:  # noqa: BLE001
            payload = resp.text
        return {"status": resp.status_code, "json": payload}

    snapshot = {
        "token": token,
        "responses": {
            "users_me": _capture(client, "GET", "/users/me"),
            "strategies": _capture(client, "GET", "/strategies"),
            "backtests": _capture(client, "GET", "/backtests"),
            "trading_accounts": _capture(client, "GET", "/trading/accounts"),
            "monitor_summary": _capture(client, "GET", "/monitor/summary"),
            "unauth_strategies": _capture(unauth_client, "GET", "/strategies", auth=False),
        },
    }

    json.dump(snapshot, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
