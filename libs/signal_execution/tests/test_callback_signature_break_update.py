"""signal_execution legacy 回调签名治理测试（BREAK UPDATE）。"""

from __future__ import annotations

import pytest

from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService


def _build_service(*, strategy_reader=None, market_history_reader=None) -> SignalExecutionService:
    return SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda _user_id, _strategy_id: True,
        account_owner_acl=lambda _user_id, _account_id: True,
        strategy_reader=strategy_reader,
        market_history_reader=market_history_reader,
    )


def test_strategy_reader_legacy_signature_is_rejected():
    with pytest.raises(TypeError):
        _build_service(strategy_reader=lambda strategy_id: {"id": strategy_id})


def test_market_history_reader_legacy_signature_is_rejected():
    with pytest.raises(TypeError):
        _build_service(market_history_reader=lambda symbol: [])

