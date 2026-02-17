"""Run quantpoly backend app as an HTTP server (for Playwright E2E).

This repo uses a libs/ multi-package layout without requiring installation of each
package in editable mode. Similar to `conftest.py`, this script bootstraps
`sys.path` so `apps.backend_app:create_app` can import all libs successfully.

Default behavior is tuned for local/E2E runs:
- in-memory storage backend (no Postgres required)
- bind to 127.0.0.1
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path


_LIBS = (
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
)


def _bootstrap_sys_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    for lib in _LIBS:
        lib_root = repo_root / "libs" / lib
        if lib_root.exists():
            sys.path.insert(0, str(lib_root))


def _has_websocket_runtime_support() -> bool:
    return (
        importlib.util.find_spec("websockets") is not None
        or importlib.util.find_spec("wsproto") is not None
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run backend HTTP server for E2E.")
    parser.add_argument("--host", default=os.getenv("BACKEND_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("BACKEND_PORT", "8000")),
    )
    parser.add_argument(
        "--storage-backend",
        default=os.getenv("BACKEND_STORAGE_BACKEND", "memory"),
        choices=("memory", "postgres"),
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("BACKEND_LOG_LEVEL", "warning"),
        choices=("critical", "error", "warning", "info", "debug", "trace"),
    )
    parser.add_argument(
        "--require-ws-support",
        action="store_true",
        default=os.getenv("BACKEND_REQUIRE_WS_SUPPORT", "false").lower() in {"1", "true", "yes"},
    )
    args = parser.parse_args(argv)

    _bootstrap_sys_path()

    try:
        import uvicorn  # type: ignore
    except ModuleNotFoundError:
        sys.stderr.write(
            "Missing dependency: uvicorn.\n"
            "Install it into the repo venv, e.g.:\n"
            "  ./.venv/bin/pip install 'uvicorn[standard]'\n"
        )
        return 1

    if args.require_ws_support and not _has_websocket_runtime_support():
        sys.stderr.write(
            "Missing WebSocket runtime support (websockets/wsproto).\n"
            "Install one of the following into the repo venv:\n"
            "  ./.venv/bin/pip install 'uvicorn[standard]'\n"
            "  # or\n"
            "  ./.venv/bin/pip install websockets\n"
        )
        return 1

    from apps.backend_app import create_app

    app = create_app(storage_backend=args.storage_backend)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
