from __future__ import annotations

import pytest

from strategy_health.engine import run_simulation
from strategy_health.repository import InMemoryHealthReportRepository
from strategy_health.service import HealthReportExecutionError, StrategyHealthService


def test_run_simulation_should_reject_unsupported_template():
    with pytest.raises(ValueError, match="unsupported template"):
        run_simulation(
            [100.0, 101.0, 102.0, 103.0],
            "macd",
            {"fast": 12, "slow": 26, "signal": 9},
        )


def test_execute_report_should_mark_failed_when_market_history_reader_raises():
    repository = InMemoryHealthReportRepository()

    def _market_history_reader(**_: object):
        raise RuntimeError("provider timeout")

    service = StrategyHealthService(
        repository=repository,
        market_history_reader=_market_history_reader,
    )
    report = service.create_report(
        user_id="u-1",
        config={
            "template": "moving_average",
            "parameters": {"shortWindow": 2, "longWindow": 3},
            "symbol": "AAPL",
            "startDate": "2026-01-01",
            "endDate": "2026-01-31",
        },
    )

    with pytest.raises(HealthReportExecutionError) as exc_info:
        service.execute_report(user_id="u-1", report_id=report.id)

    assert exc_info.value.code == "MARKET_DATA_UNAVAILABLE"

    failed = repository.get_by_id(report.id, user_id="u-1")
    assert failed is not None
    assert failed.status == "failed"
    assert failed.report == {"error": "provider timeout"}


def test_mean_reversion_simulation_should_use_exit_z_for_exit_timing():
    close_prices = [
        100.0,
        100.0,
        100.0,
        90.0,
        91.0,
        92.0,
        93.0,
        94.0,
        95.0,
    ]

    tighter_exit = run_simulation(
        close_prices,
        "mean_reversion",
        {"window": 3, "entryZ": 1.0, "exitZ": 0.2},
    )
    looser_exit = run_simulation(
        close_prices,
        "mean_reversion",
        {"window": 3, "entryZ": 1.0, "exitZ": 0.8},
    )

    tighter_sell = next(
        trade for trade in tighter_exit["trades"] if trade["side"] == "SELL"
    )
    looser_sell = next(
        trade for trade in looser_exit["trades"] if trade["side"] == "SELL"
    )

    assert tighter_sell["index"] != looser_sell["index"]
    assert tighter_sell["price"] != looser_sell["price"]
