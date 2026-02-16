"""backend_app 配置 CLI。

遵循 CLI Mandate：
- 支持 stdin / args / file 输入
- stdout 输出 JSON
"""

from __future__ import annotations

import argparse
import json
import sys

from apps.backend_app.settings import (
    CompositionSettings,
    normalize_enabled_contexts,
    normalize_job_executor_mode,
    normalize_market_data_provider,
    normalize_storage_backend,
)
from platform_core.response import error_response, success_response


def _load_payload(*, input_file: str | None) -> dict:
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    else:
        raw = sys.stdin.read().strip()

    if not raw:
        return {}

    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("input payload must be a JSON object")
    return parsed


def _as_contexts(value: object) -> set[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("enabledContexts must be an array")
    result: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError("enabledContexts items must be strings")
        result.add(item)
    return result


def _cmd_resolve_settings(args: argparse.Namespace) -> dict:
    try:
        payload = _load_payload(input_file=args.input_file)

        storage_backend_raw = args.storage_backend or payload.get("storageBackend")
        market_provider_raw = args.market_data_provider or payload.get("marketDataProvider")
        postgres_dsn_raw = args.postgres_dsn or payload.get("postgresDsn")
        contexts_raw = args.enabled_contexts or payload.get("enabledContexts")
        job_executor_mode_raw = args.job_executor_mode or payload.get("jobExecutorMode")

        env_settings = CompositionSettings.from_env()
        storage_backend = normalize_storage_backend(storage_backend_raw or env_settings.storage_backend)
        market_data_provider = normalize_market_data_provider(market_provider_raw or env_settings.market_data_provider)
        job_executor_mode = normalize_job_executor_mode(job_executor_mode_raw or env_settings.job_executor_mode)

        contexts = normalize_enabled_contexts(_as_contexts(contexts_raw))

        postgres_dsn: str | None
        if postgres_dsn_raw is None:
            postgres_dsn = env_settings.postgres_dsn
        else:
            postgres_dsn = str(postgres_dsn_raw).strip() or None

        resolved = CompositionSettings(
            enabled_contexts=contexts,
            storage_backend=storage_backend,
            postgres_dsn=postgres_dsn,
            market_data_provider=market_data_provider,
            job_executor_mode=job_executor_mode,
        )

        return success_response(
            data={
                "enabledContexts": sorted(resolved.enabled_contexts),
                "storageBackend": resolved.storage_backend,
                "postgresDsn": resolved.postgres_dsn,
                "marketDataProvider": resolved.market_data_provider,
                "jobExecutorMode": resolved.job_executor_mode,
            },
            message="settings resolved",
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return error_response(code="INVALID_ARGUMENT", message=str(exc))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backend-app", description="QuantPoly backend app CLI")
    sub = parser.add_subparsers(dest="command")

    resolve = sub.add_parser("resolve-settings", help="解析组合入口配置")
    resolve.add_argument("--input-file", default=None, help="输入 JSON 文件路径，省略时读取 stdin")
    resolve.add_argument("--storage-backend", default=None, help="storage backend: postgres|memory")
    resolve.add_argument("--postgres-dsn", default=None, help="postgres DSN")
    resolve.add_argument("--market-data-provider", default=None, help="market provider: inmemory|alpaca")
    resolve.add_argument("--job-executor-mode", default=None, help="job executor mode: inprocess|celery-adapter")
    resolve.add_argument("--enabled-contexts", nargs="*", default=None, help="上下文列表")

    return parser


_COMMANDS = {
    "resolve-settings": _cmd_resolve_settings,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result = _COMMANDS[args.command](args)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
