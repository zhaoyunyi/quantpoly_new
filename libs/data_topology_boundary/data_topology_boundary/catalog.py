"""模型归属与存储边界目录。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BoundaryCatalog:
    user_db_models: set[str] = field(default_factory=set)
    business_db_models: set[str] = field(default_factory=set)

    def model_database(self, model_name: str) -> str | None:
        if model_name in self.user_db_models:
            return "user_db"
        if model_name in self.business_db_models:
            return "business_db"
        return None


def default_catalog() -> BoundaryCatalog:
    return BoundaryCatalog(
        user_db_models={
            "User",
            "Session",
            "UserPreference",
            "Credential",
        },
        business_db_models={
            "Strategy",
            "BacktestTask",
            "TradingAccount",
            "Position",
            "TradeRecord",
            "CashFlow",
            "RiskRule",
            "RiskAlert",
            "TradingSignal",
            "ExecutionRecord",
        },
    )
