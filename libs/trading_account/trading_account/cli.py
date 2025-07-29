"""trading_account CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import AccountAccessDeniedError, TradingAccountService

_repo = InMemoryTradingAccountRepository()
_service = TradingAccountService(repository=_repo)


def _output(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _dt(value: datetime) -> str:
    return value.isoformat()


def _serialize_account(account) -> dict:
    return {
        "id": account.id,
        "userId": account.user_id,
        "accountName": account.account_name,
        "isActive": account.is_active,
        "createdAt": _dt(account.created_at),
    }


def _cmd_account_list(args: argparse.Namespace) -> None:
    accounts = _service.list_accounts(user_id=args.user_id)
    _output({"success": True, "data": [_serialize_account(item) for item in accounts]})


def _cmd_position_summary(args: argparse.Namespace) -> None:
    try:
        summary = _service.position_summary(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "ACCOUNT_ACCESS_DENIED",
                    "message": "account does not belong to current user",
                },
            }
        )
        return

    _output({"success": True, "data": summary})


def _cmd_trade_stats(args: argparse.Namespace) -> None:
    try:
        stats = _service.trade_stats(user_id=args.user_id, account_id=args.account_id)
    except AccountAccessDeniedError:
        _output(
            {
                "success": False,
                "error": {
                    "code": "ACCOUNT_ACCESS_DENIED",
                    "message": "account does not belong to current user",
                },
            }
        )
        return

    _output({"success": True, "data": stats})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading-account", description="QuantPoly 交易账户 CLI")
    sub = parser.add_subparsers(dest="command")

    account_list = sub.add_parser("account-list", help="查询用户账户列表")
    account_list.add_argument("--user-id", required=True)

    position_summary = sub.add_parser("position-summary", help="查询账户持仓分析")
    position_summary.add_argument("--user-id", required=True)
    position_summary.add_argument("--account-id", required=True)

    trade_stats = sub.add_parser("trade-stats", help="查询账户交易统计")
    trade_stats.add_argument("--user-id", required=True)
    trade_stats.add_argument("--account-id", required=True)

    return parser


_COMMANDS = {
    "account-list": _cmd_account_list,
    "position-summary": _cmd_position_summary,
    "trade-stats": _cmd_trade_stats,
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
