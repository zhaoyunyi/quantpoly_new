"""交易账户应用服务。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from platform_core.uow import NoopUnitOfWork, SnapshotUnitOfWork, UnitOfWork
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


def _default_uow_factory(repository: Any) -> Callable[[], UnitOfWork]:
    if hasattr(repository, "snapshot_state") and hasattr(repository, "restore_state"):
        return lambda: SnapshotUnitOfWork(
            snapshot=repository.snapshot_state,
            restore=repository.restore_state,
        )
    return NoopUnitOfWork


class TradingAccountService:
    def __init__(
        self,
        *,
        repository: InMemoryTradingAccountRepository,
        uow_factory: Callable[[], UnitOfWork] | None = None,
    ) -> None:
        self._repository = repository
        self._uow_factory = uow_factory or _default_uow_factory(repository)

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

        deferred_transition_error: InvalidTradeOrderTransitionError | None = None
        filled_order: TradeOrder | None = None

        try:
            with self._uow_factory() as uow:
                try:
                    filled_order = self._transition_order_or_raise(
                        user_id=user_id,
                        account_id=account_id,
                        order_id=order_id,
                        from_status="pending",
                        to_status="filled",
                    )
                except InvalidTradeOrderTransitionError as exc:
                    deferred_transition_error = exc
                    uow.commit()
                    filled_order = None

                if deferred_transition_error is not None:
                    return self._raise_transition_error(deferred_transition_error)

                trade = TradeRecord.create(
                    user_id=filled_order.user_id,
                    account_id=filled_order.account_id,
                    symbol=filled_order.symbol,
                    side=filled_order.side,
                    quantity=filled_order.quantity,
                    price=filled_order.price,
                    order_id=filled_order.id,
                )

                notional = filled_order.quantity * filled_order.price
                signed_amount = -notional if filled_order.side == "BUY" else notional
                flow = CashFlow.create(
                    user_id=filled_order.user_id,
                    account_id=filled_order.account_id,
                    amount=signed_amount,
                    flow_type=f"trade_{filled_order.side.lower()}",
                    related_trade_id=trade.id,
                )

                self._repository.save_trade(trade)
                self._repository.save_cash_flow(flow)

            if filled_order is None:
                raise RuntimeError("filled order missing")
            return filled_order
        except (AccountAccessDeniedError, OrderNotFoundError, InvalidTradeOrderTransitionError):
            raise
        except Exception as exc:  # noqa: BLE001
            raise LedgerTransactionError("ledger transaction failed") from exc

    @staticmethod
    def _raise_transition_error(exc: InvalidTradeOrderTransitionError) -> None:
        raise exc

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
