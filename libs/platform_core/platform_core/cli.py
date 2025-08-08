"""platform-core CLI 入口。

遵循 CLI Mandate：
- 接受 stdin / args / files 输入
- stdout 输出
- 支持 JSON 格式
"""
import argparse
import json
import sys

from platform_core.capability_gate import evaluate_gate
from platform_core.config import Settings
from platform_core.logging import mask_sensitive
from platform_core.response import error_response, success_response


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


def _load_json_input(*, input_file: str | None) -> dict:
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            return json.load(f)

    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("capability gate input is empty")
    return json.loads(raw)


def _cmd_capability_gate(args: argparse.Namespace) -> dict:
    """执行能力门禁校验。"""
    try:
        payload = _load_json_input(input_file=args.input_file)
        result = evaluate_gate(payload)
        return success_response(data=result, message="capability gate evaluated")
    except (ValueError, json.JSONDecodeError) as exc:
        return error_response(code="CAPABILITY_GATE_INVALID_INPUT", message=str(exc))


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

    capability_gate = sub.add_parser("capability-gate", help="执行能力门禁校验")
    capability_gate.add_argument(
        "--input-file",
        default=None,
        help="能力门禁输入 JSON 文件路径（省略时读取 stdin）",
    )

    return parser


_COMMANDS = {
    "config": _cmd_config,
    "validate": _cmd_validate,
    "mask": _cmd_mask,
    "capability-gate": _cmd_capability_gate,
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
