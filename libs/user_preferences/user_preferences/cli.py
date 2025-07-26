"""user-preferences CLI 入口。

遵循 CLI Mandate：
- 接受 stdin / args / files 输入
- stdout 输出
- 支持 JSON 格式

子命令：default / migrate
"""

from __future__ import annotations

import argparse
import json
import sys

from user_preferences.domain import Preferences, default_preferences, migrate_preferences


def _cmd_default(_: argparse.Namespace) -> dict:
    prefs = default_preferences()
    return {"success": True, "data": prefs.model_dump(by_alias=True, exclude_none=True)}


def _cmd_migrate(args: argparse.Namespace) -> dict:
    if args.file:
        raw = args.file.read()
    else:
        raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    prefs = Preferences.model_validate(payload)
    migrated = migrate_preferences(prefs)
    return {"success": True, "data": migrated.model_dump(by_alias=True, exclude_none=True)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="user-preferences",
        description="QuantPoly 用户偏好设置 CLI",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("default", help="输出默认 preferences（JSON）")

    mig = sub.add_parser("migrate", help="迁移输入 preferences 到当前版本")
    mig.add_argument(
        "--file",
        type=argparse.FileType("r"),
        default=None,
        help="输入 JSON 文件路径（省略则从 stdin 读取）",
    )

    return parser


_COMMANDS = {
    "default": _cmd_default,
    "migrate": _cmd_migrate,
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

    result = handler(args)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
