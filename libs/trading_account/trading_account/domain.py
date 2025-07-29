"""交易账户领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TradingAccount:
    id: str
    user_id: str
    account_name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

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
class TradeRecord:
    id: str
    user_id: str
    account_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

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
    ) -> "TradeRecord":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
        )


@dataclass
class CashFlow:
    id: str
    user_id: str
    account_id: str
    amount: float
    flow_type: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        amount: float,
        flow_type: str,
    ) -> "CashFlow":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            flow_type=flow_type,
        )
