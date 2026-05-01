"""触发并轮询 Coolify 生产全栈应用部署。

默认读取 deploy/secrets/ops_tokens.local.env 中的本地令牌，令牌文件被
.gitignore 忽略，不需要也不应该提交。脚本输出 JSON，方便人工阅读或
后续 CI/运维脚本集成。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_APPLICATION_UUID = "wgsoo0gow8wkwow8kkg00kks"
DEFAULT_ENV_FILE = Path("deploy/secrets/ops_tokens.local.env")
DEFAULT_TARGET_STATUS = "running:healthy"
ENV_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class CoolifyConfig:
    base_url: str
    api_token: str
    application_uuid: str


class CoolifyApiError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _print_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _error_payload(code: str, message: str, *, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "detail": detail or {},
        },
        "timestamp": _utc_now(),
    }


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            raise ValueError(f"{path}:{line_number} 不是 KEY=VALUE 格式")

        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not ENV_KEY_PATTERN.match(key):
            raise ValueError(f"{path}:{line_number} 变量名不合法: {key}")

        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized.startswith(("http://", "https://")):
        raise ValueError("COOLIFY_BASE_URL 必须以 http:// 或 https:// 开头")
    return normalized


def build_config(args: argparse.Namespace) -> CoolifyConfig:
    env_file_values = load_env_file(args.env_file)
    base_url = (
        args.base_url
        or os.environ.get("COOLIFY_BASE_URL")
        or env_file_values.get("COOLIFY_BASE_URL")
        or ""
    )
    api_token = (
        args.api_token
        or os.environ.get("COOLIFY_API_TOKEN")
        or env_file_values.get("COOLIFY_API_TOKEN")
        or ""
    )
    application_uuid = args.application_uuid or DEFAULT_APPLICATION_UUID

    missing = [
        name
        for name, value in {
            "COOLIFY_BASE_URL": base_url,
            "COOLIFY_API_TOKEN": api_token,
            "application_uuid": application_uuid,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"缺少必要配置: {', '.join(missing)}")

    return CoolifyConfig(
        base_url=_normalize_base_url(base_url),
        api_token=api_token,
        application_uuid=application_uuid,
    )


def _request_json(url: str, *, api_token: str, method: str = "GET") -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_token}",
            "User-Agent": "quantpoly-coolify-deploy/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise CoolifyApiError("Coolify API 请求失败", status=exc.code, body=body) from exc
    except urllib.error.URLError as exc:
        raise CoolifyApiError(f"无法连接 Coolify API: {exc.reason}") from exc

    if not body:
        return {}
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise CoolifyApiError("Coolify API 返回了非 JSON 响应", body=body[:1000]) from exc
    if isinstance(decoded, dict):
        return decoded
    return {"data": decoded}


def _application_url(config: CoolifyConfig) -> str:
    return f"{config.base_url}/api/v1/applications/{config.application_uuid}"


def _deploy_url(config: CoolifyConfig, *, force: bool) -> str:
    query = urllib.parse.urlencode(
        {
            "uuid": config.application_uuid,
            "force": str(force).lower(),
        }
    )
    return f"{config.base_url}/api/v1/deploy?{query}"


def get_application(config: CoolifyConfig) -> dict[str, Any]:
    return _request_json(_application_url(config), api_token=config.api_token)


def trigger_deploy(config: CoolifyConfig, *, force: bool) -> dict[str, Any]:
    # Coolify v4 的部署入口是 GET；不要用 HEAD 探测该 endpoint，HEAD 也可能触发部署。
    return _request_json(_deploy_url(config, force=force), api_token=config.api_token, method="GET")


def summarize_application(application: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "uuid",
        "name",
        "fqdn",
        "status",
        "git_repository",
        "git_branch",
        "docker_compose_location",
        "last_online_at",
        "updated_at",
        "restart_count",
    ]
    return {key: application.get(key) for key in keys if key in application}


def wait_for_application_status(
    config: CoolifyConfig,
    *,
    target_status: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> dict[str, Any]:
    deadline = time.time() + max(timeout_seconds, 1)
    latest: dict[str, Any] = {}
    while time.time() < deadline:
        latest = get_application(config)
        if latest.get("status") == target_status:
            return latest
        time.sleep(max(poll_interval_seconds, 1))

    raise TimeoutError(
        f"等待 Coolify 应用达到 {target_status} 超时，最后状态为 {latest.get('status')!r}"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="触发 Coolify 生产全栈应用部署并轮询健康状态")
    parser.add_argument("--env-file", type=Path, default=_repo_root() / DEFAULT_ENV_FILE)
    parser.add_argument("--base-url", default=None, help="覆盖 COOLIFY_BASE_URL")
    parser.add_argument("--api-token", default=None, help="覆盖 COOLIFY_API_TOKEN；不建议在 shell history 中直接传入")
    parser.add_argument("--application-uuid", default=DEFAULT_APPLICATION_UUID)
    parser.add_argument("--force", action="store_true", help="传给 Coolify deploy endpoint 的 force=true")
    parser.add_argument("--status-only", action="store_true", help="只读取应用状态，不触发部署")
    parser.add_argument("--dry-run", action="store_true", help="只校验配置并打印将要调用的 endpoint，不联网")
    parser.add_argument("--no-wait", action="store_true", help="触发部署后不轮询运行状态")
    parser.add_argument("--target-status", default=DEFAULT_TARGET_STATUS)
    parser.add_argument("--timeout-seconds", type=float, default=900.0)
    parser.add_argument("--poll-interval-seconds", type=float, default=5.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = build_config(args)
        if args.dry_run:
            _print_json(
                {
                    "success": True,
                    "action": "dry-run",
                    "application_uuid": config.application_uuid,
                    "base_url": config.base_url,
                    "status_endpoint": _application_url(config),
                    "deploy_endpoint": _deploy_url(config, force=args.force),
                    "timestamp": _utc_now(),
                }
            )
            return 0

        if args.status_only:
            application = get_application(config)
            _print_json(
                {
                    "success": True,
                    "action": "status",
                    "application": summarize_application(application),
                    "timestamp": _utc_now(),
                }
            )
            return 0

        before = get_application(config)
        deployment = trigger_deploy(config, force=args.force)
        final_application = before if args.no_wait else wait_for_application_status(
            config,
            target_status=args.target_status,
            timeout_seconds=args.timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
        _print_json(
            {
                "success": True,
                "action": "deploy",
                "application_uuid": config.application_uuid,
                "deployment": deployment,
                "before": summarize_application(before),
                "application": summarize_application(final_application),
                "waited": not args.no_wait,
                "timestamp": _utc_now(),
            }
        )
        return 0
    except (ValueError, CoolifyApiError, TimeoutError) as exc:
        detail: dict[str, Any] = {}
        if isinstance(exc, CoolifyApiError):
            detail = {
                "http_status": exc.status,
                "body": exc.body,
            }
        _print_json(_error_payload(type(exc).__name__, str(exc), detail=detail))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
