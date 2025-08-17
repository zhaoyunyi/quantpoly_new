"""交易账户生命周期与风险评估闭环 CLI 测试。"""

from __future__ import annotations

import argparse
import json

from risk_control.repository import InMemoryRiskRepository
from risk_control.service import RiskControlService
from trading_account import cli
from trading_account.repository import InMemoryTradingAccountRepository
from trading_account.service import TradingAccountService


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _setup(monkeypatch) -> TradingAccountService:
    repo = InMemoryTradingAccountRepository()
    risk_service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: repo.get_account(account_id=account_id, user_id=user_id)
        is not None,
    )
    service = TradingAccountService(
        repository=repo,
        risk_snapshot_reader=lambda user_id, account_id: risk_service.get_account_assessment_snapshot(
            user_id=user_id,
            account_id=account_id,
        ),
        risk_evaluator=lambda user_id, account_id: risk_service.evaluate_account_risk(
            user_id=user_id,
            account_id=account_id,
        ),
    )

    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)
    return service


def test_cli_account_lifecycle_and_filter_config(capsys, monkeypatch):
    _setup(monkeypatch)

    created = _run(
        cli._cmd_account_create,
        capsys=capsys,
        user_id="u-1",
        account_name="paper-main",
        initial_capital=1000.0,
    )
    assert created["success"] is True
    account_id = created["data"]["id"]

    fetched = _run(
        cli._cmd_account_get,
        capsys=capsys,
        user_id="u-1",
        account_id=account_id,
    )
    assert fetched["success"] is True

    updated = _run(
        cli._cmd_account_update,
        capsys=capsys,
        user_id="u-1",
        account_id=account_id,
        account_name="paper-main-v2",
        is_active=False,
    )
    assert updated["success"] is True
    assert updated["data"]["accountName"] == "paper-main-v2"
    assert updated["data"]["isActive"] is False

    filter_config = _run(cli._cmd_account_filter_config, capsys=capsys, user_id="u-1")
    assert filter_config["success"] is True
    assert filter_config["data"]["totalAccounts"] == 1


def test_cli_summary_cash_flow_summary_and_risk_assessment(capsys, monkeypatch):
    service = _setup(monkeypatch)
    account = service.create_account(user_id="u-1", account_name="alpha")

    summary = _run(
        cli._cmd_account_summary,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )
    assert summary["success"] is True
    assert summary["data"]["positionCount"] == 0

    cash_summary = _run(
        cli._cmd_cash_flow_summary,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )
    assert cash_summary["success"] is True
    assert cash_summary["data"]["totalInflow"] == 0

    pending = _run(
        cli._cmd_risk_assessment,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )
    assert pending["success"] is False
    assert pending["error"]["code"] == "RISK_ASSESSMENT_PENDING"

    evaluated = _run(
        cli._cmd_risk_assessment_evaluate,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )
    assert evaluated["success"] is True
    assert evaluated["data"]["accountId"] == account.id

    fetched = _run(
        cli._cmd_risk_assessment,
        capsys=capsys,
        user_id="u-1",
        account_id=account.id,
    )
    assert fetched["success"] is True
    assert fetched["data"]["accountId"] == account.id
