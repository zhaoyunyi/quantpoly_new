"""trading_account 交易运营自动化任务 CLI 测试。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from job_orchestration.repository import InMemoryJobRepository
from job_orchestration.scheduler import InMemoryScheduler
from job_orchestration.service import JobOrchestrationService
from trading_account import cli
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import TradingAccountService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _setup(monkeypatch) -> tuple[TradingAccountService, InMemoryTradingAccountRepository, JobOrchestrationService]:
    repo = InMemoryTradingAccountRepository()
    service = TradingAccountService(repository=repo)
    job_service = JobOrchestrationService(repository=InMemoryJobRepository(), scheduler=InMemoryScheduler())

    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)
    monkeypatch.setattr(cli, "_job_service", job_service)
    return service, repo, job_service


def test_cli_pending_process_task_requires_admin(capsys, monkeypatch):
    _setup(monkeypatch)

    denied = _run(
        cli._cmd_ops_pending_process_task,
        capsys=capsys,
        user_id="u-1",
        is_admin=False,
        max_trades=10,
        idempotency_key="pp-cli-1",
    )

    assert denied["success"] is False
    assert denied["error"]["code"] == "ADMIN_REQUIRED"


def test_cli_pending_process_task_returns_job_payload_for_admin(capsys, monkeypatch):
    service, _repo, _job_service = _setup(monkeypatch)
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )

    payload = _run(
        cli._cmd_ops_pending_process_task,
        capsys=capsys,
        user_id="admin-1",
        is_admin=True,
        max_trades=100,
        idempotency_key="pp-cli-2",
    )

    assert payload["success"] is True
    assert payload["data"]["taskType"] == "trading_pending_process"
    assert payload["data"]["status"] == "succeeded"
    assert payload["data"]["result"]["processed"] == 1


def test_cli_daily_stats_calculate_then_read_back(capsys, monkeypatch):
    service, _repo, _job_service = _setup(monkeypatch)
    account = service.create_account(user_id="admin-1", account_name="primary")
    service.deposit(user_id="admin-1", account_id=account.id, amount=1000)
    order = service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )
    service.fill_order(user_id="admin-1", account_id=account.id, order_id=order.id)

    calc = _run(
        cli._cmd_ops_daily_stats_task,
        capsys=capsys,
        user_id="admin-1",
        is_admin=True,
        account_ids=[account.id],
        target_date="2026-02-10",
        idempotency_key="ds-cli-1",
    )

    assert calc["success"] is True
    assert calc["data"]["taskType"] == "trading_daily_stats_calculate"
    assert calc["data"]["result"]["date"] == "2026-02-10"

    read = _run(
        cli._cmd_stats_daily_get,
        capsys=capsys,
        user_id="admin-1",
        date="2026-02-10",
        account_id=account.id,
    )

    assert read["success"] is True
    assert read["data"]["date"] == "2026-02-10"
    assert read["data"]["items"][0]["accountId"] == account.id


def test_cli_account_cleanup_task_deletes_old_cancelled_orders(capsys, monkeypatch):
    service, repo, _job_service = _setup(monkeypatch)
    account = service.create_account(user_id="admin-1", account_name="primary")
    order = service.submit_order(
        user_id="admin-1",
        account_id=account.id,
        symbol="AAPL",
        side="BUY",
        quantity=1,
        price=100,
    )
    service.cancel_order(user_id="admin-1", account_id=account.id, order_id=order.id)
    stored = repo.get_order(account_id=account.id, user_id="admin-1", order_id=order.id)
    assert stored is not None
    stored.updated_at = datetime.now(timezone.utc) - timedelta(days=120)
    repo.save_order(stored)

    cleaned = _run(
        cli._cmd_ops_account_cleanup_task,
        capsys=capsys,
        user_id="admin-1",
        is_admin=True,
        account_ids=[account.id],
        days_threshold=90,
        idempotency_key="cleanup-cli-1",
    )

    assert cleaned["success"] is True
    assert cleaned["data"]["taskType"] == "trading_account_cleanup"
    assert repo.get_order(account_id=account.id, user_id="admin-1", order_id=order.id) is None

