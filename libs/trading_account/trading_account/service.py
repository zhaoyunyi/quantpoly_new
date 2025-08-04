"""交易账户应用服务。"""

from __future__ import annotations

from trading_account.domain import (
    CashFlow,
    InvalidTradeOrderTransitionError,
    Position,
    TradeOrder,
    TradeRecord,
    TradingAccount,
)
from trading_account.repository import InMemoryTradingAccountRepository


class AccountAccessDeniedError(PermissionError):
    """访问不属于当前用户的账户。"""


class OrderNotFoundError(LookupError):
    """订单不存在。"""


class TradeNotFoundError(LookupError):
    """成交记录不存在。"""


class InsufficientFundsError(ValueError):
    """可用资金不足。"""


class LedgerTransactionError(RuntimeError):
    """账本事务失败。"""


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

    def submit_order(
        self,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> TradeOrder:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        order = TradeOrder.create(
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
        )
        self._repository.save_order(order)
        return order

    def get_order(self, *, user_id: str, account_id: str, order_id: str) -> TradeOrder | None:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.get_order(account_id=account_id, user_id=user_id, order_id=order_id)

    def list_orders(self, *, user_id: str, account_id: str) -> list[TradeOrder]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.list_orders(account_id=account_id, user_id=user_id)

    def _transition_order_or_raise(
        self,
        *,
        user_id: str,
        account_id: str,
        order_id: str,
        from_status: str,
        to_status: str,
    ) -> TradeOrder:
        existing = self._repository.get_order(account_id=account_id, user_id=user_id, order_id=order_id)
        if existing is None:
            raise OrderNotFoundError("order not found")

        transitioned = self._repository.transition_order_status(
            account_id=account_id,
            user_id=user_id,
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
        )
        if transitioned is None:
            raise InvalidTradeOrderTransitionError(
                f"invalid transition: {existing.status} -> {to_status}"
            )
        return transitioned

    def fill_order(self, *, user_id: str, account_id: str, order_id: str) -> TradeOrder:
        self._assert_account_owner(user_id=user_id, account_id=account_id)

        order = self._transition_order_or_raise(
            user_id=user_id,
            account_id=account_id,
            order_id=order_id,
            from_status="pending",
            to_status="filled",
        )

        trade = TradeRecord.create(
            user_id=order.user_id,
            account_id=order.account_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            order_id=order.id,
        )

        notional = order.quantity * order.price
        signed_amount = -notional if order.side == "BUY" else notional
        flow = CashFlow.create(
            user_id=order.user_id,
            account_id=order.account_id,
            amount=signed_amount,
            flow_type=f"trade_{order.side.lower()}",
            related_trade_id=trade.id,
        )

        try:
            self._repository.save_trade(trade)
            self._repository.save_cash_flow(flow)
        except Exception as exc:
            self._repository.delete_trade(trade_id=trade.id)
            self._repository.delete_cash_flow(cash_flow_id=flow.id)
            self._repository.transition_order_status(
                account_id=account_id,
                user_id=user_id,
                order_id=order_id,
                from_status="filled",
                to_status="pending",
            )
            raise LedgerTransactionError("ledger transaction failed") from exc

        return order

    def cancel_order(self, *, user_id: str, account_id: str, order_id: str) -> TradeOrder:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._transition_order_or_raise(
            user_id=user_id,
            account_id=account_id,
            order_id=order_id,
            from_status="pending",
            to_status="cancelled",
        )

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

    def get_trade(self, *, user_id: str, account_id: str, trade_id: str) -> TradeRecord:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        trade = self._repository.get_trade(account_id=account_id, user_id=user_id, trade_id=trade_id)
        if trade is None:
            raise TradeNotFoundError("trade not found")
        return trade

    def list_trades(self, *, user_id: str, account_id: str) -> list[TradeRecord]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.list_trades(account_id=account_id, user_id=user_id)

    def deposit(self, *, user_id: str, account_id: str, amount: float) -> CashFlow:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        if amount <= 0:
            raise ValueError("amount must be positive")

        flow = CashFlow.create(
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            flow_type="deposit",
        )
        self._repository.save_cash_flow(flow)
        return flow

    def withdraw(self, *, user_id: str, account_id: str, amount: float) -> CashFlow:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        if amount <= 0:
            raise ValueError("amount must be positive")

        current_balance = self.cash_balance(user_id=user_id, account_id=account_id)
        if current_balance < amount:
            raise InsufficientFundsError("insufficient funds")

        flow = CashFlow.create(
            user_id=user_id,
            account_id=account_id,
            amount=-amount,
            flow_type="withdraw",
        )
        self._repository.save_cash_flow(flow)
        return flow

    def list_cash_flows(self, *, user_id: str, account_id: str) -> list[CashFlow]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.list_cash_flows(account_id=account_id, user_id=user_id)

    def cash_balance(self, *, user_id: str, account_id: str) -> float:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        flows = self._repository.list_cash_flows(account_id=account_id, user_id=user_id)
        return sum(item.amount for item in flows)

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

    def account_overview(self, *, user_id: str, account_id: str) -> dict:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        order_list = self._repository.list_orders(account_id=account_id, user_id=user_id)
        position_metrics = self.position_summary(user_id=user_id, account_id=account_id)
        trade_metrics = self.trade_stats(user_id=user_id, account_id=account_id)
        cash_balance = self.cash_balance(user_id=user_id, account_id=account_id)

        status_counts = {
            "pendingOrderCount": 0,
            "filledOrderCount": 0,
            "cancelledOrderCount": 0,
            "failedOrderCount": 0,
        }
        for item in order_list:
            key = f"{item.status}OrderCount"
            if key in status_counts:
                status_counts[key] += 1

        return {
            **position_metrics,
            **trade_metrics,
            "orderCount": len(order_list),
            **status_counts,
            "cashBalance": cash_balance,
        }
