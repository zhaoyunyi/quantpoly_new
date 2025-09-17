"""signal_execution 策略执行查询读模型 CLI 测试。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from signal_execution import cli
from signal_execution.domain import ExecutionRecord
from signal_execution.repository import InMemorySignalRepository
from signal_execution.service import SignalExecutionService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _build_service() -> tuple[SignalExecutionService, InMemorySignalRepository]:
    repo = InMemorySignalRepository()
    service = SignalExecutionService(
        repository=repo,
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    return service, repo


def test_cli_should_support_templates_strategy_statistics_and_trend(capsys, monkeypatch):
    service, repo = _build_service()
    monkeypatch.setattr(cli, "_service", service)
    now = datetime(2026, 2, 11, 10, 0, tzinfo=timezone.utc)

    repo.save_execution(
        ExecutionRecord(
            id="e-1",
            user_id="u-1",
            signal_id="s-1",
            strategy_id="u-1-s1",
            symbol="AAPL",
            status="executed",
            metrics={"pnl": 5.0, "latencyMs": 60},
            created_at=now - timedelta(days=1),
        )
    )

    templates_payload = _run(
        cli._cmd_templates,
        capsys=capsys,
        strategy_type="moving_average",
    )
    stats_payload = _run(
        cli._cmd_strategy_statistics,
        capsys=capsys,
        user_id="u-1",
        strategy_id="u-1-s1",
    )
    trend_payload = _run(
        cli._cmd_strategy_trend,
        capsys=capsys,
        user_id="u-1",
        strategy_id="u-1-s1",
        days=3,
    )

    assert templates_payload["success"] is True
    assert len(templates_payload["data"]) == 1
    assert templates_payload["data"][0]["strategyType"] == "moving_average"

    assert stats_payload["success"] is True
    assert stats_payload["data"]["strategyId"] == "u-1-s1"
    assert stats_payload["data"]["totalExecutions"] == 1

    assert trend_payload["success"] is True
    assert len(trend_payload["data"]) == 1
    assert trend_payload["data"][0]["total"] == 1


def test_cli_strategy_statistics_should_enforce_acl(capsys, monkeypatch):
    service, _repo = _build_service()
    monkeypatch.setattr(cli, "_service", service)

    payload = _run(
        cli._cmd_strategy_statistics,
        capsys=capsys,
        user_id="u-1",
        strategy_id="u-2-s1",
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_ACCESS_DENIED"
