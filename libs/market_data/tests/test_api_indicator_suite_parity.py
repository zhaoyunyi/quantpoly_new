"""market_data 指标套件能力对齐测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI


class _User:
    def __init__(self, user_id: str):
        self.id = user_id


class _StableProvider:
    def search(self, *, keyword: str, limit: int):
        del keyword, limit
        return []

    def quote(self, *, symbol: str):
        del symbol
        raise RuntimeError("not used")

    def history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ):
        del symbol, start_date, end_date, timeframe, limit

        from market_data.domain import MarketCandle

        close_prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        base = datetime(2026, 2, 1, tzinfo=timezone.utc)
        return [
            MarketCandle(
                timestamp=base + timedelta(days=i),
                open_price=price,
                high_price=price,
                low_price=price,
                close_price=price,
                volume=1000.0,
            )
            for i, price in enumerate(close_prices)
        ]

    def list_assets(self, *, limit: int):
        del limit
        return []

    def batch_quote(self, *, symbols: list[str]):
        del symbols
        return {}

    def health(self):
        return {"provider": "stable", "healthy": True, "status": "ok", "message": ""}


def _build_client(*, current_user_id: str = "u-1"):
    from fastapi.testclient import TestClient

    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService
    from market_data.api import create_router
    from market_data.service import MarketDataService

    def _get_current_user(request=None):
        return _User(current_user_id)

    service = MarketDataService(provider=_StableProvider())
    job_service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    app = FastAPI()
    app.include_router(
        create_router(
            service=service,
            get_current_user=_get_current_user,
            job_service=job_service,
        )
    )
    return TestClient(app)


def _as_indicator_map(payload: dict) -> dict[str, dict]:
    return {item["name"]: item for item in payload["data"]["result"]["indicators"]}


def test_api_indicators_calculate_supports_ema_rsi_macd_bollinger():
    client = _build_client()

    resp = client.post(
        "/market/indicators/calculate-task",
        json={
            "symbol": "AAPL",
            "startDate": "2026-02-01",
            "endDate": "2026-02-05",
            "timeframe": "1Day",
            "indicators": [
                {"name": "ema", "period": 3},
                {"name": "rsi", "period": 3},
                {"name": "macd", "fast": 3, "slow": 5, "signal": 2},
                {"name": "bollinger", "period": 3, "stdDev": 2},
            ],
            "idempotencyKey": "idem-indicator-suite-ok",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    indicators = _as_indicator_map(payload)

    for name in ["ema", "rsi", "macd", "bollinger"]:
        assert indicators[name]["status"] == "ok"
        assert "value" in indicators[name]
        assert "metadata" in indicators[name]

    assert indicators["ema"]["metadata"]["period"] == 3
    assert indicators["rsi"]["metadata"]["period"] == 3
    assert indicators["macd"]["metadata"]["fast"] == 3
    assert indicators["macd"]["metadata"]["slow"] == 5
    assert indicators["macd"]["metadata"]["signal"] == 2
    assert indicators["bollinger"]["metadata"]["period"] == 3
    assert indicators["bollinger"]["metadata"]["stdDev"] == 2.0


def test_api_indicators_calculate_returns_unsupported_and_insufficient_data_status():
    client = _build_client()

    resp = client.post(
        "/market/indicators/calculate-task",
        json={
            "symbol": "AAPL",
            "startDate": "2026-02-01",
            "endDate": "2026-02-05",
            "timeframe": "1Day",
            "indicators": [
                {"name": "foo", "period": 3},
                {"name": "rsi", "period": 14},
            ],
            "idempotencyKey": "idem-indicator-suite-error-semantics",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True

    indicators = _as_indicator_map(payload)

    unsupported = indicators["foo"]
    assert unsupported["status"] == "unsupported"
    assert "value" not in unsupported
    assert unsupported["metadata"]["period"] == 3

    insufficient = indicators["rsi"]
    assert insufficient["status"] == "insufficient_data"
    assert "value" not in insufficient
    assert insufficient["metadata"]["period"] == 14
    assert insufficient["metadata"]["requiredDataPoints"] == 15
