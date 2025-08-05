"""策略管理服务。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from strategy_management.domain import (
    InvalidStrategyTransitionError,
    Strategy,
    StrategyInUseError,
)
from strategy_management.repository import InMemoryStrategyRepository

_TEMPLATE_CATALOG: dict[str, dict[str, Any]] = {
    "mean_reversion": {
        "templateId": "mean_reversion",
        "name": "均值回归",
        "requiredParameters": {
            "window": {"type": "int", "min": 2},
            "entryZ": {"type": "float", "min": 0.1},
            "exitZ": {"type": "float", "min": 0.0},
        },
    }
}


class InvalidStrategyParametersError(ValueError):
    """策略参数非法。"""


class StrategyService:
    def __init__(
        self,
        *,
        repository: InMemoryStrategyRepository,
        count_active_backtests: Callable[[str], int],
    ) -> None:
        self._repository = repository
        self._count_active_backtests = count_active_backtests

    def list_templates(self) -> list[dict[str, Any]]:
        return list(_TEMPLATE_CATALOG.values())

    def _validate_parameters(self, *, template_id: str, parameters: dict[str, Any]) -> None:
        template = _TEMPLATE_CATALOG.get(template_id)
        if template is None:
            raise InvalidStrategyParametersError(f"unknown template: {template_id}")

        required = template["requiredParameters"]
        for key, rule in required.items():
            if key not in parameters:
                raise InvalidStrategyParametersError(f"missing parameter: {key}")

            value = parameters[key]
            expected_type = rule["type"]
            if expected_type == "int" and not isinstance(value, int):
                raise InvalidStrategyParametersError(f"invalid parameter type: {key}")
            if expected_type == "float" and not isinstance(value, (int, float)):
                raise InvalidStrategyParametersError(f"invalid parameter type: {key}")

            min_value = rule.get("min")
            if min_value is not None and value < min_value:
                raise InvalidStrategyParametersError(f"parameter below minimum: {key}")

        entry_z = float(parameters["entryZ"])
        exit_z = float(parameters["exitZ"])
        if entry_z <= exit_z:
            raise InvalidStrategyParametersError("entryZ must be greater than exitZ")

    def create_strategy_from_template(
        self,
        *,
        user_id: str,
        name: str,
        template_id: str,
        parameters: dict[str, Any],
    ) -> Strategy:
        self._validate_parameters(template_id=template_id, parameters=parameters)
        strategy = Strategy.create(
            user_id=user_id,
            name=name,
            template=template_id,
            parameters=parameters,
        )
        self._repository.save(strategy)
        return strategy

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

    def activate_strategy(self, *, user_id: str, strategy_id: str) -> Strategy | None:
        strategy = self._repository.get_by_id(strategy_id, user_id=user_id)
        if strategy is None:
            return None
        strategy.activate()
        self._repository.save(strategy)
        return strategy

    def deactivate_strategy(self, *, user_id: str, strategy_id: str) -> Strategy | None:
        strategy = self._repository.get_by_id(strategy_id, user_id=user_id)
        if strategy is None:
            return None
        strategy.deactivate()
        self._repository.save(strategy)
        return strategy

    def archive_strategy(self, *, user_id: str, strategy_id: str) -> Strategy | None:
        strategy = self._repository.get_by_id(strategy_id, user_id=user_id)
        if strategy is None:
            return None
        strategy.archive()
        self._repository.save(strategy)
        return strategy

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


__all__ = [
    "StrategyService",
    "InvalidStrategyParametersError",
    "InvalidStrategyTransitionError",
]
