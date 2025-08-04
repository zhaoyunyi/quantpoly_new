"""交易账户领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InvalidTradeOrderTransitionError(ValueError):
    """订单状态迁移非法。"""


@dataclass
class TradingAccount:
    id: str
    user_id: str
    account_name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(cls, *, user_id: str, account_name: str) -> "TradingAccount":
        return cls(id=str(uuid.uuid4()), user_id=user_id, account_name=account_name)


@dataclass
class Position:
    id: str
    user_id: str
    account_id: str
    symbol: str
    quantity: float
    avg_price: float
    last_price: float

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        quantity: float,
        avg_price: float,
        last_price: float,
    ) -> "Position":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            avg_price=avg_price,
            last_price=last_price,
        )


@dataclass
class TradeOrder:
    id: str
    user_id: str
    account_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> "TradeOrder":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            side=side.upper(),
            quantity=quantity,
            price=price,
            status="pending",
        )

    def _transition(self, *, target: str) -> None:
        if self.status != "pending":
            raise InvalidTradeOrderTransitionError(
                f"invalid transition: {self.status} -> {target}"
            )
        self.status = target
        self.updated_at = _utc_now()

    def mark_filled(self) -> None:
        self._transition(target="filled")

    def mark_cancelled(self) -> None:
        self._transition(target="cancelled")

    def mark_failed(self) -> None:
        self._transition(target="failed")


@dataclass
class TradeRecord:
    id: str
    user_id: str
    account_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    order_id: str | None = None
    created_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_id: str | None = None,
    ) -> "TradeRecord":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            side=side.upper(),
            quantity=quantity,
            price=price,
            order_id=order_id,
        )


@dataclass
class CashFlow:
    id: str
    user_id: str
    account_id: str
    amount: float
    flow_type: str
    related_trade_id: str | None = None
    created_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        amount: float,
        flow_type: str,
        related_trade_id: str | None = None,
    ) -> "CashFlow":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            flow_type=flow_type,
            related_trade_id=related_trade_id,
        )
