"""交易账户生命周期与风险评估闭环 API 测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import RiskControlService
    from trading_account.api import create_router
    from trading_account.repository import InMemoryTradingAccountRepository
    from trading_account.service import TradingAccountService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    trading_repo = InMemoryTradingAccountRepository()
    risk_service = RiskControlService(
        repository=InMemoryRiskRepository(),
        account_owner_acl=lambda user_id, account_id: trading_repo.get_account(
            account_id=account_id,
            user_id=user_id,
        )
        is not None,
    )

    trading_service = TradingAccountService(
        repository=trading_repo,
        risk_snapshot_reader=lambda user_id, account_id: risk_service.get_account_assessment_snapshot(
            user_id=user_id,
            account_id=account_id,
        ),
        risk_evaluator=lambda user_id, account_id: risk_service.evaluate_account_risk(
            user_id=user_id,
            account_id=account_id,
        ),
    )

    app = FastAPI()
    app.include_router(create_router(service=trading_service, get_current_user=_get_current_user))
    return app, trading_service


def test_account_lifecycle_create_get_update_and_filter_config():
    app, _service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    created = client.post(
        "/trading/accounts",
        json={"accountName": "paper-main", "initialCapital": 1000},
    )
    assert created.status_code == 200
    account_id = created.json()["data"]["id"]

    fetched = client.get(f"/trading/accounts/{account_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["accountName"] == "paper-main"

    updated = client.put(
        f"/trading/accounts/{account_id}",
        json={"accountName": "paper-main-v2", "isActive": False},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["accountName"] == "paper-main-v2"
    assert updated.json()["data"]["isActive"] is False

    filter_config = client.get("/trading/accounts/filter-config")
    assert filter_config.status_code == 200
    assert filter_config.json()["data"]["totalAccounts"] == 1


def test_account_summary_and_cash_flow_summary_cover_empty_and_non_empty_boundaries():
    app, service = _build_app(current_user_id="u-1")
    account = service.create_account(user_id="u-1", account_name="alpha")

    client = TestClient(app)

    summary_empty = client.get(f"/trading/accounts/{account.id}/summary")
    assert summary_empty.status_code == 200
    assert summary_empty.json()["data"]["positionCount"] == 0
    assert summary_empty.json()["data"]["stats"]["tradeCount"] == 0

    cash_empty = client.get(f"/trading/accounts/{account.id}/cash-flows/summary")
    assert cash_empty.status_code == 200
    assert cash_empty.json()["data"]["totalInflow"] == 0
    assert cash_empty.json()["data"]["totalOutflow"] == 0
    assert cash_empty.json()["data"]["netFlow"] == 0

    client.post(f"/trading/accounts/{account.id}/deposit", json={"amount": 500})
    client.post(f"/trading/accounts/{account.id}/withdraw", json={"amount": 120})

    cash_non_empty = client.get(f"/trading/accounts/{account.id}/cash-flows/summary")
    assert cash_non_empty.status_code == 200
    assert cash_non_empty.json()["data"]["totalInflow"] == 500
    assert cash_non_empty.json()["data"]["totalOutflow"] == 120
    assert cash_non_empty.json()["data"]["netFlow"] == 380


def test_risk_assessment_snapshot_and_evaluate_follow_acl():
    app, service = _build_app(current_user_id="u-1")
    mine = service.create_account(user_id="u-1", account_name="mine")
    other = service.create_account(user_id="u-2", account_name="other")

    client = TestClient(app)

    pending = client.get(f"/trading/accounts/{mine.id}/risk-assessment")
    assert pending.status_code == 202
    assert pending.json()["error"]["code"] == "RISK_ASSESSMENT_PENDING"

    evaluated = client.post(f"/trading/accounts/{mine.id}/risk-assessment/evaluate")
    assert evaluated.status_code == 200
    assert evaluated.json()["data"]["accountId"] == mine.id

    fetched = client.get(f"/trading/accounts/{mine.id}/risk-assessment")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["accountId"] == mine.id

    denied = client.get(f"/trading/accounts/{other.id}/risk-assessment")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "ACCOUNT_ACCESS_DENIED"
