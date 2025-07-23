"""monitoring-realtime CLI 入口。

遵循 CLI Mandate：
- 接受 stdin / args / files 输入
- stdout 输出
- 支持 JSON 格式

当前提供最小可观测能力：输出监控 heartbeat 消息。
"""

from __future__ import annotations

import argparse
import json
import sys
import time


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _cmd_heartbeat(args: argparse.Namespace) -> dict:
    ts = int(args.ts) if args.ts is not None else int(time.time())
    return {"success": True, "data": {"type": "monitor.heartbeat", "ts": ts}}


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

    return parser


_COMMANDS = {
    "heartbeat": _cmd_heartbeat,
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

