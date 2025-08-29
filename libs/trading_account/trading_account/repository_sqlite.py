"""交易账户 SQLite 持久化仓储。"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from trading_account.domain import CashFlow, Position, TradeOrder, TradeRecord, TradingAccount


class SQLiteTradingAccountRepository:
    """基于 sqlite3 的交易账户仓储。"""

    def __init__(self, *, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_account_account (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    is_active INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_account_position (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    last_price REAL NOT NULL,
                    UNIQUE(account_id, user_id, symbol)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_account_order (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_account_trade (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    order_id TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_account_cash_flow (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    flow_type TEXT NOT NULL,
                    related_trade_id TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _to_dt(self, value: str) -> datetime:
        return datetime.fromisoformat(value)

    def save_account(self, account: TradingAccount) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trading_account_account (id, user_id, account_name, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    account_name = excluded.account_name,
                    is_active = excluded.is_active,
                    created_at = excluded.created_at
                """,
                (
                    account.id,
                    account.user_id,
                    account.account_name,
                    1 if account.is_active else 0,
                    account.created_at.isoformat(),
                ),
            )

    def list_accounts(self, *, user_id: str) -> list[TradingAccount]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, account_name, is_active, created_at
                FROM trading_account_account
                WHERE user_id = ?
                ORDER BY created_at ASC
                """,
                (user_id,),
            ).fetchall()

        return [
            TradingAccount(
                id=row[0],
                user_id=row[1],
                account_name=row[2],
                is_active=bool(row[3]),
                created_at=self._to_dt(row[4]),
            )
            for row in rows
        ]

    def get_account(self, *, account_id: str, user_id: str) -> TradingAccount | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, account_name, is_active, created_at
                FROM trading_account_account
                WHERE id = ? AND user_id = ?
                """,
                (account_id, user_id),
            ).fetchone()

        if row is None:
            return None

        return TradingAccount(
            id=row[0],
            user_id=row[1],
            account_name=row[2],
            is_active=bool(row[3]),
            created_at=self._to_dt(row[4]),
        )

    def save_position(self, position: Position) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trading_account_position
                    (id, user_id, account_id, symbol, quantity, avg_price, last_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id, user_id, symbol) DO UPDATE SET
                    id = excluded.id,
                    quantity = excluded.quantity,
                    avg_price = excluded.avg_price,
                    last_price = excluded.last_price
                """,
                (
                    position.id,
                    position.user_id,
                    position.account_id,
                    position.symbol,
                    position.quantity,
                    position.avg_price,
                    position.last_price,
                ),
            )

    def list_positions(self, *, account_id: str, user_id: str) -> list[Position]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, account_id, symbol, quantity, avg_price, last_price
                FROM trading_account_position
                WHERE account_id = ? AND user_id = ?
                ORDER BY symbol ASC
                """,
                (account_id, user_id),
            ).fetchall()

        return [
            Position(
                id=row[0],
                user_id=row[1],
                account_id=row[2],
                symbol=row[3],
                quantity=row[4],
                avg_price=row[5],
                last_price=row[6],
            )
            for row in rows
        ]

    def save_order(self, order: TradeOrder) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trading_account_order
                    (id, user_id, account_id, symbol, side, quantity, price, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    account_id = excluded.account_id,
                    symbol = excluded.symbol,
                    side = excluded.side,
                    quantity = excluded.quantity,
                    price = excluded.price,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    order.id,
                    order.user_id,
                    order.account_id,
                    order.symbol,
                    order.side,
                    order.quantity,
                    order.price,
                    order.status,
                    order.created_at.isoformat(),
                    order.updated_at.isoformat(),
                ),
            )

    def delete_order(self, *, order_id: str) -> TradeOrder | None:
        existing = self._get_order_by_id(order_id=order_id)
        if existing is None:
            return None

        with self._connect() as conn:
            conn.execute(
                "DELETE FROM trading_account_order WHERE id = ?",
                (order_id,),
            )
        return existing

    def _get_order_by_id(self, *, order_id: str) -> TradeOrder | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, account_id, symbol, side, quantity, price, status, created_at, updated_at
                FROM trading_account_order
                WHERE id = ?
                """,
                (order_id,),
            ).fetchone()

        if row is None:
            return None

        return TradeOrder(
            id=row[0],
            user_id=row[1],
            account_id=row[2],
            symbol=row[3],
            side=row[4],
            quantity=row[5],
            price=row[6],
            status=row[7],
            created_at=self._to_dt(row[8]),
            updated_at=self._to_dt(row[9]),
        )

    def get_order(self, *, account_id: str, user_id: str, order_id: str) -> TradeOrder | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, account_id, symbol, side, quantity, price, status, created_at, updated_at
                FROM trading_account_order
                WHERE id = ? AND account_id = ? AND user_id = ?
                """,
                (order_id, account_id, user_id),
            ).fetchone()

        if row is None:
            return None

        return TradeOrder(
            id=row[0],
            user_id=row[1],
            account_id=row[2],
            symbol=row[3],
            side=row[4],
            quantity=row[5],
            price=row[6],
            status=row[7],
            created_at=self._to_dt(row[8]),
            updated_at=self._to_dt(row[9]),
        )

    def list_orders(self, *, account_id: str, user_id: str) -> list[TradeOrder]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, account_id, symbol, side, quantity, price, status, created_at, updated_at
                FROM trading_account_order
                WHERE account_id = ? AND user_id = ?
                ORDER BY created_at ASC
                """,
                (account_id, user_id),
            ).fetchall()

        return [
            TradeOrder(
                id=row[0],
                user_id=row[1],
                account_id=row[2],
                symbol=row[3],
                side=row[4],
                quantity=row[5],
                price=row[6],
                status=row[7],
                created_at=self._to_dt(row[8]),
                updated_at=self._to_dt(row[9]),
            )
            for row in rows
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
        with self._connect() as conn:
            updated_at = datetime.now().astimezone().isoformat()
            cursor = conn.execute(
                """
                UPDATE trading_account_order
                SET status = ?, updated_at = ?
                WHERE id = ? AND account_id = ? AND user_id = ? AND status = ?
                """,
                (to_status, updated_at, order_id, account_id, user_id, from_status),
            )
            if cursor.rowcount == 0:
                return None

            row = conn.execute(
                """
                SELECT id, user_id, account_id, symbol, side, quantity, price, status, created_at, updated_at
                FROM trading_account_order
                WHERE id = ?
                """,
                (order_id,),
            ).fetchone()

        if row is None:
            return None

        return TradeOrder(
            id=row[0],
            user_id=row[1],
            account_id=row[2],
            symbol=row[3],
            side=row[4],
            quantity=row[5],
            price=row[6],
            status=row[7],
            created_at=self._to_dt(row[8]),
            updated_at=self._to_dt(row[9]),
        )

    def save_trade(self, trade: TradeRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trading_account_trade
                    (id, user_id, account_id, symbol, side, quantity, price, order_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    account_id = excluded.account_id,
                    symbol = excluded.symbol,
                    side = excluded.side,
                    quantity = excluded.quantity,
                    price = excluded.price,
                    order_id = excluded.order_id,
                    created_at = excluded.created_at
                """,
                (
                    trade.id,
                    trade.user_id,
                    trade.account_id,
                    trade.symbol,
                    trade.side,
                    trade.quantity,
                    trade.price,
                    trade.order_id,
                    trade.created_at.isoformat(),
                ),
            )

    def delete_trade(self, *, trade_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM trading_account_trade WHERE id = ?", (trade_id,))

    def get_trade(self, *, account_id: str, user_id: str, trade_id: str) -> TradeRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, account_id, symbol, side, quantity, price, order_id, created_at
                FROM trading_account_trade
                WHERE id = ? AND account_id = ? AND user_id = ?
                """,
                (trade_id, account_id, user_id),
            ).fetchone()

        if row is None:
            return None

        return TradeRecord(
            id=row[0],
            user_id=row[1],
            account_id=row[2],
            symbol=row[3],
            side=row[4],
            quantity=row[5],
            price=row[6],
            order_id=row[7],
            created_at=self._to_dt(row[8]),
        )

    def list_trades(self, *, account_id: str, user_id: str) -> list[TradeRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, account_id, symbol, side, quantity, price, order_id, created_at
                FROM trading_account_trade
                WHERE account_id = ? AND user_id = ?
                ORDER BY created_at ASC
                """,
                (account_id, user_id),
            ).fetchall()

        return [
            TradeRecord(
                id=row[0],
                user_id=row[1],
                account_id=row[2],
                symbol=row[3],
                side=row[4],
                quantity=row[5],
                price=row[6],
                order_id=row[7],
                created_at=self._to_dt(row[8]),
            )
            for row in rows
        ]

    def save_cash_flow(self, cash_flow: CashFlow) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trading_account_cash_flow
                    (id, user_id, account_id, amount, flow_type, related_trade_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    account_id = excluded.account_id,
                    amount = excluded.amount,
                    flow_type = excluded.flow_type,
                    related_trade_id = excluded.related_trade_id,
                    created_at = excluded.created_at
                """,
                (
                    cash_flow.id,
                    cash_flow.user_id,
                    cash_flow.account_id,
                    cash_flow.amount,
                    cash_flow.flow_type,
                    cash_flow.related_trade_id,
                    cash_flow.created_at.isoformat(),
                ),
            )

    def delete_cash_flow(self, *, cash_flow_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM trading_account_cash_flow WHERE id = ?", (cash_flow_id,))

    def list_cash_flows(self, *, account_id: str, user_id: str) -> list[CashFlow]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, account_id, amount, flow_type, related_trade_id, created_at
                FROM trading_account_cash_flow
                WHERE account_id = ? AND user_id = ?
                ORDER BY created_at ASC
                """,
                (account_id, user_id),
            ).fetchall()

        return [
            CashFlow(
                id=row[0],
                user_id=row[1],
                account_id=row[2],
                amount=row[3],
                flow_type=row[4],
                related_trade_id=row[5],
                created_at=self._to_dt(row[6]),
            )
            for row in rows
        ]

    def list_orders_by_status(
        self,
        *,
        status: str,
        account_id: str | None = None,
        user_id: str | None = None,
    ) -> list[TradeOrder]:
        sql = """
                SELECT id, user_id, account_id, symbol, side, quantity, price, status, created_at, updated_at
                FROM trading_account_order
                WHERE status = ?
            """
        params: list[object] = [status]

        if account_id is not None:
            sql += " AND account_id = ?"
            params.append(account_id)
        if user_id is not None:
            sql += " AND user_id = ?"
            params.append(user_id)

        sql += " ORDER BY created_at ASC"

        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            TradeOrder(
                id=row[0],
                user_id=row[1],
                account_id=row[2],
                symbol=row[3],
                side=row[4],
                quantity=row[5],
                price=row[6],
                status=row[7],
                created_at=self._to_dt(row[8]),
                updated_at=self._to_dt(row[9]),
            )
            for row in rows
        ]

    def refresh_position_prices(
        self,
        *,
        price_updates: dict[str, float],
        account_id: str | None = None,
        user_id: str | None = None,
    ) -> int:
        updated = 0
        with self._connect() as conn:
            for symbol, price in price_updates.items():
                sql = "UPDATE trading_account_position SET last_price = ? WHERE symbol = ?"
                params: list[object] = [float(price), symbol]

                if account_id is not None:
                    sql += " AND account_id = ?"
                    params.append(account_id)
                if user_id is not None:
                    sql += " AND user_id = ?"
                    params.append(user_id)

                cursor = conn.execute(sql, tuple(params))
                updated += cursor.rowcount

        return updated
