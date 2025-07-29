"""策略管理服务。"""

from __future__ import annotations

from collections.abc import Callable

from strategy_management.domain import Strategy, StrategyInUseError
from strategy_management.repository import InMemoryStrategyRepository


class StrategyService:
    def __init__(
        self,
        *,
        repository: InMemoryStrategyRepository,
        count_active_backtests: Callable[[str], int],
    ) -> None:
        self._repository = repository
        self._count_active_backtests = count_active_backtests

    def create_strategy(
        self,
        *,
        user_id: str,
        name: str,
        template: str,
        parameters: dict,
    ) -> Strategy:
        strategy = Strategy.create(
            user_id=user_id,
            name=name,
            template=template,
            parameters=parameters,
        )
        self._repository.save(strategy)
        return strategy

    def list_strategies(self, *, user_id: str) -> list[Strategy]:
        return self._repository.list_by_user(user_id=user_id)

    def get_strategy(self, *, user_id: str, strategy_id: str) -> Strategy | None:
        return self._repository.get_by_id(strategy_id, user_id=user_id)

    def delete_strategy(self, *, user_id: str, strategy_id: str) -> bool:
        strategy = self._repository.get_by_id(strategy_id, user_id=user_id)
        if strategy is None:
            return False

        active_count = self._count_active_backtests(strategy.id)
        if active_count > 0:
            raise StrategyInUseError(
                f"strategy_in_use active_backtests={active_count} strategy_id={strategy.id}"
            )

        return self._repository.delete(strategy_id, user_id=user_id)
