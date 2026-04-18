"""回测引擎轻量封装。"""

from __future__ import annotations

import math
from typing import Any


SUPPORTED_TEMPLATES = frozenset({"moving_average", "mean_reversion"})


class UnsupportedTemplateError(ValueError):
    """策略健康分析不支持的模板。"""


class SimulationConfigurationError(ValueError):
    """策略健康分析参数配置非法。"""


def supports_template(template: str) -> bool:
    return template.strip().lower() in SUPPORTED_TEMPLATES


def _require_supported_template(template: str) -> str:
    normalized = template.strip().lower()
    if normalized not in SUPPORTED_TEMPLATES:
        raise UnsupportedTemplateError(f"unsupported template: {template}")
    return normalized


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
            events.append({"index": idx, "side": "BUY", "reason": "moving_average_bullish_cross"})
        elif prev_short >= prev_long and curr_short < curr_long:
            events.append({"index": idx, "side": "SELL", "reason": "moving_average_bearish_cross"})

    return events


def _mean_reversion_events(
    *,
    close_prices: list[float],
    window: int,
    entry_z: float,
    exit_z: float,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if len(close_prices) < window:
        return events

    in_position = False
    for idx in range(window - 1, len(close_prices)):
        current_window = close_prices[idx - window + 1 : idx + 1]
        mean_price = sum(current_window) / float(window)
        variance = sum((item - mean_price) ** 2 for item in current_window) / float(window)
        deviation = math.sqrt(variance)
        if deviation == 0:
            continue

        z_score = (close_prices[idx] - mean_price) / deviation
        if not in_position and z_score <= -entry_z:
            events.append({"index": idx, "side": "BUY", "reason": "mean_reversion_oversold"})
            in_position = True
        elif in_position and z_score >= -exit_z:
            events.append({"index": idx, "side": "SELL", "reason": "mean_reversion_recovered"})
            in_position = False

    return events


def _simulate_backtest(
    *,
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
                trades.append({"index": idx, "side": "BUY", "price": float(price), "quantity": float(position_qty)})

            if side == "SELL" and position_qty > 0:
                gross = position_qty * price
                fee = gross * commission_rate
                cash = gross - fee
                pnl = cash - entry_cost
                sell_pnls.append(float(pnl))
                trades.append({"index": idx, "side": "SELL", "price": float(price), "quantity": float(position_qty), "pnl": float(pnl)})
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
        trades.append({"index": len(close_prices) - 1, "side": "SELL", "price": float(final_price), "quantity": float(position_qty), "pnl": float(pnl)})
        position_qty = 0.0
        entry_cost = 0.0
        if equity_curve:
            equity_curve[-1]["equity"] = float(cash)

    metrics = _equity_metrics(
        initial_capital=initial_capital,
        equity_curve=equity_curve,
        daily_returns=daily_returns,
        sell_pnls=sell_pnls,
    )

    return {"metrics": metrics, "trades": trades}


def _equity_metrics(
    *,
    initial_capital: float,
    equity_curve: list[dict[str, float]],
    daily_returns: list[float],
    sell_pnls: list[float],
) -> dict[str, float]:
    if not equity_curve:
        return {"returnRate": 0.0, "maxDrawdown": 0.0, "sharpeRatio": 0.0, "tradeCount": 0.0, "winRate": 0.0}

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


def run_simulation(
    close_prices: list[float],
    template: str,
    parameters: dict[str, Any],
    initial_capital: float = 100000.0,
    commission_rate: float = 0.0,
) -> dict[str, Any]:
    """运行单次回测模拟，返回 metrics 和 trades。"""
    normalized_template = _require_supported_template(template)

    if normalized_template == "moving_average":
        short_window = int(parameters.get("shortWindow", 5))
        long_window = int(parameters.get("longWindow", 20))
        if short_window <= 0 or long_window <= 0 or short_window >= long_window:
            raise SimulationConfigurationError("invalid moving_average parameters")
        if len(close_prices) < long_window + 1:
            return {"metrics": {"returnRate": 0.0, "maxDrawdown": 0.0, "sharpeRatio": 0.0, "tradeCount": 0.0, "winRate": 0.0}, "trades": []}
        events = _moving_average_events(close_prices=close_prices, short_window=short_window, long_window=long_window)
    elif normalized_template == "mean_reversion":
        window = int(parameters.get("window", 20))
        entry_z = float(parameters.get("entryZ", 1.5))
        exit_z = float(parameters.get("exitZ", 0.5))
        if window <= 0 or entry_z <= 0 or exit_z < 0 or entry_z <= exit_z:
            raise SimulationConfigurationError("invalid mean_reversion parameters")
        if len(close_prices) < window:
            return {"metrics": {"returnRate": 0.0, "maxDrawdown": 0.0, "sharpeRatio": 0.0, "tradeCount": 0.0, "winRate": 0.0}, "trades": []}
        events = _mean_reversion_events(
            close_prices=close_prices,
            window=window,
            entry_z=entry_z,
            exit_z=exit_z,
        )

    return _simulate_backtest(
        close_prices=close_prices,
        events=events,
        initial_capital=initial_capital,
        commission_rate=commission_rate,
    )
