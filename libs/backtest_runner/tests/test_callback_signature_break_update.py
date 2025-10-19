"""backtest_runner legacy 回调签名治理测试（BREAK UPDATE）。

目标：禁止通过 try/except TypeError 兼容省略 user_id 的旧签名。
"""

from __future__ import annotations

import pytest

from backtest_runner.repository import InMemoryBacktestRepository
from backtest_runner.service import BacktestService


def test_strategy_reader_legacy_signature_is_rejected():
    with pytest.raises(TypeError):
        BacktestService(
            repository=InMemoryBacktestRepository(),
            strategy_reader=lambda strategy_id: {"id": strategy_id},
        )


def test_market_history_reader_legacy_signature_is_rejected():
    with pytest.raises(TypeError):
        BacktestService(
            repository=InMemoryBacktestRepository(),
            market_history_reader=lambda symbol: [],
        )

