"""user-auth CLI 入口。

遵循 CLI Mandate：
- 接受 stdin / args / files 输入
- stdout 输出
- 支持 JSON 格式

子命令：register / login / verify / logout / update-me / change-password / admin-list-users / admin-update-user
"""

from __future__ import annotations

import argparse
import json
import sys

from user_auth.domain import PasswordTooWeakError, User
from user_auth.repository import UserRepository
from user_auth.session import Session, SessionStore
from user_auth.token import extract_session_token

# CLI 使用内存存储（每次运行独立）
_repo = UserRepository()
_sessions = SessionStore()


def _output(data: dict) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _get_current_user_by_token(token: str):
    parsed_token = extract_session_token(
        headers={"Authorization": f"Bearer {token}"},
        cookies={},
    )
    session = _sessions.get_by_token(parsed_token or "")
    if session is None:
        return None, None

    user = _repo.get_by_id(session.user_id)
    if user is None:
        return None, None

    return user, parsed_token


def _require_admin(token: str):
    user, parsed_token = _get_current_user_by_token(token)
    if user is None:
        _output({"success": False, "error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})
        return None, None

    if user.role != "admin":
        _output({"success": False, "error": {"code": "ADMIN_REQUIRED", "message": "admin role required"}})
        return None, None

    return user, parsed_token


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "displayName": user.display_name,
        "isActive": user.is_active,
        "emailVerified": user.email_verified,
        "role": user.role,
        "level": user.level,
    }


def _cmd_register(args: argparse.Namespace) -> None:
    if _repo.email_exists(args.email):
        _output({"success": False, "error": {"code": "DUPLICATE_EMAIL", "message": "Email already registered"}})
        return
    try:
        user = User.register(email=args.email, password=args.password)
    except PasswordTooWeakError as e:
        _output({"success": False, "error": {"code": "WEAK_PASSWORD", "message": str(e)}})
        return
    _repo.save(user)
    _output({"success": True, "data": {"userId": user.id, "email": user.email}})


def _cmd_verify_email(args: argparse.Namespace) -> None:
    user = _repo.get_by_email(args.email)
    if user is None:
        _output({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "User not found"}})
        return
    user.verify_email()
    _repo.save(user)
    _output({"success": True, "message": "Email verified"})


def _cmd_login(args: argparse.Namespace) -> None:
    user = _repo.get_by_email(args.email)
    if user is None or not user.authenticate(args.password):
        _output({"success": False, "error": {"code": "INVALID_CREDENTIALS", "message": "Invalid credentials"}})
        return
    if not user.email_verified:
        _output({"success": False, "error": {"code": "EMAIL_NOT_VERIFIED", "message": "EMAIL_NOT_VERIFIED"}})
        return
    if not user.is_active:
        _output({"success": False, "error": {"code": "USER_DISABLED", "message": "USER_DISABLED"}})
        return
    session = Session.create(user_id=user.id)
    _sessions.save(session)
    _output({"success": True, "data": {"token": session.token}})


def _cmd_verify(args: argparse.Namespace) -> None:
    user, _ = _get_current_user_by_token(args.token)
    if user is None:
        _output({"success": False, "error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})
        return
    _output({"success": True, "data": {"userId": user.id, "email": user.email}})


def _cmd_logout(args: argparse.Namespace) -> None:
    user, parsed_token = _get_current_user_by_token(args.token)
    if user is None:
        _output({"success": False, "error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})
        return
    _sessions.revoke(parsed_token or "")
    _output({"success": True, "message": "Logged out"})


def _cmd_update_me(args: argparse.Namespace) -> None:
    user, _ = _get_current_user_by_token(args.token)
    if user is None:
        _output({"success": False, "error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})
        return

    if args.email is not None and args.email != user.email:
        existing = _repo.get_by_email(args.email)
        if existing is not None and existing.id != user.id:
            _output({"success": False, "error": {"code": "DUPLICATE_EMAIL", "message": "email already exists"}})
            return

    user.update_profile(email=args.email, display_name=args.display_name)
    _repo.save(user)
    _output({"success": True, "data": _user_payload(user)})


def _cmd_change_password(args: argparse.Namespace) -> None:
    user, _ = _get_current_user_by_token(args.token)
    if user is None:
        _output({"success": False, "error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})
        return

    try:
        user.change_password(
            current_password=args.current_password,
            new_password=args.new_password,
        )
    except PasswordTooWeakError as exc:
        _output({"success": False, "error": {"code": "WEAK_PASSWORD", "message": str(exc)}})
        return
    except ValueError as exc:
        _output({"success": False, "error": {"code": "PASSWORD_CHANGE_INVALID", "message": str(exc)}})
        return

    _repo.save(user)
    revoke_all_sessions = getattr(args, "revoke_all_sessions", True)
    revoked = 0
    if revoke_all_sessions:
        revoked = _sessions.revoke_by_user(user_id=user.id)

    _output({"success": True, "data": {"revokedSessions": revoked}})


def _cmd_admin_list_users(args: argparse.Namespace) -> None:
    _admin, _ = _require_admin(args.token)
    if _admin is None:
        return

    result = _repo.list_users(status=args.status, page=args.page, page_size=args.page_size)
    _output(
        {
            "success": True,
            "data": {
                "items": [_user_payload(item) for item in result["items"]],
                "total": result["total"],
                "page": result["page"],
                "pageSize": result["pageSize"],
            },
        }
    )


def _cmd_admin_update_user(args: argparse.Namespace) -> None:
    _admin, _ = _require_admin(args.token)
    if _admin is None:
        return

    target = _repo.get_by_id(args.user_id)
    if target is None:
        _output({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "user not found"}})
        return

    try:
        if args.email is not None and args.email != target.email:
            existing = _repo.get_by_email(args.email)
            if existing is not None and existing.id != target.id:
                _output({"success": False, "error": {"code": "DUPLICATE_EMAIL", "message": "email already exists"}})
                return

        if args.email is not None or args.display_name is not None:
            target.update_profile(email=args.email, display_name=args.display_name)
        if args.role is not None:
            target.set_role(args.role)
        if args.level is not None:
            target.set_level(args.level)
        if args.is_active is not None:
            if args.is_active:
                target.enable()
            else:
                target.disable()
    except ValueError as exc:
        _output({"success": False, "error": {"code": "USER_UPDATE_INVALID", "message": str(exc)}})
        return

    _repo.save(target)
    if args.is_active is False:
        _sessions.revoke_by_user(user_id=target.id)

    _output({"success": True, "data": _user_payload(target)})


def _cmd_delete_me(args: argparse.Namespace) -> None:
    user, _ = _get_current_user_by_token(args.token)
    if user is None:
        _output({"success": False, "error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})
        return

    deleted = _repo.delete(user.id)
    revoked = _sessions.revoke_by_user(user_id=user.id)
    if not deleted:
        _output({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "user not found"}})
        return

    _output({"success": True, "data": {"userId": user.id, "revokedSessions": revoked}, "message": "User deleted"})


def _cmd_admin_get_user(args: argparse.Namespace) -> None:
    _admin, _ = _require_admin(args.token)
    if _admin is None:
        return

    target = _repo.get_by_id(args.user_id)
    if target is None:
        _output({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "user not found"}})
        return

    _output({"success": True, "data": _user_payload(target)})


def _cmd_admin_delete_user(args: argparse.Namespace) -> None:
    _admin, _ = _require_admin(args.token)
    if _admin is None:
        return

    target = _repo.get_by_id(args.user_id)
    if target is None:
        _output({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "user not found"}})
        return

    deleted = _repo.delete(args.user_id)
    revoked = _sessions.revoke_by_user(user_id=args.user_id)
    if not deleted:
        _output({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "user not found"}})
        return

    _output({
        "success": True,
        "data": {
            "userId": args.user_id,
            "revokedSessions": revoked,
        },
        "message": "User deleted",
    })


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="user-auth",
        description="QuantPoly 用户认证 CLI",
    )
    sub = parser.add_subparsers(dest="command")

    reg = sub.add_parser("register", help="注册用户")
    reg.add_argument("--email", required=True)
    reg.add_argument("--password", required=True)

    verify_email = sub.add_parser("verify-email", help="验证邮箱")
    verify_email.add_argument("--email", required=True)

    login = sub.add_parser("login", help="登录")
    login.add_argument("--email", required=True)
    login.add_argument("--password", required=True)

    verify = sub.add_parser("verify", help="验证 token")
    verify.add_argument("--token", required=True)

    logout = sub.add_parser("logout", help="登出")
    logout.add_argument("--token", required=True)

    update_me = sub.add_parser("update-me", help="更新当前用户资料")
    update_me.add_argument("--token", required=True)
    update_me.add_argument("--email", default=None)
    update_me.add_argument("--display-name", default=None)

    change_password = sub.add_parser("change-password", help="修改当前用户密码")
    change_password.add_argument("--token", required=True)
    change_password.add_argument("--current-password", required=True)
    change_password.add_argument("--new-password", required=True)
    change_password.add_argument("--no-revoke-all-sessions", action="store_false", dest="revoke_all_sessions")
    change_password.set_defaults(revoke_all_sessions=True)

    admin_list = sub.add_parser("admin-list-users", help="管理员查询用户")
    admin_list.add_argument("--token", required=True)
    admin_list.add_argument("--status", choices=["active", "disabled"], default=None)
    admin_list.add_argument("--page", type=int, default=1)
    admin_list.add_argument("--page-size", type=int, default=20)

    admin_update = sub.add_parser("admin-update-user", help="管理员更新用户")
    admin_update.add_argument("--token", required=True)
    admin_update.add_argument("--user-id", required=True)
    admin_update.add_argument("--email", default=None)
    admin_update.add_argument("--display-name", default=None)
    admin_update.add_argument("--role", choices=["user", "admin"], default=None)
    admin_update.add_argument("--level", type=int, default=None)
    admin_update.add_argument("--is-active", choices=["true", "false"], default=None)

    delete_me = sub.add_parser("delete-me", help="当前用户自助注销")
    delete_me.add_argument("--token", required=True)

    admin_get = sub.add_parser("admin-get-user", help="管理员查询单个用户")
    admin_get.add_argument("--token", required=True)
    admin_get.add_argument("--user-id", required=True)

    admin_delete = sub.add_parser("admin-delete-user", help="管理员删除用户")
    admin_delete.add_argument("--token", required=True)
    admin_delete.add_argument("--user-id", required=True)

    return parser


_COMMANDS = {
    "register": _cmd_register,
    "verify-email": _cmd_verify_email,
    "login": _cmd_login,
    "verify": _cmd_verify,
    "logout": _cmd_logout,
    "update-me": _cmd_update_me,
    "change-password": _cmd_change_password,
    "admin-list-users": _cmd_admin_list_users,
    "admin-update-user": _cmd_admin_update_user,
    "delete-me": _cmd_delete_me,
    "admin-get-user": _cmd_admin_get_user,
    "admin-delete-user": _cmd_admin_delete_user,
}


def _normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    if hasattr(args, "is_active") and isinstance(args.is_active, str):
        args.is_active = args.is_active == "true"
    if hasattr(args, "revoke_all_sessions") and args.command == "change-password":
        args.revoke_all_sessions = bool(args.revoke_all_sessions)
    return args


def main() -> None:
    parser = build_parser()
    args = _normalize_args(parser.parse_args())

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
