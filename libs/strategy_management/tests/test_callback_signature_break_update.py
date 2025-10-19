"""strategy_management legacy 回调签名治理测试（BREAK UPDATE）。

目标：禁止通过 try/except TypeError 兼容省略 user_id 的旧签名。
"""

from __future__ import annotations

import pytest

from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import StrategyService


def test_count_active_backtests_legacy_signature_is_rejected():
    repo = InMemoryStrategyRepository()
    with pytest.raises(TypeError):
        StrategyService(
            repository=repo,
            count_active_backtests=lambda strategy_id: 0,
        )
