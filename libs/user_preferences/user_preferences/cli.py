"""user-preferences CLI 入口。

遵循 CLI Mandate：
- 接受 stdin / args / files 输入
- stdout 输出
- 支持 JSON 格式

子命令：
- default / migrate
- get / update / export / import
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, TextIO

from user_preferences.domain import (
    AdvancedPreferencesPermissionError,
    PreferencesValidationError,
    apply_patch,
    default_preferences,
    filter_for_user,
    migrate_preferences,
)
from user_preferences.store import InMemoryPreferencesStore, PreferencesStore
from user_preferences.store_sqlite import SQLitePreferencesStore


def _resolve_store(*, db_path: str | None) -> PreferencesStore:
    if db_path:
        return SQLitePreferencesStore(db_path=db_path)
    return InMemoryPreferencesStore()


def _read_json_payload(
    *,
    inline_json: str | None,
    file_obj: TextIO | None,
    allow_empty: bool,
) -> dict[str, Any]:
    if inline_json is not None and file_obj is not None:
        raise ValueError("use either --patch or --file")

    if inline_json is not None:
        raw = inline_json
    elif file_obj is not None:
        raw = file_obj.read()
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        if allow_empty:
            return {}
        raise ValueError("empty json payload")

    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("json payload must be object")
    return parsed


def _error(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": {"code": code, "message": message}}


def _success_preferences(preferences, *, user_level: int) -> dict[str, Any]:
    filtered = filter_for_user(preferences, user_level=user_level)
    return {
        "success": True,
        "data": filtered.model_dump(by_alias=True, exclude_none=True),
    }


def _cmd_default(_: argparse.Namespace) -> dict[str, Any]:
    prefs = default_preferences()
    return {"success": True, "data": prefs.model_dump(by_alias=True, exclude_none=True)}


def _cmd_migrate(args: argparse.Namespace) -> dict[str, Any]:
    try:
        payload = _read_json_payload(
            inline_json=None,
            file_obj=args.file,
            allow_empty=True,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return _error("INVALID_JSON", str(exc))

    migrated = migrate_preferences(payload)
    return {"success": True, "data": migrated.model_dump(by_alias=True, exclude_none=True)}


def _cmd_get(args: argparse.Namespace) -> dict[str, Any]:
    store = _resolve_store(db_path=args.db_path)
    prefs = store.get_or_create(args.user_id)
    return _success_preferences(prefs, user_level=args.user_level)


def _cmd_update(args: argparse.Namespace) -> dict[str, Any]:
    store = _resolve_store(db_path=args.db_path)
    current = store.get_or_create(args.user_id)

    try:
        patch_payload = _read_json_payload(
            inline_json=args.patch,
            file_obj=args.file,
            allow_empty=False,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return _error("INVALID_JSON", str(exc))

    try:
        updated = apply_patch(current, patch_payload, user_level=args.user_level)
    except AdvancedPreferencesPermissionError as exc:
        return _error("ADVANCED_PERMISSION_DENIED", str(exc))
    except PreferencesValidationError as exc:
        return _error("INVALID_PREFERENCES", str(exc))

    store.set(args.user_id, updated)
    return _success_preferences(updated, user_level=args.user_level)


def _cmd_export(args: argparse.Namespace) -> dict[str, Any]:
    store = _resolve_store(db_path=args.db_path)
    prefs = store.get_or_create(args.user_id)
    return _success_preferences(prefs, user_level=args.user_level)


def _cmd_import(args: argparse.Namespace) -> dict[str, Any]:
    store = _resolve_store(db_path=args.db_path)

    try:
        payload = _read_json_payload(
            inline_json=None,
            file_obj=args.file,
            allow_empty=False,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return _error("INVALID_JSON", str(exc))

    try:
        imported = migrate_preferences(payload)
    except Exception as exc:  # noqa: BLE001
        return _error("INVALID_PREFERENCES", str(exc))

    if imported.advanced is not None and args.user_level < 2:
        return _error("ADVANCED_PERMISSION_DENIED", "advanced requires elevated user level")

    store.set(args.user_id, imported)
    return _success_preferences(imported, user_level=args.user_level)


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

    get_cmd = sub.add_parser("get", help="读取用户偏好")
    get_cmd.add_argument("--user-id", required=True)
    get_cmd.add_argument("--user-level", type=int, default=1)
    get_cmd.add_argument("--db-path", default=None)

    update_cmd = sub.add_parser("update", help="更新用户偏好（深度合并）")
    update_cmd.add_argument("--user-id", required=True)
    update_cmd.add_argument("--user-level", type=int, default=1)
    update_cmd.add_argument("--db-path", default=None)
    update_cmd.add_argument("--patch", default=None, help="内联 JSON patch")
    update_cmd.add_argument(
        "--file",
        type=argparse.FileType("r"),
        default=None,
        help="JSON patch 文件路径（省略则从 stdin 读取）",
    )

    export_cmd = sub.add_parser("export", help="导出用户偏好 JSON")
    export_cmd.add_argument("--user-id", required=True)
    export_cmd.add_argument("--user-level", type=int, default=1)
    export_cmd.add_argument("--db-path", default=None)

    import_cmd = sub.add_parser("import", help="导入用户偏好 JSON")
    import_cmd.add_argument("--user-id", required=True)
    import_cmd.add_argument("--user-level", type=int, default=1)
    import_cmd.add_argument("--db-path", default=None)
    import_cmd.add_argument(
        "--file",
        type=argparse.FileType("r"),
        default=None,
        help="输入 JSON 文件路径（省略则从 stdin 读取）",
    )

    return parser


_COMMANDS = {
    "default": _cmd_default,
    "migrate": _cmd_migrate,
    "get": _cmd_get,
    "update": _cmd_update,
    "export": _cmd_export,
    "import": _cmd_import,
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
