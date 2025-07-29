"""交易账户 in-memory 仓储。"""

from __future__ import annotations

from trading_account.domain import CashFlow, Position, TradeRecord, TradingAccount


class InMemoryTradingAccountRepository:
    def __init__(self) -> None:
        self._accounts: dict[str, TradingAccount] = {}
        self._positions: dict[tuple[str, str], Position] = {}
        self._trades: dict[str, TradeRecord] = {}
        self._cash_flows: dict[str, CashFlow] = {}

    def save_account(self, account: TradingAccount) -> None:
        self._accounts[account.id] = account

    def list_accounts(self, *, user_id: str) -> list[TradingAccount]:
        return [account for account in self._accounts.values() if account.user_id == user_id]

    def get_account(self, *, account_id: str, user_id: str) -> TradingAccount | None:
        account = self._accounts.get(account_id)
        if account is None or account.user_id != user_id:
            return None
        return account

    def save_position(self, position: Position) -> None:
        self._positions[(position.account_id, position.symbol)] = position

    def list_positions(self, *, account_id: str, user_id: str) -> list[Position]:
        return [
            pos
            for pos in self._positions.values()
            if pos.account_id == account_id and pos.user_id == user_id
        ]

    def save_trade(self, trade: TradeRecord) -> None:
        self._trades[trade.id] = trade

    def list_trades(self, *, account_id: str, user_id: str) -> list[TradeRecord]:
        return [
            trade
            for trade in self._trades.values()
            if trade.account_id == account_id and trade.user_id == user_id
        ]

    def save_cash_flow(self, cash_flow: CashFlow) -> None:
        self._cash_flows[cash_flow.id] = cash_flow

    def list_cash_flows(self, *, account_id: str, user_id: str) -> list[CashFlow]:
        return [
            flow
            for flow in self._cash_flows.values()
            if flow.account_id == account_id and flow.user_id == user_id
        ]
