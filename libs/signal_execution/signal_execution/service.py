"""signal_execution 应用服务。"""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from signal_execution.domain import ExecutionRecord, TradingSignal
from signal_execution.repository import InMemorySignalRepository


class SignalAccessDeniedError(PermissionError):
    """信号不属于当前用户或无权访问。"""


class AdminRequiredError(PermissionError):
    """全局维护接口需要管理员权限。"""


class BatchIdempotencyConflictError(RuntimeError):
    """批处理幂等键冲突。"""


class InvalidSignalParametersError(ValueError):
    """信号参数校验失败。"""


_EXECUTION_TEMPLATE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "strategyType": "moving_average",
        "name": "双均线策略",
        "description": "基于短期与长期移动平均线交叉触发买卖信号。",
        "parameters": {
            "shortWindow": {"type": "integer", "required": True, "minimum": 1},
            "longWindow": {"type": "integer", "required": True, "minimum": 2},
        },
    },
    {
        "strategyType": "mean_reversion",
        "name": "均值回归策略",
        "description": "基于价格偏离均值程度（Z-Score）触发反转信号。",
        "parameters": {
            "window": {"type": "integer", "required": True, "minimum": 2},
            "entryZ": {"type": "number", "required": True, "exclusiveMinimum": 0},
            "exitZ": {"type": "number", "required": True, "exclusiveMinimum": 0},
        },
    },
)


class SignalExecutionService:
    def __init__(
        self,
        *,
        repository: InMemorySignalRepository,
        strategy_owner_acl: Callable[[str, str], bool],
        account_owner_acl: Callable[[str, str], bool],
        risk_checker: Callable[..., dict[str, Any]] | None = None,
        strategy_parameter_validator: Callable[[str, str, dict[str, Any]], None] | None = None,
        governance_checker: Callable[..., Any] | None = None,
        strategy_reader: Callable[..., Any] | None = None,
        market_history_reader: Callable[..., Any] | None = None,
    ) -> None:
        self._repository = repository
        self._strategy_owner_acl = strategy_owner_acl
        self._account_owner_acl = account_owner_acl
        self._risk_checker = risk_checker
        self._strategy_parameter_validator = strategy_parameter_validator
        self._governance_checker = governance_checker
        self._strategy_reader = strategy_reader
        self._market_history_reader = market_history_reader

    def _ensure_admin(
        self,
        *,
        actor_id: str,
        is_admin: bool,
        admin_decision_source: str,
        confirmation_token: str | None,
        action: str,
        target: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        if self._governance_checker is not None:
            role = "admin" if is_admin else "user"
            level = 10 if is_admin else 1
            payload = dict(context or {})
            payload.setdefault("adminDecisionSource", admin_decision_source)
            try:
                self._governance_checker(
                    actor_id=actor_id,
                    role=role,
                    level=level,
                    action=action,
                    target=target,
                    confirmation_token=confirmation_token,
                    context=payload,
                )
            except Exception as exc:  # noqa: BLE001
                raise AdminRequiredError(str(exc)) from exc
            return

        if not is_admin:
            raise AdminRequiredError("admin role required")

    def _assert_strategy_acl(self, *, user_id: str, strategy_id: str) -> None:
        if not self._strategy_owner_acl(user_id, strategy_id):
            raise SignalAccessDeniedError("strategy does not belong to current user")

    def _assert_signal_acl(self, *, user_id: str, strategy_id: str, account_id: str) -> None:
        self._assert_strategy_acl(user_id=user_id, strategy_id=strategy_id)
        self._assert_account_acl(user_id=user_id, account_id=account_id)

    def _assert_account_acl(self, *, user_id: str, account_id: str) -> None:
        if not self._account_owner_acl(user_id, account_id):
            raise SignalAccessDeniedError("account does not belong to current user")

    def _idempotency_fingerprint(self, *, signal_ids: list[str]) -> str:
        return "|".join(sorted(signal_ids))

    @staticmethod
    def _signal_stats(signals: list[TradingSignal]) -> dict[str, int]:
        return {
            "total": len(signals),
            "pending": sum(1 for item in signals if item.status == "pending"),
            "expired": sum(1 for item in signals if item.status == "expired"),
            "executed": sum(1 for item in signals if item.status == "executed"),
            "cancelled": sum(1 for item in signals if item.status == "cancelled"),
        }

    @staticmethod
    def _average(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 4)

    def list_execution_templates(self, *, strategy_type: str | None = None) -> list[dict[str, Any]]:
        normalized = strategy_type.strip().lower() if strategy_type is not None else None

        templates: list[dict[str, Any]] = []
        for template in _EXECUTION_TEMPLATE_CATALOG:
            if normalized is not None and template["strategyType"] != normalized:
                continue
            templates.append(
                {
                    "strategyType": template["strategyType"],
                    "name": template["name"],
                    "description": template["description"],
                    "parameters": {
                        key: dict(value)
                        for key, value in dict(template.get("parameters", {})).items()
                    },
                }
            )

        return templates

    @staticmethod
    def _strategy_field(strategy: Any, key: str, default: Any = None) -> Any:
        if isinstance(strategy, dict):
            return strategy.get(key, default)
        return getattr(strategy, key, default)

    @staticmethod
    def _to_positive_int(value: Any) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed

    @staticmethod
    def _to_positive_float(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed

    @staticmethod
    def _extract_close_prices(rows: Any) -> list[float]:
        if rows is None:
            return []

        result: list[float] = []
        for row in list(rows):
            value: Any = None
            if isinstance(row, dict):
                value = row.get("close")
                if value is None:
                    value = row.get("close_price")
                if value is None:
                    value = row.get("c")
            else:
                for field in ("close_price", "close", "c"):
                    if hasattr(row, field):
                        value = getattr(row, field)
                        if value is not None:
                            break

            try:
                if value is None:
                    continue
                result.append(float(value))
            except (TypeError, ValueError):
                continue

        return result

    def _call_strategy_reader(self, *, user_id: str, strategy_id: str) -> Any:
        if self._strategy_reader is None:
            return None

        try:
            return self._strategy_reader(user_id=user_id, strategy_id=strategy_id)
        except TypeError:
            pass

        try:
            return self._strategy_reader(user_id, strategy_id)
        except TypeError:
            return self._strategy_reader(strategy_id)

    def _call_market_history_reader(
        self,
        *,
        user_id: str,
        symbol: str,
        timeframe: str,
        limit: int | None,
    ) -> Any:
        if self._market_history_reader is None:
            return []

        try:
            return self._market_history_reader(
                user_id=user_id,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
        except TypeError:
            pass

        try:
            return self._market_history_reader(user_id, symbol, timeframe, limit)
        except TypeError:
            return self._market_history_reader(symbol)

    def _evaluate_moving_average(
        self,
        *,
        close_prices: list[float],
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        short_window = self._to_positive_int(parameters.get("shortWindow"))
        long_window = self._to_positive_int(parameters.get("longWindow"))
        if short_window is None or long_window is None:
            raise InvalidSignalParametersError("moving_average missing window parameters")
        if long_window <= short_window:
            raise InvalidSignalParametersError("longWindow must be greater than shortWindow")

        if len(close_prices) < long_window:
            return {
                "decision": "skip",
                "reason": "insufficient_data",
                "metadata": {
                    "requiredDataPoints": long_window,
                    "actualDataPoints": len(close_prices),
                    "triggered_indicator": "moving_average",
                },
            }

        short_avg = sum(close_prices[-short_window:]) / float(short_window)
        long_avg = sum(close_prices[-long_window:]) / float(long_window)

        if short_avg > long_avg:
            return {
                "decision": "BUY",
                "reason": "moving_average_bullish_cross",
                "triggered_indicator": "moving_average",
                "metadata": {
                    "shortWindow": short_window,
                    "longWindow": long_window,
                    "shortAverage": short_avg,
                    "longAverage": long_avg,
                },
            }

        if short_avg < long_avg:
            return {
                "decision": "SELL",
                "reason": "moving_average_bearish_cross",
                "triggered_indicator": "moving_average",
                "metadata": {
                    "shortWindow": short_window,
                    "longWindow": long_window,
                    "shortAverage": short_avg,
                    "longAverage": long_avg,
                },
            }

        return {
            "decision": "skip",
            "reason": "no_signal",
            "metadata": {
                "triggered_indicator": "moving_average",
                "shortWindow": short_window,
                "longWindow": long_window,
            },
        }

    def _evaluate_mean_reversion(
        self,
        *,
        close_prices: list[float],
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        window = self._to_positive_int(parameters.get("window"))
        entry_z = self._to_positive_float(parameters.get("entryZ"))
        exit_z = self._to_positive_float(parameters.get("exitZ"))
        if window is None or entry_z is None or exit_z is None:
            raise InvalidSignalParametersError("mean_reversion missing required parameters")
        if entry_z <= exit_z:
            raise InvalidSignalParametersError("entryZ must be greater than exitZ")

        if len(close_prices) < window:
            return {
                "decision": "skip",
                "reason": "insufficient_data",
                "metadata": {
                    "requiredDataPoints": window,
                    "actualDataPoints": len(close_prices),
                    "triggered_indicator": "mean_reversion",
                },
            }

        window_prices = close_prices[-window:]
        latest = close_prices[-1]
        mean_price = sum(window_prices) / float(window)
        variance = sum((item - mean_price) ** 2 for item in window_prices) / float(window)
        deviation = math.sqrt(variance)

        if deviation == 0:
            return {
                "decision": "skip",
                "reason": "no_signal",
                "metadata": {
                    "triggered_indicator": "mean_reversion",
                    "zScore": 0.0,
                },
            }

        z_score = (latest - mean_price) / deviation
        if z_score <= -entry_z:
            return {
                "decision": "BUY",
                "reason": "mean_reversion_oversold",
                "triggered_indicator": "mean_reversion",
                "metadata": {
                    "window": window,
                    "entryZ": entry_z,
                    "exitZ": exit_z,
                    "zScore": z_score,
                },
            }

        if z_score >= entry_z:
            return {
                "decision": "SELL",
                "reason": "mean_reversion_overbought",
                "triggered_indicator": "mean_reversion",
                "metadata": {
                    "window": window,
                    "entryZ": entry_z,
                    "exitZ": exit_z,
                    "zScore": z_score,
                },
            }

        return {
            "decision": "skip",
            "reason": "no_signal",
            "metadata": {
                "triggered_indicator": "mean_reversion",
                "window": window,
                "entryZ": entry_z,
                "exitZ": exit_z,
                "zScore": z_score,
            },
        }

    def _evaluate_by_template(
        self,
        *,
        template: str,
        parameters: dict[str, Any],
        close_prices: list[float],
    ) -> dict[str, Any]:
        normalized = template.strip().lower()
        if normalized == "moving_average":
            return self._evaluate_moving_average(close_prices=close_prices, parameters=parameters)
        if normalized == "mean_reversion":
            return self._evaluate_mean_reversion(close_prices=close_prices, parameters=parameters)

        return {
            "decision": "skip",
            "reason": "unsupported_template",
            "metadata": {
                "template": normalized,
            },
        }

    def validate_parameters(
        self,
        *,
        user_id: str,
        strategy_id: str,
        account_id: str,
        parameters: dict[str, Any],
    ) -> None:
        self._assert_signal_acl(user_id=user_id, strategy_id=strategy_id, account_id=account_id)
        if self._strategy_parameter_validator is None:
            return

        try:
            self._strategy_parameter_validator(user_id, strategy_id, parameters)
        except PermissionError as exc:
            raise SignalAccessDeniedError(str(exc)) from exc
        except ValueError as exc:
            raise InvalidSignalParametersError(str(exc)) from exc

    def create_signal(
        self,
        *,
        user_id: str,
        strategy_id: str,
        account_id: str,
        symbol: str,
        side: str,
        parameters: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TradingSignal:
        if parameters is not None:
            self.validate_parameters(
                user_id=user_id,
                strategy_id=strategy_id,
                account_id=account_id,
                parameters=parameters,
            )
        else:
            self._assert_signal_acl(user_id=user_id, strategy_id=strategy_id, account_id=account_id)

        signal = TradingSignal.create(
            user_id=user_id,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            expires_at=expires_at,
            metadata=metadata,
        )
        self._repository.save_signal(signal)
        return signal

    def generate_signals(
        self,
        *,
        user_id: str,
        strategy_id: str,
        account_id: str,
        symbols: list[str],
        side: str = "BUY",
        parameters: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> list[TradingSignal]:
        signals: list[TradingSignal] = []
        for symbol in symbols:
            signals.append(
                self.create_signal(
                    user_id=user_id,
                    strategy_id=strategy_id,
                    account_id=account_id,
                    symbol=symbol,
                    side=side,
                    parameters=parameters,
                    expires_at=expires_at,
                )
            )
        return signals

    def generate_signals_by_strategy(
        self,
        *,
        user_id: str,
        strategy_id: str,
        account_id: str,
        symbols: list[str],
        timeframe: str = "1Day",
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        self._assert_signal_acl(user_id=user_id, strategy_id=strategy_id, account_id=account_id)

        strategy = self._call_strategy_reader(user_id=user_id, strategy_id=strategy_id)
        if strategy is None:
            raise SignalAccessDeniedError("strategy does not belong to current user")

        strategy_owner = self._strategy_field(strategy, "userId", None)
        if strategy_owner is None:
            strategy_owner = self._strategy_field(strategy, "user_id", None)
        if strategy_owner is not None and str(strategy_owner) != user_id:
            raise SignalAccessDeniedError("strategy does not belong to current user")

        status_raw = self._strategy_field(strategy, "status", "active")
        status = str(status_raw or "active").lower()
        template_raw = self._strategy_field(strategy, "template", "")
        template = str(template_raw or "").strip().lower()

        parameters_raw = self._strategy_field(strategy, "parameters", {})
        parameters = parameters_raw if isinstance(parameters_raw, dict) else {}

        generated: list[TradingSignal] = []
        skipped: list[dict[str, Any]] = []

        normalized_symbols = [symbol.strip().upper() for symbol in symbols if str(symbol).strip()]
        if status != "active":
            for symbol in normalized_symbols:
                skipped.append(
                    {
                        "symbol": symbol,
                        "reason": "strategy_inactive",
                        "metadata": {"strategyStatus": status},
                    }
                )
            return {
                "strategyId": strategy_id,
                "accountId": account_id,
                "template": template,
                "signals": generated,
                "skipped": skipped,
            }

        for symbol in normalized_symbols:
            history_rows = self._call_market_history_reader(
                user_id=user_id,
                symbol=symbol,
                timeframe=timeframe,
                limit=None,
            )
            close_prices = self._extract_close_prices(history_rows)
            decision = self._evaluate_by_template(
                template=template,
                parameters=parameters,
                close_prices=close_prices,
            )

            action = str(decision.get("decision") or "skip").upper()
            if action in {"BUY", "SELL"}:
                signal_metadata = dict(decision.get("metadata") or {})
                signal_metadata["reason"] = str(decision.get("reason") or "strategy_signal")
                signal_metadata["triggered_indicator"] = str(
                    decision.get("triggered_indicator") or template or "unknown"
                )
                signal = self.create_signal(
                    user_id=user_id,
                    strategy_id=strategy_id,
                    account_id=account_id,
                    symbol=symbol,
                    side=action,
                    expires_at=expires_at,
                    metadata=signal_metadata,
                )
                generated.append(signal)
                continue

            skipped_item = {
                "symbol": symbol,
                "reason": str(decision.get("reason") or "no_signal"),
            }
            metadata = dict(decision.get("metadata") or {})
            if metadata:
                skipped_item["metadata"] = metadata
            skipped.append(skipped_item)

        return {
            "strategyId": strategy_id,
            "accountId": account_id,
            "template": template,
            "signals": generated,
            "skipped": skipped,
        }

    def get_signal(self, *, user_id: str, signal_id: str) -> TradingSignal | None:
        return self._repository.get_signal(signal_id=signal_id, user_id=user_id)

    def get_signal_detail(self, *, user_id: str, signal_id: str) -> TradingSignal:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )
        return signal

    def list_signals(
        self,
        *,
        user_id: str,
        keyword: str | None = None,
        strategy_id: str | None = None,
        account_id: str | None = None,
        symbol: str | None = None,
        status: str | None = None,
    ) -> list[TradingSignal]:
        return self._repository.list_signals(
            user_id=user_id,
            keyword=keyword,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            status=status,
        )

    def list_pending_signals(self, *, user_id: str) -> list[TradingSignal]:
        return self.list_signals(user_id=user_id, status="pending")

    def list_expired_signals(self, *, user_id: str) -> list[TradingSignal]:
        return self.list_signals(user_id=user_id, status="expired")

    def search_signals(
        self,
        *,
        user_id: str,
        keyword: str | None = None,
        strategy_id: str | None = None,
        account_id: str | None = None,
        symbol: str | None = None,
        status: str | None = None,
    ) -> list[TradingSignal]:
        return self.list_signals(
            user_id=user_id,
            keyword=keyword,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            status=status,
        )

    def signal_dashboard(
        self,
        *,
        user_id: str,
        keyword: str | None = None,
        strategy_id: str | None = None,
        account_id: str | None = None,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        signals = self.search_signals(
            user_id=user_id,
            keyword=keyword,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
        )
        overall = self._signal_stats(signals)

        by_account_group: dict[str, list[TradingSignal]] = {}
        for signal in signals:
            account_signals = by_account_group.setdefault(signal.account_id, [])
            account_signals.append(signal)

        by_account: list[dict[str, Any]] = []
        for key in sorted(by_account_group.keys()):
            item = {"accountId": key}
            item.update(self._signal_stats(by_account_group[key]))
            by_account.append(item)

        result = dict(overall)
        result["byAccount"] = by_account
        return result

    def account_statistics(self, *, user_id: str, account_id: str) -> dict[str, Any]:
        self._assert_account_acl(user_id=user_id, account_id=account_id)
        signals = self.list_signals(user_id=user_id, account_id=account_id)
        payload = {"accountId": account_id}
        payload.update(self._signal_stats(signals))
        return payload

    def execute_signal(
        self,
        *,
        user_id: str,
        signal_id: str,
        execution_metrics: dict[str, float] | None = None,
    ) -> TradingSignal:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )
        if signal.status != "pending":
            return signal

        signal.execute()
        self._repository.save_signal(signal)
        self._repository.save_execution(
            ExecutionRecord.create(
                user_id=user_id,
                signal_id=signal.id,
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                status="executed",
                metrics=execution_metrics,
            )
        )
        return signal

    def process_signal(self, *, user_id: str, signal_id: str) -> tuple[TradingSignal, dict[str, Any]]:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )

        risk: dict[str, Any] = {"passed": True}
        if self._risk_checker is not None:
            risk = dict(
                self._risk_checker(
                    user_id=user_id,
                    account_id=signal.account_id,
                    strategy_id=signal.strategy_id,
                )
            )

        if signal.status != "pending":
            return signal, risk

        if not risk.get("passed", True):
            return self.cancel_signal(user_id=user_id, signal_id=signal_id), risk

        execution_metrics: dict[str, float] = {}
        risk_score = risk.get("riskScore")
        if isinstance(risk_score, (int, float)):
            execution_metrics["riskScore"] = float(risk_score)

        return (
            self.execute_signal(
                user_id=user_id,
                signal_id=signal_id,
                execution_metrics=execution_metrics or None,
            ),
            risk,
        )

    def cancel_signal(self, *, user_id: str, signal_id: str) -> TradingSignal:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )
        if signal.status != "pending":
            return signal

        signal.cancel()
        self._repository.save_signal(signal)
        self._repository.save_execution(
            ExecutionRecord.create(
                user_id=user_id,
                signal_id=signal.id,
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                status="cancelled",
            )
        )
        return signal

    def expire_signal(self, *, user_id: str, signal_id: str) -> TradingSignal:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )
        if signal.status != "pending":
            return signal

        signal.expire()
        self._repository.save_signal(signal)
        self._repository.save_execution(
            ExecutionRecord.create(
                user_id=user_id,
                signal_id=signal.id,
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                status="expired",
            )
        )
        return signal

    def _run_batch(
        self,
        *,
        user_id: str,
        signal_ids: list[str],
        action: str,
        idempotency_key: str | None = None,
    ) -> dict:
        if idempotency_key:
            fingerprint = self._idempotency_fingerprint(signal_ids=signal_ids)
            existed = self._repository.get_batch_record(
                user_id=user_id,
                action=action,
                idempotency_key=idempotency_key,
            )
            if existed is not None:
                stored_fingerprint, stored_result = existed
                if stored_fingerprint != fingerprint:
                    raise BatchIdempotencyConflictError("idempotency key already exists")
                replay = dict(stored_result)
                replay["idempotent"] = True
                return replay
        else:
            fingerprint = ""

        results: list[dict] = []
        success = 0
        skipped = 0
        denied = 0

        for signal_id in signal_ids:
            signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
            if signal is None:
                denied += 1
                results.append({"signalId": signal_id, "status": "denied"})
                continue

            try:
                self._assert_signal_acl(
                    user_id=user_id,
                    strategy_id=signal.strategy_id,
                    account_id=signal.account_id,
                )
            except SignalAccessDeniedError:
                denied += 1
                results.append({"signalId": signal_id, "status": "denied"})
                continue

            if action == "execute":
                if signal.status == "pending":
                    self.execute_signal(user_id=user_id, signal_id=signal_id)
                    success += 1
                    results.append({"signalId": signal_id, "status": "executed"})
                else:
                    skipped += 1
                    results.append({"signalId": signal_id, "status": "skipped"})
            else:
                if signal.status == "pending":
                    self.cancel_signal(user_id=user_id, signal_id=signal_id)
                    success += 1
                    results.append({"signalId": signal_id, "status": "cancelled"})
                else:
                    skipped += 1
                    results.append({"signalId": signal_id, "status": "skipped"})

        if action == "execute":
            result = {
                "total": len(signal_ids),
                "executed": success,
                "skipped": skipped,
                "denied": denied,
                "results": results,
                "idempotent": False,
            }
        else:
            result = {
                "total": len(signal_ids),
                "cancelled": success,
                "skipped": skipped,
                "denied": denied,
                "results": results,
                "idempotent": False,
            }

        if idempotency_key:
            self._repository.save_batch_record(
                user_id=user_id,
                action=action,
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                result=result,
            )
        return result

    def batch_execute_signals(
        self,
        *,
        user_id: str,
        signal_ids: list[str],
        idempotency_key: str | None = None,
    ) -> dict:
        return self._run_batch(
            user_id=user_id,
            signal_ids=signal_ids,
            action="execute",
            idempotency_key=idempotency_key,
        )

    def batch_cancel_signals(
        self,
        *,
        user_id: str,
        signal_ids: list[str],
        idempotency_key: str | None = None,
    ) -> dict:
        return self._run_batch(
            user_id=user_id,
            signal_ids=signal_ids,
            action="cancel",
            idempotency_key=idempotency_key,
        )

    def list_executions(
        self,
        *,
        user_id: str,
        signal_id: str | None = None,
        status: str | None = None,
    ) -> list[ExecutionRecord]:
        return self._repository.list_executions(user_id=user_id, signal_id=signal_id, status=status)

    def get_execution(self, *, user_id: str, execution_id: str) -> ExecutionRecord:
        execution = self._repository.get_execution(execution_id=execution_id, user_id=user_id)
        if execution is None:
            raise SignalAccessDeniedError("signal does not belong to current user")
        return execution

    def list_running_executions(self, *, user_id: str) -> list[TradingSignal]:
        signals = self._repository.list_signals(user_id=user_id)
        return [item for item in signals if item.status in {"pending", "running"}]

    def execution_trend(self, *, user_id: str) -> dict:
        executions = self._repository.list_executions(user_id=user_id)
        return {
            "total": len(executions),
            "executed": sum(1 for item in executions if item.status == "executed"),
            "cancelled": sum(1 for item in executions if item.status == "cancelled"),
            "expired": sum(1 for item in executions if item.status == "expired"),
        }

    def daily_trend(
        self,
        *,
        user_id: str,
        days: int,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        if days <= 0:
            raise ValueError("days must be positive")

        now_ts = now or datetime.now(timezone.utc)
        start_date = now_ts.date() - timedelta(days=days - 1)
        executions = self._repository.list_executions(user_id=user_id)
        buckets: dict[str, list[ExecutionRecord]] = {}

        for record in executions:
            day = record.created_at.date()
            if day < start_date:
                continue
            key = day.isoformat()
            buckets.setdefault(key, []).append(record)

        series: list[dict[str, Any]] = []
        for key in sorted(buckets.keys()):
            items = buckets[key]
            series.append(
                {
                    "date": key,
                    "total": len(items),
                    "executed": sum(1 for item in items if item.status == "executed"),
                    "cancelled": sum(1 for item in items if item.status == "cancelled"),
                    "expired": sum(1 for item in items if item.status == "expired"),
                }
            )

        return series

    def performance_statistics(
        self,
        *,
        user_id: str,
        strategy_id: str | None = None,
        symbol: str | None = None,
    ) -> dict:
        executions = self._repository.list_executions(user_id=user_id, status="executed")
        if strategy_id is not None:
            executions = [item for item in executions if item.strategy_id == strategy_id]
        if symbol is not None:
            executions = [item for item in executions if item.symbol == symbol]

        pnls = [float(item.metrics.get("pnl", 0.0)) for item in executions if "pnl" in item.metrics]
        latencies = [
            float(item.metrics.get("latencyMs", 0.0)) for item in executions if "latencyMs" in item.metrics
        ]

        return {
            "totalExecutions": len(executions),
            "averagePnl": self._average(pnls),
            "averageLatencyMs": self._average(latencies),
        }

    def performance_statistics_by_strategy(self, *, user_id: str) -> list[dict[str, Any]]:
        executions = self._repository.list_executions(user_id=user_id, status="executed")

        grouped: dict[str, list[ExecutionRecord]] = {}
        for record in executions:
            grouped.setdefault(record.strategy_id, []).append(record)

        result: list[dict[str, Any]] = []
        for strategy_id in sorted(grouped.keys()):
            metrics = self.performance_statistics(user_id=user_id, strategy_id=strategy_id)
            metrics_payload = dict(metrics)
            metrics_payload["strategyId"] = strategy_id
            result.append(metrics_payload)

        return result

    def strategy_execution_statistics(self, *, user_id: str, strategy_id: str) -> dict[str, Any]:
        self._assert_strategy_acl(user_id=user_id, strategy_id=strategy_id)

        executions = [
            item
            for item in self._repository.list_executions(user_id=user_id)
            if item.strategy_id == strategy_id
        ]
        executed_items = [item for item in executions if item.status == "executed"]

        pnls = [float(item.metrics.get("pnl", 0.0)) for item in executed_items if "pnl" in item.metrics]
        latencies = [
            float(item.metrics.get("latencyMs", 0.0))
            for item in executed_items
            if "latencyMs" in item.metrics
        ]

        return {
            "strategyId": strategy_id,
            "totalExecutions": len(executions),
            "pending": sum(1 for item in executions if item.status == "pending"),
            "executed": sum(1 for item in executions if item.status == "executed"),
            "cancelled": sum(1 for item in executions if item.status == "cancelled"),
            "expired": sum(1 for item in executions if item.status == "expired"),
            "averagePnl": self._average(pnls),
            "averageLatencyMs": self._average(latencies),
        }

    def strategy_execution_trend(
        self,
        *,
        user_id: str,
        strategy_id: str,
        days: int,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        if days <= 0:
            raise ValueError("days must be positive")

        self._assert_strategy_acl(user_id=user_id, strategy_id=strategy_id)
        now_ts = now or datetime.now(timezone.utc)
        start_date = now_ts.date() - timedelta(days=days - 1)

        executions = self._repository.list_executions(user_id=user_id)
        buckets: dict[str, list[ExecutionRecord]] = {}

        for record in executions:
            if record.strategy_id != strategy_id:
                continue
            day = record.created_at.date()
            if day < start_date:
                continue
            key = day.isoformat()
            buckets.setdefault(key, []).append(record)

        series: list[dict[str, Any]] = []
        for key in sorted(buckets.keys()):
            items = buckets[key]
            series.append(
                {
                    "date": key,
                    "total": len(items),
                    "pending": sum(1 for item in items if item.status == "pending"),
                    "executed": sum(1 for item in items if item.status == "executed"),
                    "cancelled": sum(1 for item in items if item.status == "cancelled"),
                    "expired": sum(1 for item in items if item.status == "expired"),
                }
            )

        return series

    def signal_performance(self, *, user_id: str, signal_id: str) -> dict[str, Any]:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )

        executions = self._repository.list_executions(
            user_id=user_id,
            signal_id=signal_id,
            status="executed",
        )
        pnls = [float(item.metrics.get("pnl", 0.0)) for item in executions if "pnl" in item.metrics]

        average_pnl = 0.0
        if pnls:
            average_pnl = round(sum(pnls) / len(pnls), 4)

        return {
            "signalId": signal_id,
            "strategyId": signal.strategy_id,
            "symbol": signal.symbol,
            "totalExecutions": len(executions),
            "averagePnl": average_pnl,
        }

    def cleanup_signals(self, *, user_id: str) -> int:
        return self._repository.delete_signals_by_user(user_id=user_id)

    def update_expired_signals(self, *, user_id: str, now: datetime | None = None) -> int:
        now_ts = now or datetime.now(timezone.utc)
        signals = self._repository.list_signals(user_id=user_id)
        expired_count = 0
        for signal in signals:
            if signal.status != "pending":
                continue
            if signal.expires_at is None or signal.expires_at > now_ts:
                continue
            signal.expire()
            expired_count += 1
            self._repository.save_signal(signal)
            self._repository.save_execution(
                ExecutionRecord.create(
                    user_id=user_id,
                    signal_id=signal.id,
                    strategy_id=signal.strategy_id,
                    symbol=signal.symbol,
                    status="expired",
                )
            )
        return expired_count

    def cleanup_expired_signals(self, *, user_id: str) -> int:
        return self._repository.delete_expired_signals_by_user(user_id=user_id)

    def cleanup_all_signals(
        self,
        *,
        user_id: str,
        is_admin: bool,
        admin_decision_source: str = "unknown",
        confirmation_token: str | None = None,
    ) -> int:
        if self._governance_checker is not None:
            self._ensure_admin(
                actor_id=user_id,
                is_admin=is_admin,
                admin_decision_source=admin_decision_source,
                confirmation_token=confirmation_token,
                action="signals.cleanup_all",
                target="signals",
                context={
                    "actor": user_id,
                    "token": confirmation_token or "",
                },
            )
        else:
            self._ensure_admin(
                actor_id=user_id,
                is_admin=is_admin,
                admin_decision_source=admin_decision_source,
                confirmation_token=confirmation_token,
                action="signals.cleanup_all",
                target="signals",
                context=None,
            )

        return self._repository.delete_all_signals()

    def cleanup_execution_history(
        self,
        *,
        user_id: str,
        is_admin: bool,
        retention_days: int,
        admin_decision_source: str = "unknown",
        confirmation_token: str | None = None,
        audit_id: str,
        now: datetime | None = None,
    ) -> int:
        if retention_days <= 0:
            raise ValueError("retention_days must be positive")

        cutoff_base = now or datetime.now(timezone.utc)
        cutoff = cutoff_base - timedelta(days=retention_days)

        self._ensure_admin(
            actor_id=user_id,
            is_admin=is_admin,
            admin_decision_source=admin_decision_source,
            confirmation_token=confirmation_token,
            action="signals.cleanup_execution_history",
            target="signals.executions",
            context={
                "actor": user_id,
                "retentionDays": retention_days,
                "cutoff": cutoff.isoformat(),
                "auditId": audit_id,
                "token": confirmation_token or "",
            },
        )

        return self._repository.delete_executions_before(cutoff=cutoff)
