"""本地 Coolify Compose + Playwright 一键验证脚本。

默认流程：
1. 使用 docker compose 拉起本地全栈栈
2. 等待 postgres / backend / frontend 全部 healthy
3. 验证宿主机 backend /health 与 frontend /
4. 执行 Playwright E2E（指向本地 Compose 栈）
5. 默认清理 compose 栈；可通过 --keep-stack 保留

输出统一为 JSON，便于终端阅读和后续脚本集成。
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PROJECT_NAME = "quantpoly_local_browser"
DEFAULT_POSTGRES_PASSWORD = "quantpoly_local_pw"
DEFAULT_FRONTEND_ORIGIN = "http://localhost:13000"
DEFAULT_BACKEND_ORIGIN = "http://localhost:18000"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _print_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _command_to_text(command: list[str]) -> str:
    return shlex.join(command)


def _error(code: str, message: str, *, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": False,
        "action": "verify",
        "error": {
            "code": code,
            "message": message,
            "detail": detail or {},
        },
        "timestamp": _utc_now(),
    }


def _build_plan(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = _repo_root()
    frontend_dir = repo_root / "apps" / "frontend_web"

    env = {
        "POSTGRES_PASSWORD": args.postgres_password,
        "VITE_BACKEND_ORIGIN": args.backend_origin,
        "BACKEND_CORS_ALLOWED_ORIGINS": args.frontend_origin,
        "USER_AUTH_COOKIE_SECURE": "false",
        "USER_AUTH_COOKIE_SAMESITE": "lax",
    }

    compose_base = [
        "docker",
        "compose",
        "-p",
        args.project_name,
        "-f",
        "docker-compose.coolify.yml",
        "-f",
        "docker-compose.coolify.local.yml",
    ]
    up_command = [*compose_base, "up", "-d", "--build"]
    down_command = [*compose_base, "down", "-v"]
    e2e_command = [
        "npx",
        "playwright",
        "test",
        "--config",
        "playwright.compose.config.ts",
    ]

    return {
        "project_name": args.project_name,
        "compose_files": [
            "docker-compose.coolify.yml",
            "docker-compose.coolify.local.yml",
        ],
        "frontend_dir": str(frontend_dir),
        "frontend_origin": args.frontend_origin,
        "backend_origin": args.backend_origin,
        "env": env,
        "commands": {
            "up": _command_to_text(up_command),
            "e2e": _command_to_text(
                [
                    "env",
                    f"PLAYWRIGHT_BACKEND_PORT={args.backend_origin.rsplit(':', 1)[1]}",
                    *e2e_command,
                ]
            ),
            "down": _command_to_text(down_command),
        },
    }


def _run_command(
    *,
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    merged_env = dict(os.environ)
    merged_env.update(env)
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=merged_env,
        capture_output=capture_output,
        text=True,
    )


def _wait_healthy(project_name: str, *, timeout_seconds: float) -> dict[str, str]:
    names = {
        "postgres": f"{project_name}-postgres-1",
        "backend": f"{project_name}-backend-1",
        "frontend": f"{project_name}-frontend-1",
    }
    deadline = time.time() + max(timeout_seconds, 1)
    latest = {key: "unknown" for key in names}
    while time.time() < deadline:
        all_healthy = True
        for service, container_name in names.items():
            proc = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
                    container_name,
                ],
                capture_output=True,
                text=True,
            )
            latest[service] = proc.stdout.strip() if proc.returncode == 0 else "missing"
            if latest[service] != "healthy":
                all_healthy = False
        if all_healthy:
            return latest
        time.sleep(1)
    raise RuntimeError(f"services_not_healthy: {latest}")


def _http_get_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def _http_get_text(url: str) -> str:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8")


def _verify_http(frontend_origin: str, backend_origin: str) -> dict[str, Any]:
    backend_health = _http_get_json(f"{backend_origin}/health")
    frontend_html = _http_get_text(f"{frontend_origin}/")
    if backend_health.get("success") is not True:
        raise RuntimeError("backend_health_not_success")
    if "QuantPoly" not in frontend_html:
        raise RuntimeError("frontend_html_missing_quantpoly")
    return {
        "backend_health": backend_health,
        "frontend_bytes": len(frontend_html.encode("utf-8")),
    }


def _run_e2e(frontend_dir: Path, *, backend_origin: str) -> dict[str, Any]:
    backend_port = backend_origin.rsplit(":", 1)[1]
    proc = _run_command(
        command=[
            "npx",
            "playwright",
            "test",
            "--config",
            "playwright.compose.config.ts",
        ],
        cwd=frontend_dir,
        env={"PLAYWRIGHT_BACKEND_PORT": backend_port},
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout or proc.stderr or "playwright_failed")
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="验证本地 Coolify Compose + Playwright 链路")
    parser.add_argument("--print-only", action="store_true")
    parser.add_argument("--keep-stack", action="store_true")
    parser.add_argument("--project-name", default=DEFAULT_PROJECT_NAME)
    parser.add_argument("--postgres-password", default=DEFAULT_POSTGRES_PASSWORD)
    parser.add_argument("--frontend-origin", default=DEFAULT_FRONTEND_ORIGIN)
    parser.add_argument("--backend-origin", default=DEFAULT_BACKEND_ORIGIN)
    parser.add_argument("--health-timeout-seconds", type=float, default=120.0)
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    plan = _build_plan(args)
    if args.print_only:
        _print_json(
            {
                "success": True,
                "action": "verify",
                "plan": plan,
                "timestamp": _utc_now(),
            }
        )
        return 0

    env = plan["env"]
    compose_base = [
        "docker",
        "compose",
        "-p",
        args.project_name,
        "-f",
        "docker-compose.coolify.yml",
        "-f",
        "docker-compose.coolify.local.yml",
    ]
    up_command = [*compose_base, "up", "-d", "--build"]
    down_command = [*compose_base, "down", "-v"]

    cleanup_result: dict[str, Any] = {"attempted": False}
    try:
        up = _run_command(command=up_command, cwd=repo_root, env=env)
        if up.returncode != 0:
            _print_json(_error("COMPOSE_UP_FAILED", "docker compose up 失败", detail={"stdout": up.stdout, "stderr": up.stderr}))
            return 1

        health = _wait_healthy(args.project_name, timeout_seconds=args.health_timeout_seconds)
        http_check = _verify_http(args.frontend_origin, args.backend_origin)
        e2e = _run_e2e(repo_root / "apps" / "frontend_web", backend_origin=args.backend_origin)

        _print_json(
            {
                "success": True,
                "action": "verify",
                "project_name": args.project_name,
                "health": health,
                "http_check": http_check,
                "e2e": e2e,
                "cleanup": {"attempted": not args.keep_stack},
                "timestamp": _utc_now(),
            }
        )
        return 0
    except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        _print_json(
            _error(
                "VERIFY_FAILED",
                "本地 Coolify Compose 验证失败",
                detail={"message": str(exc)},
            )
        )
        return 1
    finally:
        if not args.keep_stack:
            cleanup_result["attempted"] = True
            _run_command(command=down_command, cwd=repo_root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
