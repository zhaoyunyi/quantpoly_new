"""回测任务服务。"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any, Protocol

from platform_core.callback_contract import require_explicit_keyword_parameters

from backtest_runner.domain import BacktestTask
from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.result_store import InMemoryBacktestResultStore


class BacktestIdempotencyConflictError(RuntimeError):
    """回测任务幂等键冲突。"""


class BacktestAccessDeniedError(PermissionError):
    """无权访问回测任务。"""


class BacktestDispatchError(RuntimeError):
    """回测任务提交到编排系统失败。"""


class BacktestDeleteInvalidStateError(RuntimeError):
    """回测任务状态不允许删除。"""


class BacktestExecutionError(RuntimeError):
    """回测引擎执行失败。"""

    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class BacktestDispatcher(Protocol):
    def submit_backtest(self, task: BacktestTask) -> str:
        """向编排系统提交回测任务并返回 job_id。"""


class BacktestResultStore(Protocol):
    def save_result(self, *, user_id: str, task_id: str, result: dict[str, Any]) -> None:
        """保存回测结果。"""

    def get_result(self, *, user_id: str, task_id: str) -> dict[str, Any] | None:
        """读取回测结果。"""

    def delete_result(self, *, user_id: str, task_id: str) -> bool:
        """删除回测结果。"""


class BacktestService:
    def __init__(
        self,
        *,
        repository: InMemoryBacktestRepository,
        on_task_created: Callable[[BacktestTask], None] | None = None,
        dispatcher: BacktestDispatcher | None = None,
        strategy_owner_acl: Callable[[str, str], bool] | None = None,
        result_store: BacktestResultStore | None = None,
        strategy_reader: Callable[..., Any] | None = None,
        market_history_reader: Callable[..., Any] | None = None,
    ) -> None:
        self._repository = repository
        self._on_task_created = on_task_created
        self._dispatcher = dispatcher
        self._strategy_owner_acl = strategy_owner_acl or (lambda _user_id, _strategy_id: True)
        self._result_store = result_store or InMemoryBacktestResultStore()
        self._strategy_reader = strategy_reader
        self._market_history_reader = market_history_reader

        require_explicit_keyword_parameters(
            self._strategy_reader,
            required=["user_id", "strategy_id"],
            callback_name="strategy_reader",
        )
        require_explicit_keyword_parameters(
            self._market_history_reader,
            required=["user_id", "symbol", "start_date", "end_date", "timeframe", "limit"],
            callback_name="market_history_reader",
        )

    @staticmethod
    def _strategy_field(strategy: Any, key: str, default: Any = None) -> Any:
        if isinstance(strategy, dict):
            return strategy.get(key, default)
        return getattr(strategy, key, default)

    @staticmethod
    def _to_positive_int(value: Any, *, fallback: int | None = None) -> int | None:
        candidate = value if value is not None else fallback
        if candidate is None:
            return None
        try:
            parsed = int(candidate)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed

    @staticmethod
    def _to_non_negative_float(value: Any, *, fallback: float | None = None) -> float | None:
        candidate = value if value is not None else fallback
        if candidate is None:
            return None
        try:
            parsed = float(candidate)
        except (TypeError, ValueError):
            return None
        if parsed < 0:
            return None
        return parsed

    @staticmethod
    def _extract_close_prices(rows: Any) -> list[float]:
        if rows is None:
            return []

        prices: list[float] = []
        for row in list(rows):
            value: Any = None
            if isinstance(row, dict):
                value = row.get("close")
                if value is None:
                    value = row.get("close_price")
                if value is None:
                    value = row.get("c")
            else:
                for key in ("close_price", "close", "c"):
                    if hasattr(row, key):
                        value = getattr(row, key)
                        if value is not None:
                            break

            if value is None:
                continue

            try:
                prices.append(float(value))
            except (TypeError, ValueError):
                continue

        return prices

    def _call_strategy_reader(self, *, user_id: str, strategy_id: str) -> Any:
        if self._strategy_reader is None:
            return None

        return self._strategy_reader(user_id=user_id, strategy_id=strategy_id)

    def _call_market_history_reader(
        self,
        *,
        user_id: str,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
        timeframe: str,
        limit: int | None,
    ) -> Any:
        if self._market_history_reader is None:
            return None

        return self._market_history_reader(
            user_id=user_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            limit=limit,
        )

    @staticmethod
    def _moving_average_events(
        *,
        close_prices: list[float],
        short_window: int,
        long_window: int,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if len(close_prices) < long_window + 1:
            return events

        for idx in range(long_window, len(close_prices)):
            prev_short = sum(close_prices[idx - short_window : idx]) / float(short_window)
            prev_long = sum(close_prices[idx - long_window : idx]) / float(long_window)
            curr_short = sum(close_prices[idx - short_window + 1 : idx + 1]) / float(short_window)
            curr_long = sum(close_prices[idx - long_window + 1 : idx + 1]) / float(long_window)

            if prev_short <= prev_long and curr_short > curr_long:
                events.append(
                    {
                        "index": idx,
                        "side": "BUY",
                        "reason": "moving_average_bullish_cross",
                        "triggered_indicator": "moving_average",
                        "metadata": {
                            "shortWindow": short_window,
                            "longWindow": long_window,
                            "shortAverage": curr_short,
                            "longAverage": curr_long,
                        },
                    }
                )
            elif prev_short >= prev_long and curr_short < curr_long:
                events.append(
                    {
                        "index": idx,
                        "side": "SELL",
                        "reason": "moving_average_bearish_cross",
                        "triggered_indicator": "moving_average",
                        "metadata": {
                            "shortWindow": short_window,
                            "longWindow": long_window,
                            "shortAverage": curr_short,
                            "longAverage": curr_long,
                        },
                    }
                )

        return events

    @staticmethod
    def _mean_reversion_events(
        *,
        close_prices: list[float],
        window: int,
        entry_z: float,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if len(close_prices) < window:
            return events

        for idx in range(window - 1, len(close_prices)):
            current_window = close_prices[idx - window + 1 : idx + 1]
            mean_price = sum(current_window) / float(window)
            variance = sum((item - mean_price) ** 2 for item in current_window) / float(window)
            deviation = math.sqrt(variance)
            if deviation == 0:
                continue

            z_score = (close_prices[idx] - mean_price) / deviation
            if z_score <= -entry_z:
                events.append(
                    {
                        "index": idx,
                        "side": "BUY",
                        "reason": "mean_reversion_oversold",
                        "triggered_indicator": "mean_reversion",
                        "metadata": {
                            "window": window,
                            "entryZ": entry_z,
                            "zScore": z_score,
                        },
                    }
                )
            elif z_score >= entry_z:
                events.append(
                    {
                        "index": idx,
                        "side": "SELL",
                        "reason": "mean_reversion_overbought",
                        "triggered_indicator": "mean_reversion",
                        "metadata": {
                            "window": window,
                            "entryZ": entry_z,
                            "zScore": z_score,
                        },
                    }
                )

        return events

    @staticmethod
    def _equity_metrics(*, initial_capital: float, equity_curve: list[dict[str, float]], daily_returns: list[float], sell_pnls: list[float]) -> dict[str, float]:
        if not equity_curve:
            return {
                "returnRate": 0.0,
                "maxDrawdown": 0.0,
                "sharpeRatio": 0.0,
                "tradeCount": 0.0,
                "winRate": 0.0,
            }

        final_equity = float(equity_curve[-1]["equity"])
        return_rate = (final_equity - initial_capital) / initial_capital if initial_capital > 0 else 0.0

        peak = float(equity_curve[0]["equity"])
        max_drawdown = 0.0
        for point in equity_curve:
            equity = float(point["equity"])
            if equity > peak:
                peak = equity
            if peak > 0:
                drawdown = (peak - equity) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        sharpe_ratio = 0.0
        if len(daily_returns) >= 2:
            avg_return = sum(daily_returns) / len(daily_returns)
            variance = sum((item - avg_return) ** 2 for item in daily_returns) / (len(daily_returns) - 1)
            std_dev = math.sqrt(max(variance, 0.0))
            if std_dev > 0:
                sharpe_ratio = (avg_return / std_dev) * math.sqrt(252.0)

        trade_count = float(len(sell_pnls))
        win_rate = 0.0
        if sell_pnls:
            win_rate = float(sum(1 for item in sell_pnls if item > 0)) / float(len(sell_pnls))

        return {
            "returnRate": float(return_rate),
            "maxDrawdown": float(max_drawdown),
            "sharpeRatio": float(sharpe_ratio),
            "tradeCount": float(trade_count),
            "winRate": float(win_rate),
        }

    def _simulate_backtest(
        self,
        *,
        symbol: str,
        close_prices: list[float],
        events: list[dict[str, Any]],
        initial_capital: float,
        commission_rate: float,
    ) -> dict[str, Any]:
        events_by_index: dict[int, list[dict[str, Any]]] = {}
        for event in events:
            index = int(event.get("index", -1))
            if index < 0:
                continue
            events_by_index.setdefault(index, []).append(event)

        cash = initial_capital
        position_qty = 0.0
        entry_cost = 0.0
        equity_curve: list[dict[str, float]] = []
        daily_returns: list[float] = []
        trades: list[dict[str, Any]] = []
        sell_pnls: list[float] = []

        for idx, price in enumerate(close_prices):
            day_events = events_by_index.get(idx, [])
            for event in day_events:
                side = str(event.get("side") or "").upper()
                if side == "BUY" and position_qty <= 0 and price > 0 and cash > 0:
                    invested_cash = cash
                    fee = invested_cash * commission_rate
                    net_cash = invested_cash - fee
                    if net_cash <= 0:
                        continue
                    position_qty = net_cash / price
                    entry_cost = invested_cash + fee
                    cash = 0.0
                    trades.append(
                        {
                            "index": idx,
                            "symbol": symbol,
                            "side": "BUY",
                            "price": float(price),
                            "quantity": float(position_qty),
                            "reason": event.get("reason"),
                            "triggered_indicator": event.get("triggered_indicator"),
                            "metadata": dict(event.get("metadata") or {}),
                        }
                    )

                if side == "SELL" and position_qty > 0:
                    gross = position_qty * price
                    fee = gross * commission_rate
                    cash = gross - fee
                    pnl = cash - entry_cost
                    sell_pnls.append(float(pnl))
                    trades.append(
                        {
                            "index": idx,
                            "symbol": symbol,
                            "side": "SELL",
                            "price": float(price),
                            "quantity": float(position_qty),
                            "reason": event.get("reason"),
                            "triggered_indicator": event.get("triggered_indicator"),
                            "pnl": float(pnl),
                            "metadata": dict(event.get("metadata") or {}),
                        }
                    )
                    position_qty = 0.0
                    entry_cost = 0.0

            equity = cash + (position_qty * price)
            equity_curve.append({"index": float(idx), "equity": float(equity)})

            if len(equity_curve) >= 2:
                previous = float(equity_curve[-2]["equity"])
                current = float(equity_curve[-1]["equity"])
                if previous == 0:
                    daily_returns.append(0.0)
                else:
                    daily_returns.append((current - previous) / previous)

        if position_qty > 0 and close_prices:
            final_price = close_prices[-1]
            gross = position_qty * final_price
            fee = gross * commission_rate
            cash = gross - fee
            pnl = cash - entry_cost
            sell_pnls.append(float(pnl))
            trades.append(
                {
                    "index": float(len(close_prices) - 1),
                    "symbol": symbol,
                    "side": "SELL",
                    "price": float(final_price),
                    "quantity": float(position_qty),
                    "reason": "force_close",
                    "triggered_indicator": "engine",
                    "pnl": float(pnl),
                    "metadata": {},
                }
            )
            position_qty = 0.0
            entry_cost = 0.0
            if equity_curve:
                equity_curve[-1]["equity"] = float(cash)

        metrics = self._equity_metrics(
            initial_capital=initial_capital,
            equity_curve=equity_curve,
            daily_returns=daily_returns,
            sell_pnls=sell_pnls,
        )

        return {
            "equityCurve": equity_curve,
            "dailyReturns": [float(item) for item in daily_returns],
            "trades": trades,
            "metrics": metrics,
        }

    def _build_engine_input(self, *, user_id: str, task: BacktestTask) -> dict[str, Any]:
        config = dict(task.config or {})

        strategy = self._call_strategy_reader(user_id=user_id, strategy_id=task.strategy_id)
        if strategy is None and self._strategy_reader is not None:
            raise BacktestExecutionError(code="BACKTEST_STRATEGY_NOT_FOUND", message="strategy not found")

        if strategy is None:
            strategy = {
                "id": task.strategy_id,
                "userId": user_id,
                "status": config.get("strategyStatus", "active"),
                "template": config.get("template", "moving_average"),
                "parameters": dict(config.get("parameters") or {}),
            }

        strategy_owner = self._strategy_field(strategy, "userId", None)
        if strategy_owner is None:
            strategy_owner = self._strategy_field(strategy, "user_id", None)
        if strategy_owner is not None and str(strategy_owner) != user_id:
            raise BacktestExecutionError(
                code="BACKTEST_STRATEGY_NOT_FOUND",
                message="strategy not found",
            )

        strategy_status = str(self._strategy_field(strategy, "status", "active") or "active").lower()
        if strategy_status != "active":
            raise BacktestExecutionError(
                code="BACKTEST_STRATEGY_INACTIVE",
                message="strategy is not executable",
            )

        template_value = self._strategy_field(strategy, "template", None)
        if template_value in {None, ""}:
            template_value = self._strategy_field(strategy, "templateId", None)
        if template_value in {None, ""}:
            template_value = self._strategy_field(strategy, "template_id", "")
        template = str(template_value or "").strip().lower()
        parameters = self._strategy_field(strategy, "parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}

        symbol = str(config.get("symbol") or "").strip().upper()
        if not symbol:
            symbols = config.get("symbols")
            if isinstance(symbols, list) and symbols:
                symbol = str(symbols[0]).strip().upper()
        if not symbol:
            raise BacktestExecutionError(code="BACKTEST_INVALID_CONFIG", message="config missing symbol")

        timeframe = str(config.get("timeframe") or "1Day")
        start_date = config.get("startDate")
        end_date = config.get("endDate")

        history_rows = self._call_market_history_reader(
            user_id=user_id,
            symbol=symbol,
            start_date=str(start_date) if start_date is not None else None,
            end_date=str(end_date) if end_date is not None else None,
            timeframe=timeframe,
            limit=None,
        )

        if history_rows is None and self._market_history_reader is None:
            inline_prices = config.get("prices")
            if isinstance(inline_prices, list):
                history_rows = [{"close": item} for item in inline_prices]

        if history_rows is None:
            raise BacktestExecutionError(
                code="BACKTEST_HISTORY_UNAVAILABLE",
                message="market history reader is not configured",
            )

        close_prices = self._extract_close_prices(history_rows)
        if not close_prices:
            inline_prices = config.get("prices")
            if isinstance(inline_prices, list):
                close_prices = self._extract_close_prices([{"close": item} for item in inline_prices])

        initial_capital = self._to_non_negative_float(config.get("initialCapital"), fallback=100000.0)
        if initial_capital is None or initial_capital <= 0:
            raise BacktestExecutionError(
                code="BACKTEST_INVALID_CONFIG",
                message="initialCapital must be positive",
            )

        commission_rate = self._to_non_negative_float(config.get("commissionRate"), fallback=0.0)
        if commission_rate is None:
            raise BacktestExecutionError(
                code="BACKTEST_INVALID_CONFIG",
                message="commissionRate must be non-negative",
            )

        return {
            "symbol": symbol,
            "template": template,
            "parameters": parameters,
            "timeframe": timeframe,
            "startDate": start_date,
            "endDate": end_date,
            "closePrices": close_prices,
            "initialCapital": float(initial_capital),
            "commissionRate": float(commission_rate),
        }

    def _run_backtest_engine(self, *, user_id: str, task: BacktestTask) -> dict[str, Any]:
        engine_input = self._build_engine_input(user_id=user_id, task=task)
        close_prices = engine_input["closePrices"]
        template = str(engine_input["template"])
        parameters = dict(engine_input["parameters"])

        if template == "moving_average":
            short_window = self._to_positive_int(parameters.get("shortWindow"), fallback=5)
            long_window = self._to_positive_int(parameters.get("longWindow"), fallback=20)
            if short_window is None or long_window is None or short_window >= long_window:
                raise BacktestExecutionError(
                    code="BACKTEST_INVALID_PARAMETERS",
                    message="moving_average parameters invalid",
                )
            if len(close_prices) < long_window + 1:
                raise BacktestExecutionError(
                    code="BACKTEST_INSUFFICIENT_DATA",
                    message="insufficient_data",
                )
            events = self._moving_average_events(
                close_prices=close_prices,
                short_window=short_window,
                long_window=long_window,
            )
        elif template == "mean_reversion":
            window = self._to_positive_int(parameters.get("window"), fallback=20)
            entry_z = self._to_non_negative_float(parameters.get("entryZ"), fallback=1.5)
            if window is None or entry_z is None or entry_z <= 0:
                raise BacktestExecutionError(
                    code="BACKTEST_INVALID_PARAMETERS",
                    message="mean_reversion parameters invalid",
                )
            if len(close_prices) < window:
                raise BacktestExecutionError(
                    code="BACKTEST_INSUFFICIENT_DATA",
                    message="insufficient_data",
                )
            events = self._mean_reversion_events(
                close_prices=close_prices,
                window=window,
                entry_z=float(entry_z),
            )
        else:
            raise BacktestExecutionError(
                code="BACKTEST_UNSUPPORTED_TEMPLATE",
                message=f"unsupported template: {template}",
            )

        simulated = self._simulate_backtest(
            symbol=engine_input["symbol"],
            close_prices=close_prices,
            events=events,
            initial_capital=float(engine_input["initialCapital"]),
            commission_rate=float(engine_input["commissionRate"]),
        )

        return {
            "taskId": task.id,
            "strategyId": task.strategy_id,
            "symbol": engine_input["symbol"],
            "template": template,
            "timeframe": engine_input["timeframe"],
            "startDate": engine_input["startDate"],
            "endDate": engine_input["endDate"],
            "equityCurve": simulated["equityCurve"],
            "dailyReturns": simulated["dailyReturns"],
            "trades": simulated["trades"],
            "metrics": simulated["metrics"],
        }

    def create_task(
        self,
        *,
        user_id: str,
        strategy_id: str,
        config: dict,
        idempotency_key: str | None = None,
    ) -> BacktestTask:
        if not self._strategy_owner_acl(user_id, strategy_id):
            raise BacktestAccessDeniedError("strategy does not belong to current user")

        if idempotency_key:
            existing = self._repository.find_by_idempotency_key(
                user_id=user_id,
                idempotency_key=idempotency_key,
            )
            if existing is not None:
                raise BacktestIdempotencyConflictError("idempotency key already exists")

        task = BacktestTask.create(
            user_id=user_id,
            strategy_id=strategy_id,
            config=config,
            idempotency_key=idempotency_key,
            display_name=config.get("displayName") if isinstance(config, dict) else None,
        )

        created = self._repository.save_if_absent(task)
        if not created:
            raise BacktestIdempotencyConflictError("idempotency key already exists")

        try:
            if self._dispatcher:
                self._dispatcher.submit_backtest(task)

            if self._on_task_created:
                self._on_task_created(task)
        except BacktestIdempotencyConflictError:
            self._repository.delete(user_id=user_id, task_id=task.id)
            raise
        except Exception as exc:
            self._repository.delete(user_id=user_id, task_id=task.id)
            raise BacktestDispatchError("failed to dispatch backtest task") from exc

        return task

    def execute_task(self, *, user_id: str, task_id: str) -> dict[str, Any]:
        task = self._repository.get_by_id(task_id, user_id=user_id)
        if task is None:
            raise BacktestAccessDeniedError("backtest task does not belong to current user")

        if task.status == "pending":
            task = self.transition(user_id=user_id, task_id=task_id, to_status="running")
            if task is None:
                raise BacktestAccessDeniedError("backtest task does not belong to current user")
        elif task.status != "running":
            raise BacktestExecutionError(
                code="BACKTEST_INVALID_STATE",
                message=f"task status={task.status} is not executable",
            )

        try:
            result = self._run_backtest_engine(user_id=user_id, task=task)
            metrics = result.get("metrics") or {}
            completed = self.transition(
                user_id=user_id,
                task_id=task.id,
                to_status="completed",
                metrics={key: float(value) for key, value in metrics.items()},
            )
            if completed is None:
                raise BacktestAccessDeniedError("backtest task does not belong to current user")
            self._result_store.save_result(user_id=user_id, task_id=completed.id, result=result)
            result["metrics"] = dict(completed.metrics or {})
            return {"task": completed, "result": result}
        except BacktestExecutionError:
            self.transition(user_id=user_id, task_id=task.id, to_status="failed")
            raise
        except Exception as exc:  # noqa: BLE001
            self.transition(user_id=user_id, task_id=task.id, to_status="failed")
            raise BacktestExecutionError(code="BACKTEST_ENGINE_FAILED", message=str(exc)) from exc

    def get_task(self, *, user_id: str, task_id: str) -> BacktestTask | None:
        return self._repository.get_by_id(task_id, user_id=user_id)

    def rename_task(self, *, user_id: str, task_id: str, display_name: str | None) -> BacktestTask | None:
        task = self._repository.get_by_id(task_id, user_id=user_id)
        if task is None:
            return None
        task.rename(display_name=display_name)
        self._repository.save(task)
        return task

    def related_tasks(
        self,
        *,
        user_id: str,
        task_id: str,
        status: str | None = None,
        limit: int = 10,
    ) -> list[BacktestTask]:
        task = self._repository.get_by_id(task_id, user_id=user_id)
        if task is None:
            raise BacktestAccessDeniedError("backtest task does not belong to current user")

        normalized_limit = max(1, limit)
        if hasattr(self._repository, "list_related_by_strategy"):
            return self._repository.list_related_by_strategy(
                user_id=user_id,
                strategy_id=task.strategy_id,
                exclude_task_id=task.id,
                status=status,
                limit=normalized_limit,
            )

        all_items = self._repository.list_by_user(
            user_id=user_id,
            strategy_id=task.strategy_id,
            status=status,
        )
        return [item for item in all_items if item.id != task.id][:normalized_limit]

    def get_task_result(self, *, user_id: str, task_id: str) -> dict[str, Any] | None:
        task = self._repository.get_by_id(task_id, user_id=user_id)
        if task is None:
            raise BacktestAccessDeniedError("backtest task does not belong to current user")
        return self._result_store.get_result(user_id=user_id, task_id=task_id)

    def list_tasks(
        self,
        *,
        user_id: str,
        strategy_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        all_items = self._repository.list_by_user(
            user_id=user_id,
            strategy_id=strategy_id,
            status=status,
        )
        total = len(all_items)
        start = max(page - 1, 0) * page_size
        end = start + page_size
        return {
            "items": all_items[start:end],
            "total": total,
            "page": page,
            "pageSize": page_size,
        }

    def transition(
        self,
        *,
        user_id: str,
        task_id: str,
        to_status: str,
        metrics: dict[str, float] | None = None,
    ) -> BacktestTask | None:
        task = self._repository.get_by_id(task_id, user_id=user_id)
        if task is None:
            return None
        task.transition_to(to_status, metrics=metrics)
        self._repository.save(task)
        return task

    def cancel_task(self, *, user_id: str, task_id: str) -> BacktestTask | None:
        return self.transition(user_id=user_id, task_id=task_id, to_status="cancelled")

    def retry_task(self, *, user_id: str, task_id: str) -> BacktestTask | None:
        return self.transition(user_id=user_id, task_id=task_id, to_status="pending")

    def delete_task(self, *, user_id: str, task_id: str) -> bool:
        task = self._repository.get_by_id(task_id, user_id=user_id)
        if task is None:
            return False

        if task.status not in {"completed", "failed", "cancelled"}:
            raise BacktestDeleteInvalidStateError(
                f"backtest_delete_invalid_state status={task.status}"
            )

        deleted = self._repository.delete(user_id=user_id, task_id=task_id)
        if deleted:
            self._result_store.delete_result(user_id=user_id, task_id=task_id)
        return deleted

    def count_active_backtests(self, *, user_id: str, strategy_id: str) -> int:
        all_items = self._repository.list_by_user(
            user_id=user_id,
            strategy_id=strategy_id,
            status=None,
        )
        return sum(1 for item in all_items if item.status in {"pending", "running"})

    def statistics(self, *, user_id: str, strategy_id: str | None = None) -> dict:
        all_items = self._repository.list_by_user(
            user_id=user_id,
            strategy_id=strategy_id,
            status=None,
        )
        counters = {
            "pendingCount": 0,
            "runningCount": 0,
            "completedCount": 0,
            "failedCount": 0,
            "cancelledCount": 0,
        }
        completed_returns: list[float] = []
        completed_drawdowns: list[float] = []
        completed_win_rates: list[float] = []

        for task in all_items:
            key = f"{task.status}Count"
            if key in counters:
                counters[key] += 1
            if task.status == "completed" and task.metrics:
                if "returnRate" in task.metrics:
                    completed_returns.append(float(task.metrics["returnRate"]))
                if "maxDrawdown" in task.metrics:
                    completed_drawdowns.append(float(task.metrics["maxDrawdown"]))
                if "winRate" in task.metrics:
                    completed_win_rates.append(float(task.metrics["winRate"]))

        def _avg(values: list[float]) -> float:
            if not values:
                return 0.0
            return sum(values) / len(values)

        return {
            **counters,
            "totalCount": len(all_items),
            "averageReturnRate": _avg(completed_returns),
            "averageMaxDrawdown": _avg(completed_drawdowns),
            "averageWinRate": _avg(completed_win_rates),
        }

    def compare_tasks(self, *, user_id: str, task_ids: list[str]) -> dict:
        tasks: list[dict] = []
        return_rates: list[float] = []

        for task_id in task_ids:
            task = self._repository.get_by_id(task_id, user_id=user_id)
            if task is None:
                raise BacktestAccessDeniedError("backtest task does not belong to current user")
            metrics = task.metrics or {}
            if "returnRate" in metrics:
                return_rates.append(float(metrics["returnRate"]))
            tasks.append(
                {
                    "taskId": task.id,
                    "strategyId": task.strategy_id,
                    "status": task.status,
                    "metrics": metrics,
                }
            )

        return {
            "tasks": tasks,
            "summary": {
                "bestReturnRate": max(return_rates) if return_rates else 0.0,
                "worstReturnRate": min(return_rates) if return_rates else 0.0,
            },
        }
