"""platform-core CLI 入口。

遵循 CLI Mandate：
- 接受 stdin / args / files 输入
- stdout 输出
- 支持 JSON 格式
"""
import argparse
import json
import sys

from platform_core.config import Settings, EnvironmentType
from platform_core.logging import mask_sensitive
from platform_core.response import success_response, error_response


def _cmd_config(args: argparse.Namespace) -> dict:
    """输出当前配置（脱敏）。"""
    settings = Settings() if args.env_file is None else Settings(_env_file=args.env_file)
    data = {
        "environment": settings.environment.value,
        "debug": settings.debug,
        "secret_key_set": bool(settings.secret_key),
    }
    return success_response(data=data, message="config loaded")


def _cmd_validate(args: argparse.Namespace) -> dict:
    """校验配置安全性。"""
    settings = Settings() if args.env_file is None else Settings(_env_file=args.env_file)
    try:
        settings.validate_security()
        return success_response(message="configuration is valid")
    except ValueError as e:
        return error_response(
            code="CONFIG_VALIDATION_ERROR",
            message=str(e),
        )


def _cmd_mask(args: argparse.Namespace) -> dict:
    """对输入文本进行脱敏。"""
    if args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()
    masked = mask_sensitive(text)
    return success_response(data={"masked": masked})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="platform-core",
        description="QuantPoly 平台核心库 CLI",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="指定 .env 文件路径",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("config", help="输出当前配置（脱敏）")
    sub.add_parser("validate", help="校验配置安全性")

    mask_parser = sub.add_parser("mask", help="对文本进行脱敏")
    mask_parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="待脱敏文本（省略则从 stdin 读取）",
    )

    return parser


_COMMANDS = {
    "config": _cmd_config,
    "validate": _cmd_validate,
    "mask": _cmd_mask,
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
