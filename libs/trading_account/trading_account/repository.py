"""交易账户 in-memory 仓储。"""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from trading_account.domain import CashFlow, Position, TradeOrder, TradeRecord, TradingAccount


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryTradingAccountRepository:
    def __init__(self) -> None:
        self._accounts: dict[str, TradingAccount] = {}
        self._positions: dict[tuple[str, str, str], Position] = {}
        self._orders: dict[str, TradeOrder] = {}
        self._trades: dict[str, TradeRecord] = {}
        self._cash_flows: dict[str, CashFlow] = {}
        self._lock = threading.RLock()

    def _clone_account(self, account: TradingAccount) -> TradingAccount:
        return TradingAccount(
            id=account.id,
            user_id=account.user_id,
            account_name=account.account_name,
            is_active=account.is_active,
            created_at=account.created_at,
        )

    def _clone_position(self, position: Position) -> Position:
        return Position(
            id=position.id,
            user_id=position.user_id,
            account_id=position.account_id,
            symbol=position.symbol,
            quantity=position.quantity,
            avg_price=position.avg_price,
            last_price=position.last_price,
        )

    def _clone_order(self, order: TradeOrder) -> TradeOrder:
        return TradeOrder(
            id=order.id,
            user_id=order.user_id,
            account_id=order.account_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    def _clone_trade(self, trade: TradeRecord) -> TradeRecord:
        return TradeRecord(
            id=trade.id,
            user_id=trade.user_id,
            account_id=trade.account_id,
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price,
            order_id=trade.order_id,
            created_at=trade.created_at,
        )

    def _clone_cash_flow(self, cash_flow: CashFlow) -> CashFlow:
        return CashFlow(
            id=cash_flow.id,
            user_id=cash_flow.user_id,
            account_id=cash_flow.account_id,
            amount=cash_flow.amount,
            flow_type=cash_flow.flow_type,
            related_trade_id=cash_flow.related_trade_id,
            created_at=cash_flow.created_at,
        )

    def snapshot_state(self) -> dict:
        with self._lock:
            return {
                "accounts": {key: self._clone_account(value) for key, value in self._accounts.items()},
                "positions": {key: self._clone_position(value) for key, value in self._positions.items()},
                "orders": {key: self._clone_order(value) for key, value in self._orders.items()},
                "trades": {key: self._clone_trade(value) for key, value in self._trades.items()},
                "cash_flows": {key: self._clone_cash_flow(value) for key, value in self._cash_flows.items()},
            }

    def restore_state(self, snapshot: dict) -> None:
        with self._lock:
            self._accounts = {key: self._clone_account(value) for key, value in snapshot["accounts"].items()}
            self._positions = {
                key: self._clone_position(value)
                for key, value in snapshot["positions"].items()
            }
            self._orders = {key: self._clone_order(value) for key, value in snapshot["orders"].items()}
            self._trades = {key: self._clone_trade(value) for key, value in snapshot["trades"].items()}
            self._cash_flows = {
                key: self._clone_cash_flow(value)
                for key, value in snapshot["cash_flows"].items()
            }

    def save_account(self, account: TradingAccount) -> None:
        with self._lock:
            self._accounts[account.id] = self._clone_account(account)

    def list_accounts(self, *, user_id: str) -> list[TradingAccount]:
        with self._lock:
            return [
                self._clone_account(account)
                for account in self._accounts.values()
                if account.user_id == user_id
            ]

    def get_account(self, *, account_id: str, user_id: str) -> TradingAccount | None:
        with self._lock:
            account = self._accounts.get(account_id)
            if account is None or account.user_id != user_id:
                return None
            return self._clone_account(account)

    def save_position(self, position: Position) -> None:
        with self._lock:
            key = (position.account_id, position.symbol, position.user_id)
            self._positions[key] = self._clone_position(position)

    def list_positions(self, *, account_id: str, user_id: str) -> list[Position]:
        with self._lock:
            return [
                self._clone_position(pos)
                for pos in self._positions.values()
                if pos.account_id == account_id and pos.user_id == user_id
            ]

    def refresh_position_prices(
        self,
        *,
        price_updates: dict[str, float],
        account_id: str | None = None,
        user_id: str | None = None,
    ) -> int:
        with self._lock:
            updated = 0
            for key, position in list(self._positions.items()):
                if account_id is not None and position.account_id != account_id:
                    continue
                if user_id is not None and position.user_id != user_id:
                    continue
                new_price = price_updates.get(position.symbol)
                if new_price is None:
                    continue

                cloned = self._clone_position(position)
                cloned.last_price = float(new_price)
                self._positions[key] = cloned
                updated += 1
            return updated

    def save_order(self, order: TradeOrder) -> None:
        with self._lock:
            self._orders[order.id] = self._clone_order(order)

    def delete_order(self, *, order_id: str) -> TradeOrder | None:
        with self._lock:
            existed = self._orders.pop(order_id, None)
            if existed is None:
                return None
            return self._clone_order(existed)

    def get_order(self, *, account_id: str, user_id: str, order_id: str) -> TradeOrder | None:
        with self._lock:
            order = self._orders.get(order_id)
            if order is None:
                return None
            if order.account_id != account_id or order.user_id != user_id:
                return None
            return self._clone_order(order)

    def list_orders(self, *, account_id: str, user_id: str) -> list[TradeOrder]:
        with self._lock:
            return [
                self._clone_order(order)
                for order in self._orders.values()
                if order.account_id == account_id and order.user_id == user_id
            ]

    def list_orders_by_status(
        self,
        *,
        status: str,
        account_id: str | None = None,
        user_id: str | None = None,
    ) -> list[TradeOrder]:
        with self._lock:
            return [
                self._clone_order(order)
                for order in self._orders.values()
                if order.status == status
                and (account_id is None or order.account_id == account_id)
                and (user_id is None or order.user_id == user_id)
            ]

    def transition_order_status(
        self,
        *,
        account_id: str,
        user_id: str,
        order_id: str,
        from_status: str,
        to_status: str,
    ) -> TradeOrder | None:
        with self._lock:
            order = self._orders.get(order_id)
            if order is None:
                return None
            if order.account_id != account_id or order.user_id != user_id:
                return None
            if order.status != from_status:
                return None

            updated = self._clone_order(order)
            updated.status = to_status
            updated.updated_at = _utc_now()
            self._orders[order_id] = updated
            return self._clone_order(updated)

    def save_trade(self, trade: TradeRecord) -> None:
        with self._lock:
            self._trades[trade.id] = self._clone_trade(trade)

    def delete_trade(self, *, trade_id: str) -> None:
        with self._lock:
            self._trades.pop(trade_id, None)

    def get_trade(self, *, account_id: str, user_id: str, trade_id: str) -> TradeRecord | None:
        with self._lock:
            trade = self._trades.get(trade_id)
            if trade is None:
                return None
            if trade.account_id != account_id or trade.user_id != user_id:
                return None
            return self._clone_trade(trade)

    def list_trades(self, *, account_id: str, user_id: str) -> list[TradeRecord]:
        with self._lock:
            return [
                self._clone_trade(trade)
                for trade in self._trades.values()
                if trade.account_id == account_id and trade.user_id == user_id
            ]

    def save_cash_flow(self, cash_flow: CashFlow) -> None:
        with self._lock:
            self._cash_flows[cash_flow.id] = self._clone_cash_flow(cash_flow)

    def delete_cash_flow(self, *, cash_flow_id: str) -> None:
        with self._lock:
            self._cash_flows.pop(cash_flow_id, None)

    def list_cash_flows(self, *, account_id: str, user_id: str) -> list[CashFlow]:
        with self._lock:
            return [
                self._clone_cash_flow(flow)
                for flow in self._cash_flows.values()
                if flow.account_id == account_id and flow.user_id == user_id
            ]
