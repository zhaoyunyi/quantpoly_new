"""signal_execution 领域模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TradingSignal:
    id: str
    user_id: str
    strategy_id: str
    account_id: str
    symbol: str
    side: str
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        strategy_id: str,
        account_id: str,
        symbol: str,
        side: str,
        expires_at: datetime | None = None,
    ) -> "TradingSignal":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )

    def execute(self) -> None:
        self.status = "executed"
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        self.status = "cancelled"
        self.updated_at = datetime.now(timezone.utc)

    def expire(self) -> None:
        self.status = "expired"
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ExecutionRecord:
    id: str
    user_id: str
    signal_id: str
    strategy_id: str
    symbol: str
    status: str
    metrics: dict[str, float]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        signal_id: str,
        strategy_id: str,
        symbol: str,
        status: str,
        metrics: dict[str, float] | None = None,
    ) -> "ExecutionRecord":
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            signal_id=signal_id,
            strategy_id=strategy_id,
            symbol=symbol,
            status=status,
            metrics=dict(metrics or {}),
        )
