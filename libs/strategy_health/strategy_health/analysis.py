"""策略健康分析算法。"""

from __future__ import annotations

from typing import Any

from strategy_health.domain import OverfitRisk, SensitivityResult
from strategy_health.engine import run_simulation


def analyze_parameter_sensitivity(
    close_prices: list[float],
    template: str,
    parameters: dict[str, Any],
    initial_capital: float = 100000.0,
    commission_rate: float = 0.0,
) -> list[SensitivityResult]:
    """对每个参数逐个扰动，评估敏感性。"""
    baseline = run_simulation(close_prices, template, parameters, initial_capital, commission_rate)
    baseline_return = float(baseline["metrics"]["returnRate"])

    results: list[SensitivityResult] = []
    perturbations = [-0.5, -0.2, -0.1, 0.1, 0.2, 0.5]

    for param_name, original_value in parameters.items():
        try:
            original_float = float(original_value)
        except (TypeError, ValueError):
            continue

        variations: list[dict[str, Any]] = []
        max_deviation = 0.0

        for pct in perturbations:
            perturbed_value = original_float * (1.0 + pct)
            perturbed_params = dict(parameters)
            perturbed_params[param_name] = perturbed_value

            result = run_simulation(close_prices, template, perturbed_params, initial_capital, commission_rate)
            perturbed_return = float(result["metrics"]["returnRate"])
            deviation = perturbed_return - baseline_return
            change_pct = (deviation / abs(baseline_return) * 100.0) if abs(baseline_return) > 0 else 0.0
            label = f"+{int(pct * 100)}%" if pct > 0 else f"{int(pct * 100)}%"

            variations.append({
                "perturbation": label,
                "value": round(perturbed_value, 4),
                "returnRate": round(perturbed_return, 6),
                "changePercent": round(change_pct, 2),
            })

            if abs(deviation) > max_deviation:
                max_deviation = abs(deviation)

        threshold = abs(baseline_return) * 0.3 if abs(baseline_return) > 0 else 0.01
        if max_deviation > threshold:
            rating = "HIGH"
        else:
            rating = "LOW"

        results.append(SensitivityResult(
            param_name=param_name,
            original_value=original_float,
            variations=variations,
            rating=rating,
        ))

    return results


def analyze_out_of_sample(
    close_prices: list[float],
    template: str,
    parameters: dict[str, Any],
    initial_capital: float = 100000.0,
    commission_rate: float = 0.0,
) -> dict[str, Any]:
    """将数据按 70/30 分割，比较样本内外表现。"""
    split_idx = int(len(close_prices) * 0.7)
    in_sample_prices = close_prices[:split_idx]
    out_sample_prices = close_prices[split_idx:]

    in_result = run_simulation(in_sample_prices, template, parameters, initial_capital, commission_rate)
    out_result = run_simulation(out_sample_prices, template, parameters, initial_capital, commission_rate)

    in_sample_return = float(in_result["metrics"]["returnRate"])
    out_sample_return = float(out_result["metrics"]["returnRate"])

    if abs(in_sample_return) > 0:
        return_ratio = out_sample_return / in_sample_return
    else:
        return_ratio = 1.0 if abs(out_sample_return) < 0.001 else 0.0

    overfit_warning = False
    if in_sample_return > 0 and out_sample_return < in_sample_return * 0.5:
        overfit_warning = True
    elif in_sample_return < 0 and out_sample_return < in_sample_return * 0.5:
        overfit_warning = True

    return {
        "inSampleReturn": in_sample_return,
        "outSampleReturn": out_sample_return,
        "returnRatio": return_ratio,
        "overfitWarning": overfit_warning,
        "inSampleTradeCount": int(in_result["metrics"]["tradeCount"]),
        "outSampleTradeCount": int(out_result["metrics"]["tradeCount"]),
    }


def calculate_overfit_score(
    sensitivity_results: list[SensitivityResult],
    out_of_sample_result: dict[str, Any],
    trade_count: int,
) -> tuple[int, str, list[str]]:
    """计算综合过拟合评分。"""
    warnings: list[str] = []

    total_params = len(sensitivity_results)
    high_sensitivity_count = sum(1 for r in sensitivity_results if r.rating == "HIGH")

    if total_params > 0:
        sensitivity_score = 100.0 - (high_sensitivity_count / total_params) * 100.0
    else:
        sensitivity_score = 100.0

    for r in sensitivity_results:
        if r.rating == "HIGH":
            warnings.append(f"参数 {r.param_name} 高度敏感")

    in_sample_return = out_of_sample_result.get("inSampleReturn", 0.0)
    out_sample_return = out_of_sample_result.get("outSampleReturn", 0.0)

    if in_sample_return > 0 and out_sample_return >= 0:
        ratio = min(out_sample_return / in_sample_return, 1.0)
    elif in_sample_return < 0 and out_sample_return <= 0:
        if abs(in_sample_return) > 0:
            ratio = min(abs(in_sample_return) / abs(out_sample_return), 1.0) if abs(out_sample_return) > 0 else 1.0
        else:
            ratio = 1.0
    elif in_sample_return > 0 and out_sample_return < 0:
        ratio = 0.0
    elif in_sample_return == 0:
        ratio = 1.0 if abs(out_sample_return) < 0.001 else 0.5
    else:
        ratio = min(out_sample_return / abs(in_sample_return), 1.0) if abs(in_sample_return) > 0 else 1.0

    return_ratio_score = ratio * 100.0

    if out_of_sample_result.get("overfitWarning"):
        warnings.append("样本外收益显著低于样本内")

    trade_score = min(trade_count / 30.0, 1.0) * 100.0
    if trade_count < 10:
        warnings.append("交易次数过少，统计显著性不足")

    overall_score = int(sensitivity_score * 0.4 + return_ratio_score * 0.4 + trade_score * 0.2)

    if overall_score >= 80:
        overfit_risk = OverfitRisk.LOW.value
    elif overall_score >= 60:
        overfit_risk = OverfitRisk.MEDIUM.value
    elif overall_score >= 40:
        overfit_risk = OverfitRisk.HIGH.value
    else:
        overfit_risk = OverfitRisk.CRITICAL.value

    return overall_score, overfit_risk, warnings
