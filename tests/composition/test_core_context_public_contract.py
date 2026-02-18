"""核心上下文公开契约测试。"""

from __future__ import annotations


def test_core_context_public_contract_should_not_export_sqlite_adapters():
    import backtest_runner
    import job_orchestration
    import strategy_management
    import trading_account

    assert all("SQLite" not in name for name in strategy_management.__all__)
    assert all("SQLite" not in name for name in backtest_runner.__all__)
    assert all("SQLite" not in name for name in job_orchestration.__all__)
    assert all("SQLite" not in name for name in trading_account.__all__)

    assert "PostgresStrategyRepository" in strategy_management.__all__
    assert "PostgresBacktestRepository" in backtest_runner.__all__
    assert "PostgresBacktestResultStore" in backtest_runner.__all__
    assert "PostgresJobRepository" in job_orchestration.__all__
    assert "PostgresTradingAccountRepository" in trading_account.__all__


def test_risk_signal_public_contract_should_not_export_sqlite_adapters():
    import risk_control
    import signal_execution

    assert all("SQLite" not in name for name in risk_control.__all__)
    assert all("SQLite" not in name for name in signal_execution.__all__)

    assert "PostgresRiskRepository" in risk_control.__all__
    assert "PostgresSignalRepository" in signal_execution.__all__
