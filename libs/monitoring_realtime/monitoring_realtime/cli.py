"""monitoring-realtime CLI 入口。

遵循 CLI Mandate：
- 接受 stdin / args / files 输入
- stdout 输出
- 支持 JSON 格式

命令：
- heartbeat: 输出最小心跳消息（可用于门禁/探活）
- summary: 从 snapshot JSON 复算运营摘要（Read Model）
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from monitoring_realtime.read_model import build_operational_summary_from_snapshot


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _cmd_heartbeat(args: argparse.Namespace) -> dict:
    ts = int(args.ts) if args.ts is not None else int(time.time())
    return {"success": True, "data": {"type": "monitor.heartbeat", "ts": ts}}


def _cmd_summary(args: argparse.Namespace) -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        snapshot: object = {}
    else:
        try:
            snapshot = json.loads(raw)
        except json.JSONDecodeError as exc:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_JSON",
                    "message": f"invalid json: {exc}",
                },
            }

    if not isinstance(snapshot, dict):
        return {
            "success": False,
            "error": {
                "code": "INVALID_SNAPSHOT",
                "message": "snapshot must be a json object",
            },
        }

    for key in ("accounts", "strategies", "backtests", "tasks", "signals", "alerts"):
        if key in snapshot and not isinstance(snapshot[key], list):
            return {
                "success": False,
                "error": {
                    "code": "INVALID_SNAPSHOT",
                    "message": f"snapshot.{key} must be a json array",
                },
            }

    started_at = time.perf_counter()
    summary = build_operational_summary_from_snapshot(
        user_id=str(args.user_id),
        snapshot=snapshot,
        latency_ms=max(0, int((time.perf_counter() - started_at) * 1000)),
    )
    return {"success": True, "data": summary}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="monitoring-realtime",
        description="QuantPoly 实时监控（WebSocket）库 CLI",
    )
    sub = parser.add_subparsers(dest="command")

    heartbeat = sub.add_parser("heartbeat", help="输出 heartbeat 消息")
    heartbeat.add_argument(
        "--ts",
        default=None,
        help="指定时间戳（秒）。省略则使用当前时间。",
    )

    summary = sub.add_parser("summary", help="从 snapshot JSON 复算运营摘要")
    summary.add_argument(
        "--user-id",
        required=True,
        help="当前用户 id（用于过滤 snapshot 数据范围）",
    )

    return parser


_COMMANDS = {
    "heartbeat": _cmd_heartbeat,
    "summary": _cmd_summary,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    _output(handler(args))


if __name__ == "__main__":
    main()
