"""user-auth CLI 入口。

遵循 CLI Mandate：
- 接受 stdin / args / files 输入
- stdout 输出
- 支持 JSON 格式

子命令：register / login / verify / logout
"""
import argparse
import json
import sys

from user_auth.domain import User, PasswordTooWeakError
from user_auth.session import Session, SessionStore
from user_auth.repository import UserRepository

# CLI 使用内存存储（每次运行独立）
_repo = UserRepository()
_sessions = SessionStore()


def _output(data: dict) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


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


def _cmd_login(args: argparse.Namespace) -> None:
    user = _repo.get_by_email(args.email)
    if user is None or not user.authenticate(args.password):
        _output({"success": False, "error": {"code": "INVALID_CREDENTIALS", "message": "Invalid credentials"}})
        return
    session = Session.create(user_id=user.id)
    _sessions.save(session)
    _output({"success": True, "data": {"token": session.token}})


def _cmd_verify(args: argparse.Namespace) -> None:
    session = _sessions.get_by_token(args.token)
    if session is None:
        _output({"success": False, "error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})
        return
    user = _repo.get_by_id(session.user_id)
    if user is None:
        _output({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "User not found"}})
        return
    _output({"success": True, "data": {"userId": user.id, "email": user.email}})


def _cmd_logout(args: argparse.Namespace) -> None:
    session = _sessions.get_by_token(args.token)
    if session is None:
        _output({"success": False, "error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})
        return
    _sessions.revoke(args.token)
    _output({"success": True, "message": "Logged out"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="user-auth",
        description="QuantPoly 用户认证 CLI",
    )
    sub = parser.add_subparsers(dest="command")

    reg = sub.add_parser("register", help="注册用户")
    reg.add_argument("--email", required=True)
    reg.add_argument("--password", required=True)

    login = sub.add_parser("login", help="登录")
    login.add_argument("--email", required=True)
    login.add_argument("--password", required=True)

    verify = sub.add_parser("verify", help="验证 token")
    verify.add_argument("--token", required=True)

    logout = sub.add_parser("logout", help="登出")
    logout.add_argument("--token", required=True)

    return parser


_COMMANDS = {
    "register": _cmd_register,
    "login": _cmd_login,
    "verify": _cmd_verify,
    "logout": _cmd_logout,
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

    handler(args)


if __name__ == "__main__":
    main()
