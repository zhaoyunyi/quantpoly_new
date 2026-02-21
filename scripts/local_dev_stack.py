"""本地前后端联调一键脚本。

提供三类子命令：
- up: 一键拉起 backend + frontend，并执行健康检查与可选冒烟
- down: 停止本脚本拉起的进程
- status: 查看当前运行状态

输出统一为 JSON，便于终端阅读和脚本集成。
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BACKEND_HOST = "localhost"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_HOST = "localhost"
DEFAULT_FRONTEND_PORT = 3300
DEFAULT_BACKEND_STORAGE = "memory"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_state_dir() -> Path:
    return _repo_root() / ".tmux-logs" / "local_dev_stack"


def _state_file(state_dir: Path) -> Path:
    return state_dir / "state.json"


def _as_origin(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def _command_to_text(command: list[str]) -> str:
    return shlex.join(command)


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        return None
    return data


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _print_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _error(code: str, message: str, *, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "detail": detail or {},
        },
        "timestamp": _utc_now(),
    }


def _is_pid_alive(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _read_log_tail(path: Path, *, max_lines: int = 80) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-max_lines:]


def _build_plan(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = _repo_root()
    state_dir = Path(args.state_dir)

    backend_origin = _as_origin(args.backend_host, args.backend_port)
    frontend_origin = _as_origin(args.frontend_host, args.frontend_port)

    backend_command = [
        sys.executable or "python3",
        str(repo_root / "scripts" / "run_backend_server.py"),
        "--host",
        args.backend_host,
        "--port",
        str(args.backend_port),
        "--storage-backend",
        args.backend_storage,
        "--log-level",
        args.backend_log_level,
    ]
    if args.require_ws_support:
        backend_command.append("--require-ws-support")

    frontend_command = [
        "npm",
        "run",
        "dev",
        "--",
        "--host",
        args.frontend_host,
    ]

    smoke_command = [
        sys.executable or "python3",
        str(repo_root / "scripts" / "smoke_backend_composition.py"),
        "--base-url",
        backend_origin,
    ]

    backend_env = {
        "BACKEND_STORAGE_BACKEND": args.backend_storage,
        "BACKEND_CORS_ALLOWED_ORIGINS": frontend_origin,
        "BACKEND_CORS_ALLOW_CREDENTIALS": "true",
        "BACKEND_CORS_ALLOW_METHODS": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
        "BACKEND_CORS_ALLOW_HEADERS": "*",
        "BACKEND_LOG_LEVEL": args.backend_log_level,
    }
    if args.backend_storage == "postgres" and args.backend_postgres_dsn:
        backend_env["BACKEND_POSTGRES_DSN"] = args.backend_postgres_dsn

    frontend_env = {
        "VITE_BACKEND_ORIGIN": backend_origin,
    }

    return {
        "backend_origin": backend_origin,
        "frontend_origin": frontend_origin,
        "state_dir": str(state_dir),
        "backend_command": backend_command,
        "frontend_command": frontend_command,
        "post_start_smoke_command": smoke_command,
        "backend_command_text": _command_to_text(backend_command),
        "frontend_command_text": _command_to_text(frontend_command),
        "post_start_smoke_command_text": _command_to_text(smoke_command),
        "backend_env": backend_env,
        "frontend_env": frontend_env,
        "backend_log": str(state_dir / "backend.log"),
        "frontend_log": str(state_dir / "frontend.log"),
    }


def _terminate_pid(pid: int, *, grace_seconds: float) -> dict[str, Any]:
    if not _is_pid_alive(pid):
        return {"pid": pid, "status": "not_running"}

    os.kill(pid, signal.SIGTERM)
    deadline = time.time() + max(grace_seconds, 0.1)
    while time.time() < deadline:
        if not _is_pid_alive(pid):
            return {"pid": pid, "status": "terminated"}
        time.sleep(0.1)

    if _is_pid_alive(pid):
        os.kill(pid, signal.SIGKILL)
        time.sleep(0.1)
    return {"pid": pid, "status": "killed"}


def _service_status_from_state(state: dict[str, Any]) -> dict[str, Any]:
    backend = state.get("backend") if isinstance(state.get("backend"), dict) else {}
    frontend = state.get("frontend") if isinstance(state.get("frontend"), dict) else {}
    backend_pid = backend.get("pid") if isinstance(backend.get("pid"), int) else None
    frontend_pid = frontend.get("pid") if isinstance(frontend.get("pid"), int) else None

    backend_alive = _is_pid_alive(backend_pid)
    frontend_alive = _is_pid_alive(frontend_pid)

    return {
        "running": backend_alive and frontend_alive,
        "backend": {
            "pid": backend_pid,
            "alive": backend_alive,
            "origin": backend.get("origin"),
            "log": backend.get("log"),
            "command": backend.get("command"),
        },
        "frontend": {
            "pid": frontend_pid,
            "alive": frontend_alive,
            "origin": frontend.get("origin"),
            "log": frontend.get("log"),
            "command": frontend.get("command"),
        },
        "started_at": state.get("started_at"),
    }


def _spawn_process(*, command: list[str], cwd: Path, env: dict[str, str], log_path: Path) -> subprocess.Popen[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"\n[{_utc_now()}] START { _command_to_text(command) }\n")

    log_stream = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdout=log_stream,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log_stream.close()
    return process


def _wait_http_ready(
    *,
    url: str,
    process: subprocess.Popen[str] | None,
    timeout_seconds: float,
    expected_success_field: bool = False,
) -> tuple[bool, str]:
    deadline = time.time() + max(timeout_seconds, 0.1)
    last_error = "timeout"
    while time.time() < deadline:
        if process is not None and process.poll() is not None:
            return False, f"process exited with code={process.returncode}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                body = response.read().decode("utf-8", errors="ignore")
                if response.status != 200:
                    last_error = f"http_status={response.status}"
                elif expected_success_field:
                    payload = json.loads(body)
                    if isinstance(payload, dict) and payload.get("success") is True:
                        return True, "ok"
                    last_error = "response_missing_success_true"
                else:
                    return True, "ok"
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(0.4)
    return False, last_error


def _run_smoke(plan: dict[str, Any]) -> dict[str, Any]:
    command = plan["post_start_smoke_command"]
    result = subprocess.run(
        command,
        cwd=str(_repo_root()),
        capture_output=True,
        text=True,
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    parsed: dict[str, Any] | None = None
    if stdout:
        try:
            candidate = json.loads(stdout)
            if isinstance(candidate, dict):
                parsed = candidate
        except json.JSONDecodeError:
            parsed = None

    ok = result.returncode == 0 and isinstance(parsed, dict) and parsed.get("success") is True
    return {
        "ok": ok,
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "parsed": parsed,
    }


def _cmd_status(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    state_path = _state_file(Path(args.state_dir))
    state = _read_json_file(state_path)
    if state is None:
        return 0, {
            "success": True,
            "action": "status",
            "running": False,
            "state_file": str(state_path),
            "timestamp": _utc_now(),
        }

    status_payload = _service_status_from_state(state)
    return 0, {
        "success": True,
        "action": "status",
        "state_file": str(state_path),
        **status_payload,
        "timestamp": _utc_now(),
    }


def _cmd_down(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    state_dir = Path(args.state_dir)
    state_path = _state_file(state_dir)
    state = _read_json_file(state_path)
    if state is None:
        return 0, {
            "success": True,
            "action": "down",
            "stopped": False,
            "message": "no running stack state",
            "state_file": str(state_path),
            "timestamp": _utc_now(),
        }

    backend = state.get("backend") if isinstance(state.get("backend"), dict) else {}
    frontend = state.get("frontend") if isinstance(state.get("frontend"), dict) else {}
    backend_pid = backend.get("pid") if isinstance(backend.get("pid"), int) else None
    frontend_pid = frontend.get("pid") if isinstance(frontend.get("pid"), int) else None

    stop_results: list[dict[str, Any]] = []
    for service_name, pid in (("frontend", frontend_pid), ("backend", backend_pid)):
        if pid is None:
            stop_results.append({"service": service_name, "pid": None, "status": "missing_pid"})
            continue
        res = _terminate_pid(pid, grace_seconds=args.grace_seconds)
        stop_results.append({"service": service_name, **res})

    if state_path.exists():
        state_path.unlink()

    return 0, {
        "success": True,
        "action": "down",
        "stopped": True,
        "results": stop_results,
        "state_file": str(state_path),
        "timestamp": _utc_now(),
    }


def _cmd_up(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    if args.frontend_port != DEFAULT_FRONTEND_PORT:
        return 1, _error(
            "INVALID_ARGUMENT",
            f"当前前端 dev 脚本端口固定为 {DEFAULT_FRONTEND_PORT}，请使用 --frontend-port {DEFAULT_FRONTEND_PORT}",
        )

    if args.backend_storage == "postgres" and not (args.backend_postgres_dsn or "").strip():
        return 1, _error(
            "INVALID_ARGUMENT",
            "backend_storage=postgres 时必须提供 --backend-postgres-dsn 或 BACKEND_POSTGRES_DSN",
        )

    plan = _build_plan(args)

    if args.print_only:
        return 0, {
            "success": True,
            "action": "up",
            "print_only": True,
            "plan": plan,
            "timestamp": _utc_now(),
        }

    state_dir = Path(args.state_dir)
    state_path = _state_file(state_dir)
    existing = _read_json_file(state_path)
    if existing is not None:
        existing_status = _service_status_from_state(existing)
        if existing_status["backend"]["alive"] or existing_status["frontend"]["alive"]:
            return 1, _error(
                "ALREADY_RUNNING",
                "检测到已有联调进程正在运行，请先执行 down",
                detail={"status": existing_status, "down_command": f"{sys.executable} scripts/local_dev_stack.py down"},
            )

    repo_root = _repo_root()
    state_dir.mkdir(parents=True, exist_ok=True)

    backend_log = Path(plan["backend_log"])
    frontend_log = Path(plan["frontend_log"])
    backend_log.write_text("", encoding="utf-8")
    frontend_log.write_text("", encoding="utf-8")

    backend_env = dict(os.environ)
    backend_env.update(plan["backend_env"])
    if args.backend_storage == "postgres":
        dsn = (args.backend_postgres_dsn or os.getenv("BACKEND_POSTGRES_DSN", "")).strip()
        backend_env["BACKEND_POSTGRES_DSN"] = dsn
        plan["backend_env"]["BACKEND_POSTGRES_DSN"] = dsn

    frontend_env = dict(os.environ)
    frontend_env.update(plan["frontend_env"])

    started: dict[str, subprocess.Popen[str]] = {}
    checks: list[dict[str, Any]] = []
    smoke_result: dict[str, Any] | None = None

    try:
        backend_proc = _spawn_process(
            command=plan["backend_command"],
            cwd=repo_root,
            env=backend_env,
            log_path=backend_log,
        )
        started["backend"] = backend_proc

        backend_ok, backend_message = _wait_http_ready(
            url=f"{plan['backend_origin']}/health",
            process=backend_proc,
            timeout_seconds=args.backend_wait_timeout,
            expected_success_field=True,
        )
        checks.append({"name": "backend_health", "ok": backend_ok, "detail": backend_message})
        if not backend_ok:
            raise RuntimeError(f"backend 启动失败：{backend_message}")

        frontend_proc = _spawn_process(
            command=plan["frontend_command"],
            cwd=repo_root / "apps" / "frontend_web",
            env=frontend_env,
            log_path=frontend_log,
        )
        started["frontend"] = frontend_proc

        frontend_ok, frontend_message = _wait_http_ready(
            url=f"{plan['frontend_origin']}/",
            process=frontend_proc,
            timeout_seconds=args.frontend_wait_timeout,
            expected_success_field=False,
        )
        checks.append({"name": "frontend_http", "ok": frontend_ok, "detail": frontend_message})
        if not frontend_ok:
            raise RuntimeError(f"frontend 启动失败：{frontend_message}")

        if not args.skip_smoke:
            smoke_result = _run_smoke(plan)
            checks.append(
                {
                    "name": "backend_smoke",
                    "ok": bool(smoke_result.get("ok")),
                    "detail": f"returncode={smoke_result.get('returncode')}",
                }
            )
            if not smoke_result["ok"]:
                raise RuntimeError("backend 冒烟失败，请检查 smoke 输出")

        state_payload = {
            "started_at": _utc_now(),
            "backend": {
                "pid": backend_proc.pid,
                "origin": plan["backend_origin"],
                "log": plan["backend_log"],
                "command": plan["backend_command_text"],
            },
            "frontend": {
                "pid": frontend_proc.pid,
                "origin": plan["frontend_origin"],
                "log": plan["frontend_log"],
                "command": plan["frontend_command_text"],
            },
        }
        _write_json_file(state_path, state_payload)

        return 0, {
            "success": True,
            "action": "up",
            "running": True,
            "state_file": str(state_path),
            "plan": plan,
            "checks": checks,
            "smoke": smoke_result,
            "timestamp": _utc_now(),
        }
    except Exception as exc:  # noqa: BLE001
        cleanup: list[dict[str, Any]] = []
        for service_name in ("frontend", "backend"):
            proc = started.get(service_name)
            if proc is None:
                continue
            cleanup_result = _terminate_pid(proc.pid, grace_seconds=args.grace_seconds)
            cleanup.append({"service": service_name, **cleanup_result})

        return 1, _error(
            "STARTUP_FAILED",
            str(exc),
            detail={
                "checks": checks,
                "cleanup": cleanup,
                "backend_log_tail": _read_log_tail(backend_log),
                "frontend_log_tail": _read_log_tail(frontend_log),
            },
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="local-dev-stack", description="QuantPoly 本地前后端联调一键脚本")
    sub = parser.add_subparsers(dest="command")

    up = sub.add_parser("up", help="启动本地前后端联调栈")
    up.add_argument("--backend-host", default=DEFAULT_BACKEND_HOST)
    up.add_argument("--backend-port", type=int, default=DEFAULT_BACKEND_PORT)
    up.add_argument("--frontend-host", default=DEFAULT_FRONTEND_HOST)
    up.add_argument("--frontend-port", type=int, default=DEFAULT_FRONTEND_PORT)
    up.add_argument("--backend-storage", choices=("memory", "postgres"), default=DEFAULT_BACKEND_STORAGE)
    up.add_argument("--backend-postgres-dsn", default=os.getenv("BACKEND_POSTGRES_DSN"))
    up.add_argument("--backend-log-level", default="warning")
    up.add_argument("--backend-wait-timeout", type=float, default=30.0)
    up.add_argument("--frontend-wait-timeout", type=float, default=45.0)
    up.add_argument("--grace-seconds", type=float, default=5.0)
    up.add_argument("--state-dir", default=str(_default_state_dir()))
    up.add_argument("--skip-smoke", action="store_true", help="跳过启动后的后端冒烟脚本")
    up.add_argument("--require-ws-support", action="store_true", help="后端启动时要求 websocket 运行时依赖")
    up.add_argument("--print-only", action="store_true", help="仅输出将要执行的命令与环境，不实际启动")

    down = sub.add_parser("down", help="停止联调栈")
    down.add_argument("--state-dir", default=str(_default_state_dir()))
    down.add_argument("--grace-seconds", type=float, default=5.0)

    status = sub.add_parser("status", help="查看联调栈状态")
    status.add_argument("--state-dir", default=str(_default_state_dir()))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    handlers = {
        "up": _cmd_up,
        "down": _cmd_down,
        "status": _cmd_status,
    }
    code, payload = handlers[args.command](args)
    _print_json(payload)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
