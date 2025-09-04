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
    "moving_average": {
        "templateId": "moving_average",
        "name": "双均线",
        "requiredParameters": {
            "shortWindow": {"type": "int", "min": 2, "max": 200},
            "longWindow": {"type": "int", "min": 3, "max": 400},
        },
        "defaults": {
            "shortWindow": 5,
            "longWindow": 20,
        },
    },
    "bollinger_bands": {
        "templateId": "bollinger_bands",
        "name": "布林带",
        "requiredParameters": {
            "period": {"type": "int", "min": 5, "max": 200},
            "stdDev": {"type": "float", "min": 0.1, "max": 5.0},
        },
        "defaults": {
            "period": 20,
            "stdDev": 2.0,
        },
    },
    "rsi": {
        "templateId": "rsi",
        "name": "RSI 反转",
        "requiredParameters": {
            "period": {"type": "int", "min": 2, "max": 200},
            "oversold": {"type": "float", "min": 0.0, "max": 100.0},
            "overbought": {"type": "float", "min": 0.0, "max": 100.0},
        },
        "defaults": {
            "period": 14,
            "oversold": 30.0,
            "overbought": 70.0,
        },
    },
    "macd": {
        "templateId": "macd",
        "name": "MACD 趋势",
        "requiredParameters": {
            "fast": {"type": "int", "min": 1, "max": 100},
            "slow": {"type": "int", "min": 2, "max": 200},
            "signal": {"type": "int", "min": 1, "max": 100},
        },
        "defaults": {
            "fast": 12,
            "slow": 26,
            "signal": 9,
        },
    },
    "mean_reversion": {
        "templateId": "mean_reversion",
        "name": "均值回归",
        "requiredParameters": {
            "window": {"type": "int", "min": 2, "max": 300},
            "entryZ": {"type": "float", "min": 0.1, "max": 5.0},
            "exitZ": {"type": "float", "min": 0.0, "max": 5.0},
        },
        "defaults": {
            "window": 20,
            "entryZ": 1.5,
            "exitZ": 0.5,
        },
    },
    "momentum": {
        "templateId": "momentum",
        "name": "动量突破",
        "requiredParameters": {
            "lookback": {"type": "int", "min": 2, "max": 252},
            "threshold": {"type": "float", "min": 0.0, "max": 1.0},
        },
        "defaults": {
            "lookback": 20,
            "threshold": 0.05,
        },
    },
}


class InvalidStrategyParametersError(ValueError):
    """策略参数非法。"""


class StrategyAccessDeniedError(PermissionError):
    """策略不属于当前用户或无权访问。"""


class StrategyService:
    def __init__(
        self,
        *,
        repository: InMemoryStrategyRepository,
        count_active_backtests: Callable[..., int],
        create_backtest_for_strategy: Callable[..., Any] | None = None,
        list_backtests_for_strategy: Callable[..., dict[str, Any]] | None = None,
        stats_backtests_for_strategy: Callable[..., dict[str, Any]] | None = None,
    ) -> None:
        self._repository = repository
        self._count_active_backtests = count_active_backtests
        self._create_backtest_for_strategy = create_backtest_for_strategy
        self._list_backtests_for_strategy = list_backtests_for_strategy
        self._stats_backtests_for_strategy = stats_backtests_for_strategy

    def list_templates(self) -> list[dict[str, Any]]:
        return list(_TEMPLATE_CATALOG.values())

    @staticmethod
    def _normalize_number(*, key: str, value: Any, expected_type: str) -> int | float:
        if expected_type == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                raise InvalidStrategyParametersError(f"invalid parameter type: {key}")
            return int(value)

        if expected_type == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise InvalidStrategyParametersError(f"invalid parameter type: {key}")
            return float(value)

        raise InvalidStrategyParametersError(f"unsupported parameter type rule: {key}")

    @staticmethod
    def _validate_template_relationships(*, template_id: str, parameters: dict[str, Any]) -> None:
        if template_id == "mean_reversion":
            entry_z = float(parameters["entryZ"])
            exit_z = float(parameters["exitZ"])
            if entry_z <= exit_z:
                raise InvalidStrategyParametersError("entryZ must be greater than exitZ")
            return

        if template_id == "moving_average":
            short_window = int(parameters["shortWindow"])
            long_window = int(parameters["longWindow"])
            if long_window <= short_window:
                raise InvalidStrategyParametersError("longWindow must be greater than shortWindow")
            return

        if template_id == "rsi":
            oversold = float(parameters["oversold"])
            overbought = float(parameters["overbought"])
            if overbought <= oversold:
                raise InvalidStrategyParametersError("overbought must be greater than oversold")
            return

        if template_id == "macd":
            fast = int(parameters["fast"])
            slow = int(parameters["slow"])
            if slow <= fast:
                raise InvalidStrategyParametersError("slow must be greater than fast")

    def _validate_parameters(self, *, template_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        template = _TEMPLATE_CATALOG.get(template_id)
        if template is None:
            raise InvalidStrategyParametersError(f"unknown template: {template_id}")

        required = template["requiredParameters"]
        parameter_keys = set(parameters.keys())
        required_keys = set(required.keys())

        unknown_keys = sorted(parameter_keys - required_keys)
        if unknown_keys:
            raise InvalidStrategyParametersError(f"unknown parameter: {unknown_keys[0]}")

        normalized: dict[str, Any] = {}
        for key, rule in required.items():
            if key not in parameters:
                raise InvalidStrategyParametersError(f"missing parameter: {key}")

            normalized_value = self._normalize_number(
                key=key,
                value=parameters[key],
                expected_type=str(rule["type"]),
            )

            min_value = rule.get("min")
            if min_value is not None and normalized_value < min_value:
                raise InvalidStrategyParametersError(f"parameter below minimum: {key}")

            max_value = rule.get("max")
            if max_value is not None and normalized_value > max_value:
                raise InvalidStrategyParametersError(f"parameter above maximum: {key}")

            normalized[key] = normalized_value

        self._validate_template_relationships(template_id=template_id, parameters=normalized)
        return normalized

    def _require_owned_strategy(self, *, user_id: str, strategy_id: str) -> Strategy:
        strategy = self._repository.get_by_id(strategy_id, user_id=user_id)
        if strategy is None:
            raise StrategyAccessDeniedError("strategy does not belong to current user")
        return strategy

    @staticmethod
    def _call_maybe_legacy_count(
        callback: Callable[..., int],
        *,
        user_id: str,
        strategy_id: str,
    ) -> int:
        try:
            return int(callback(user_id=user_id, strategy_id=strategy_id))
        except TypeError:
            pass

        try:
            return int(callback(user_id, strategy_id))
        except TypeError:
            return int(callback(strategy_id))

    @staticmethod
    def _call_required(callback: Callable[..., Any] | None, **kwargs: Any) -> Any:
        if callback is None:
            raise RuntimeError("backtest linkage callback is not configured")

        try:
            return callback(**kwargs)
        except TypeError:
            ordered = [
                kwargs["user_id"],
                kwargs["strategy_id"],
            ]
            if "config" in kwargs:
                ordered.append(kwargs["config"])
            if "idempotency_key" in kwargs:
                ordered.append(kwargs["idempotency_key"])
            if "status" in kwargs:
                ordered.append(kwargs["status"])
            if "page" in kwargs:
                ordered.append(kwargs["page"])
            if "page_size" in kwargs:
                ordered.append(kwargs["page_size"])
            return callback(*ordered)

    def validate_execution_parameters(
        self,
        *,
        user_id: str,
        strategy_id: str,
        parameters: dict[str, Any],
    ) -> Strategy:
        strategy = self._require_owned_strategy(user_id=user_id, strategy_id=strategy_id)
        self._validate_parameters(template_id=strategy.template, parameters=parameters)
        return strategy

    def create_strategy_from_template(
        self,
        *,
        user_id: str,
        name: str,
        template_id: str,
        parameters: dict[str, Any],
    ) -> Strategy:
        validated_parameters = self._validate_parameters(template_id=template_id, parameters=parameters)
        strategy = Strategy.create(
            user_id=user_id,
            name=name,
            template=template_id,
            parameters=validated_parameters,
        )
        self._repository.save(strategy)
        return strategy

    def create_strategy(
        self,
        *,
        user_id: str,
        name: str,
        template: str,
        parameters: dict[str, Any],
    ) -> Strategy:
        validated_parameters = self._validate_parameters(template_id=template, parameters=parameters)
        strategy = Strategy.create(
            user_id=user_id,
            name=name,
            template=template,
            parameters=validated_parameters,
        )
        self._repository.save(strategy)
        return strategy

    def update_strategy(
        self,
        *,
        user_id: str,
        strategy_id: str,
        name: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> Strategy | None:
        strategy = self._repository.get_by_id(strategy_id, user_id=user_id)
        if strategy is None:
            return None

        validated_parameters = parameters
        if parameters is not None:
            validated_parameters = self._validate_parameters(template_id=strategy.template, parameters=parameters)

        strategy.update(name=name, parameters=validated_parameters)
        self._repository.save(strategy)
        return strategy

    def list_strategies(self, *, user_id: str) -> list[Strategy]:
        return self._repository.list_by_user(user_id=user_id)

    def get_strategy(self, *, user_id: str, strategy_id: str) -> Strategy | None:
        return self._repository.get_by_id(strategy_id, user_id=user_id)

    def create_backtest_for_strategy(
        self,
        *,
        user_id: str,
        strategy_id: str,
        config: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> Any:
        strategy = self._require_owned_strategy(user_id=user_id, strategy_id=strategy_id)
        return self._call_required(
            self._create_backtest_for_strategy,
            user_id=user_id,
            strategy_id=strategy.id,
            config=config,
            idempotency_key=idempotency_key,
        )

    def list_backtests_for_strategy(
        self,
        *,
        user_id: str,
        strategy_id: str,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        strategy = self._require_owned_strategy(user_id=user_id, strategy_id=strategy_id)
        listing = self._call_required(
            self._list_backtests_for_strategy,
            user_id=user_id,
            strategy_id=strategy.id,
            status=status,
            page=page,
            page_size=page_size,
        )
        return dict(listing)

    def backtest_stats_for_strategy(self, *, user_id: str, strategy_id: str) -> dict[str, Any]:
        strategy = self._require_owned_strategy(user_id=user_id, strategy_id=strategy_id)
        stats = self._call_required(
            self._stats_backtests_for_strategy,
            user_id=user_id,
            strategy_id=strategy.id,
        )
        return dict(stats)

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

        active_count = self._call_maybe_legacy_count(
            self._count_active_backtests,
            user_id=user_id,
            strategy_id=strategy.id,
        )
        if active_count > 0:
            raise StrategyInUseError(
                f"strategy_in_use active_backtests={active_count} strategy_id={strategy.id}"
            )

        return self._repository.delete(strategy_id, user_id=user_id)


__all__ = [
    "StrategyService",
    "InvalidStrategyParametersError",
    "StrategyAccessDeniedError",
    "InvalidStrategyTransitionError",
]
