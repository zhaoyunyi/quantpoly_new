"""signal_execution 策略驱动生成 API 合同测试。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str, strategies: dict[str, dict], histories: dict[str, list[float]]):
    from signal_execution.api import create_router
    from signal_execution.repository import InMemorySignalRepository
    from signal_execution.service import SignalExecutionService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id
            self.is_admin = False

    def _get_current_user():
        return _User(current_user_id)

    def _strategy_reader(*, user_id: str, strategy_id: str):
        strategy = strategies.get(strategy_id)
        if strategy is None:
            return None
        if strategy.get("userId") != user_id:
            return None
        return strategy

    def _market_history_reader(*, user_id: str, symbol: str, timeframe: str, limit: int | None = None):
        del user_id, timeframe, limit
        closes = histories.get(symbol.upper(), [])
        return [{"close": item} for item in closes]

    service = SignalExecutionService(
        repository=InMemorySignalRepository(),
        strategy_owner_acl=lambda user_id, strategy_id: strategy_id.startswith(user_id),
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
        strategy_reader=_strategy_reader,
        market_history_reader=_market_history_reader,
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user))
    return TestClient(app)


def test_api_generate_by_strategy_creates_signal_when_template_condition_matches():
    client = _build_app(
        current_user_id="u-1",
        strategies={
            "u-1-ma": {
                "id": "u-1-ma",
                "userId": "u-1",
                "status": "active",
                "template": "moving_average",
                "parameters": {"shortWindow": 2, "longWindow": 3},
            }
        },
        histories={"AAPL": [10.0, 11.0, 12.0, 13.0]},
    )

    resp = client.post(
        "/signals/generate-by-strategy",
        json={
            "strategyId": "u-1-ma",
            "accountId": "u-1-account-1",
            "symbols": ["AAPL"],
            "timeframe": "1Day",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert len(payload["data"]["signals"]) == 1
    signal = payload["data"]["signals"][0]
    assert signal["symbol"] == "AAPL"
    assert signal["side"] == "BUY"
    assert signal["metadata"]["reason"]
    assert signal["metadata"]["triggered_indicator"]
    assert payload["data"]["skipped"] == []


def test_api_generate_by_strategy_returns_skip_reason_for_inactive_and_insufficient_data():
    client = _build_app(
        current_user_id="u-1",
        strategies={
            "u-1-inactive": {
                "id": "u-1-inactive",
                "userId": "u-1",
                "status": "inactive",
                "template": "moving_average",
                "parameters": {"shortWindow": 2, "longWindow": 3},
            },
            "u-1-active": {
                "id": "u-1-active",
                "userId": "u-1",
                "status": "active",
                "template": "moving_average",
                "parameters": {"shortWindow": 3, "longWindow": 5},
            },
        },
        histories={"MSFT": [10.0, 11.0, 12.0]},
    )

    inactive = client.post(
        "/signals/generate-by-strategy",
        json={
            "strategyId": "u-1-inactive",
            "accountId": "u-1-account-1",
            "symbols": ["AAPL"],
            "timeframe": "1Day",
        },
    )
    assert inactive.status_code == 200
    inactive_payload = inactive.json()
    assert inactive_payload["success"] is True
    assert inactive_payload["data"]["signals"] == []
    assert inactive_payload["data"]["skipped"][0]["reason"] == "strategy_inactive"

    insufficient = client.post(
        "/signals/generate-by-strategy",
        json={
            "strategyId": "u-1-active",
            "accountId": "u-1-account-1",
            "symbols": ["MSFT"],
            "timeframe": "1Day",
        },
    )
    assert insufficient.status_code == 200
    insufficient_payload = insufficient.json()
    assert insufficient_payload["success"] is True
    assert insufficient_payload["data"]["signals"] == []
    assert insufficient_payload["data"]["skipped"][0]["reason"] == "insufficient_data"


def test_api_generate_by_strategy_rejects_acl_violation():
    client = _build_app(
        current_user_id="u-1",
        strategies={
            "u-2-ma": {
                "id": "u-2-ma",
                "userId": "u-2",
                "status": "active",
                "template": "moving_average",
                "parameters": {"shortWindow": 2, "longWindow": 3},
            }
        },
        histories={"AAPL": [1.0, 2.0, 3.0, 4.0]},
    )

    resp = client.post(
        "/signals/generate-by-strategy",
        json={
            "strategyId": "u-2-ma",
            "accountId": "u-1-account-1",
            "symbols": ["AAPL"],
            "timeframe": "1Day",
        },
    )

    assert resp.status_code == 403
    payload = resp.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "SIGNAL_ACCESS_DENIED"
