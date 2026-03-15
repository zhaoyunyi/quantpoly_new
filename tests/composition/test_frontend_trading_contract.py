"""前端 Trading 页面联调契约测试（后端 composition root）。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.backend_app.app import create_app


def _register_and_login(client: TestClient) -> str:
    email = "trading-contract@example.com"
    password = "StrongPass123!"

    register = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert register.status_code == 200

    verify = client.post("/auth/verify-email", json={"email": email})
    assert verify.status_code == 200

    login = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return login.json()["data"]["token"]


def test_trading_endpoints_support_frontend_flows_and_error_codes():
    app = create_app(storage_backend="memory")
    client = TestClient(app)
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/trading/accounts",
        headers=headers,
        json={"accountName": "主账户", "initialCapital": 1000},
    )
    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["success"] is True
    account_id = created_payload["data"]["id"]

    # overview（用于 /trading KPI 卡片）
    overview = client.get(f"/trading/accounts/{account_id}/overview", headers=headers)
    assert overview.status_code == 200
    overview_data = overview.json()["data"]
    assert set(
        [
            "positionCount",
            "totalMarketValue",
            "unrealizedPnl",
            "tradeCount",
            "turnover",
            "orderCount",
            "pendingOrderCount",
            "filledOrderCount",
            "cancelledOrderCount",
            "failedOrderCount",
            "cashBalance",
        ]
    ).issubset(set(overview_data.keys()))

    # buy 冲突：INSUFFICIENT_FUNDS（前端映射提示）
    buy_conflict = client.post(
        f"/trading/accounts/{account_id}/buy",
        headers=headers,
        json={"symbol": "AAPL", "quantity": 100, "price": 100},
    )
    assert buy_conflict.status_code == 409
    buy_conflict_payload = buy_conflict.json()
    assert buy_conflict_payload["success"] is False
    assert buy_conflict_payload["error"]["code"] == "INSUFFICIENT_FUNDS"

    # 充值后买入成功
    dep = client.post(
        f"/trading/accounts/{account_id}/deposit",
        headers=headers,
        json={"amount": 10_000},
    )
    assert dep.status_code == 200

    buy_ok = client.post(
        f"/trading/accounts/{account_id}/buy",
        headers=headers,
        json={"symbol": "AAPL", "quantity": 10, "price": 100},
    )
    assert buy_ok.status_code == 200
    buy_ok_payload = buy_ok.json()
    assert buy_ok_payload["success"] is True
    assert set(["order", "trade", "cashFlow", "position"]).issubset(set(buy_ok_payload["data"].keys()))

    # sell 冲突：INSUFFICIENT_POSITION（前端映射提示）
    sell_conflict = client.post(
        f"/trading/accounts/{account_id}/sell",
        headers=headers,
        json={"symbol": "AAPL", "quantity": 10_000, "price": 100},
    )
    assert sell_conflict.status_code == 409
    sell_conflict_payload = sell_conflict.json()
    assert sell_conflict_payload["success"] is False
    assert sell_conflict_payload["error"]["code"] == "INSUFFICIENT_POSITION"

    # cash-flows（用于 /trading/analytics）
    cf = client.get(f"/trading/accounts/{account_id}/cash-flows", headers=headers)
    assert cf.status_code == 200
    assert cf.json()["success"] is True

    cf_summary = client.get(f"/trading/accounts/{account_id}/cash-flows/summary", headers=headers)
    assert cf_summary.status_code == 200
    cf_summary_data = cf_summary.json()["data"]
    assert set(["flowCount", "totalInflow", "totalOutflow", "netFlow", "latestFlowAt"]).issubset(
        set(cf_summary_data.keys())
    )

    # filter-config（用于账户页过滤配置展示）
    fc = client.get("/trading/accounts/filter-config", headers=headers)
    assert fc.status_code == 200
    fc_data = fc.json()["data"]
    assert set(
        [
            "totalAccounts",
            "totalAssets",
            "profitLoss",
            "profitLossRate",
            "accountTypeCounts",
            "statusCounts",
            "riskLevelCounts",
            "hasPositionsCount",
            "hasFrozenBalanceCount",
        ]
    ).issubset(set(fc_data.keys()))

    # risk-assessment：初次应为 202 PENDING（前端展示 pending banner）
    pending = client.get(f"/trading/accounts/{account_id}/risk-assessment", headers=headers)
    assert pending.status_code == 202
    pending_payload = pending.json()
    assert pending_payload["success"] is False
    assert pending_payload["error"]["code"] == "RISK_ASSESSMENT_PENDING"

    # evaluate 后可获取快照
    evaluated = client.post(f"/trading/accounts/{account_id}/risk-assessment/evaluate", headers=headers)
    assert evaluated.status_code == 200
    assert evaluated.json()["success"] is True

    snapshot = client.get(f"/trading/accounts/{account_id}/risk-assessment", headers=headers)
    assert snapshot.status_code == 200
    assert snapshot.json()["success"] is True

