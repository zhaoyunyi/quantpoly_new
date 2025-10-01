"""策略仓储实现。"""

from __future__ import annotations

from strategy_management.domain import Strategy
from strategy_management.portfolio import Portfolio


class InMemoryStrategyRepository:
    def __init__(self) -> None:
        self._items: dict[str, Strategy] = {}

    def save(self, strategy: Strategy) -> None:
        self._items[strategy.id] = strategy

    def get_by_id(self, strategy_id: str, *, user_id: str) -> Strategy | None:
        item = self._items.get(strategy_id)
        if item is None:
            return None
        if item.user_id != user_id:
            return None
        return item

    def list_by_user(self, *, user_id: str) -> list[Strategy]:
        return [item for item in self._items.values() if item.user_id == user_id]

    def delete(self, strategy_id: str, *, user_id: str) -> bool:
        item = self._items.get(strategy_id)
        if item is None or item.user_id != user_id:
            return False
        del self._items[strategy_id]
        return True


class InMemoryPortfolioRepository:
    def __init__(self) -> None:
        self._items: dict[str, Portfolio] = {}

    def save(self, portfolio: Portfolio) -> None:
        self._items[portfolio.id] = portfolio

    def get_by_id(self, portfolio_id: str, *, user_id: str) -> Portfolio | None:
        item = self._items.get(portfolio_id)
        if item is None:
            return None
        if item.user_id != user_id:
            return None
        return item

    def list_by_user(self, *, user_id: str) -> list[Portfolio]:
        return [item for item in self._items.values() if item.user_id == user_id]

    def delete(self, portfolio_id: str, *, user_id: str) -> bool:
        item = self._items.get(portfolio_id)
        if item is None or item.user_id != user_id:
            return False
        del self._items[portfolio_id]
        return True
