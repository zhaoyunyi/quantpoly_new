"""trading_account 风险回调签名治理测试（BREAK UPDATE）。"""

from __future__ import annotations

import pytest

from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import TradingAccountService


def test_risk_snapshot_reader_legacy_signature_is_rejected():
    with pytest.raises(TypeError):
        TradingAccountService(
            repository=InMemoryTradingAccountRepository(),
            risk_snapshot_reader=lambda account_id: {"accountId": account_id},
        )


def test_risk_evaluator_legacy_signature_is_rejected():
    with pytest.raises(TypeError):
        TradingAccountService(
            repository=InMemoryTradingAccountRepository(),
            risk_evaluator=lambda account_id: {"accountId": account_id},
        )

