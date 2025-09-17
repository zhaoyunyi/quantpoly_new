"""signal_execution 策略执行查询读模型服务测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from signal_execution.domain import ExecutionRecord
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalAccessDeniedError, SignalExecutionService


def _build_service() -> tuple[SignalExecutionService, InMemorySignalRepository]:
    repo = InMemorySignalRepository()
    service = SignalExecutionService(
        repository=repo,
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    return service, repo


def test_service_should_query_execution_templates_by_strategy_type():
    service, _repo = _build_service()

    templates = service.list_execution_templates(strategy_type="moving_average")

    assert len(templates) == 1
    assert templates[0]["strategyType"] == "moving_average"
    assert "parameters" in templates[0]
    assert "shortWindow" in templates[0]["parameters"]


def test_service_should_return_strategy_statistics_and_trend_readmodel():
    service, repo = _build_service()
    now = datetime(2026, 2, 11, 10, 0, tzinfo=timezone.utc)

    repo.save_execution(
        ExecutionRecord(
            id="e-1",
            user_id="u-1",
            signal_id="s-1",
            strategy_id="u-1-s1",
            symbol="AAPL",
            status="executed",
            metrics={"pnl": 1.5, "latencyMs": 100},
            created_at=now - timedelta(days=1),
        )
    )
    repo.save_execution(
        ExecutionRecord(
            id="e-2",
            user_id="u-1",
            signal_id="s-2",
            strategy_id="u-1-s1",
            symbol="AAPL",
            status="cancelled",
            metrics={},
            created_at=now - timedelta(days=2),
        )
    )
    repo.save_execution(
        ExecutionRecord(
            id="e-3",
            user_id="u-1",
            signal_id="s-3",
            strategy_id="u-1-s2",
            symbol="MSFT",
            status="executed",
            metrics={"pnl": 99.0, "latencyMs": 10},
            created_at=now - timedelta(days=1),
        )
    )

    stats = service.strategy_execution_statistics(user_id="u-1", strategy_id="u-1-s1")
    trend = service.strategy_execution_trend(
        user_id="u-1",
        strategy_id="u-1-s1",
        days=3,
        now=now,
    )

    assert stats["strategyId"] == "u-1-s1"
    assert stats["totalExecutions"] == 2
    assert stats["executed"] == 1
    assert stats["cancelled"] == 1
    assert stats["averagePnl"] == 1.5

    assert len(trend) == 2
    assert sum(item["total"] for item in trend) == 2


def test_service_should_reject_foreign_strategy_query():
    service, _repo = _build_service()

    with pytest.raises(SignalAccessDeniedError):
        service.strategy_execution_statistics(user_id="u-1", strategy_id="u-2-s1")
