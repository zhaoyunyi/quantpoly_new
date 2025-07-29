"""交易账户应用服务。"""

from __future__ import annotations

from trading_account.domain import Position, TradeRecord, TradingAccount
from trading_account.repository import InMemoryTradingAccountRepository


class AccountAccessDeniedError(PermissionError):
    """访问不属于当前用户的账户。"""


class TradingAccountService:
    def __init__(self, *, repository: InMemoryTradingAccountRepository) -> None:
        self._repository = repository

    def create_account(self, *, user_id: str, account_name: str) -> TradingAccount:
        account = TradingAccount.create(user_id=user_id, account_name=account_name)
        self._repository.save_account(account)
        return account

    def list_accounts(self, *, user_id: str) -> list[TradingAccount]:
        return self._repository.list_accounts(user_id=user_id)

    def get_account(self, *, user_id: str, account_id: str) -> TradingAccount | None:
        return self._repository.get_account(account_id=account_id, user_id=user_id)

    def _assert_account_owner(self, *, user_id: str, account_id: str) -> None:
        account = self._repository.get_account(account_id=account_id, user_id=user_id)
        if account is None:
            raise AccountAccessDeniedError("无权访问该账户")

    def upsert_position(
        self,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        quantity: float,
        avg_price: float,
        last_price: float,
    ) -> Position:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        position = Position.create(
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            avg_price=avg_price,
            last_price=last_price,
        )
        self._repository.save_position(position)
        return position

    def list_positions(self, *, user_id: str, account_id: str) -> list[Position]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.list_positions(account_id=account_id, user_id=user_id)

    def record_trade(
        self,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> TradeRecord:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        trade = TradeRecord.create(
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
        )
        self._repository.save_trade(trade)
        return trade

    def position_summary(self, *, user_id: str, account_id: str) -> dict:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        positions = self._repository.list_positions(account_id=account_id, user_id=user_id)
        total_market_value = sum(item.quantity * item.last_price for item in positions)
        total_cost = sum(item.quantity * item.avg_price for item in positions)
        unrealized_pnl = total_market_value - total_cost
        return {
            "positionCount": len(positions),
            "totalMarketValue": total_market_value,
            "unrealizedPnl": unrealized_pnl,
        }

    def trade_stats(self, *, user_id: str, account_id: str) -> dict:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        trades = self._repository.list_trades(account_id=account_id, user_id=user_id)
        turnover = sum(item.quantity * item.price for item in trades)
        return {
            "tradeCount": len(trades),
            "turnover": turnover,
        }
