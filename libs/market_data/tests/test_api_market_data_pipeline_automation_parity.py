"""market_data 数据管道任务补齐测试（WaveX）。

覆盖：
- 行情同步任务提交/状态/重试
- 技术指标计算任务接口与 JSON 契约
- 同步后边界一致性校验报告语义
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI


class _User:
    def __init__(self, user_id: str):
        self.id = user_id


def _build_app(*, provider, current_user_id: str = "u-1"):
    from fastapi.testclient import TestClient

    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService
    from market_data.api import create_router
    from market_data.service import MarketDataService

    def _get_current_user(request=None):
        return _User(current_user_id)

    service = MarketDataService(provider=provider)
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

    return TestClient(app), service, job_service


class _StableProvider:
    """返回稳定的历史数据，用于指标与同步测试。"""

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
        del start_date, end_date, timeframe, limit
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


class _FlakyProvider(_StableProvider):
    def __init__(self):
        self._fail_once = True

    def history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        limit: int | None,
    ):
        if symbol.upper() == "MSFT" and self._fail_once:
            self._fail_once = False
            from market_data.domain import UpstreamTimeoutError

            raise UpstreamTimeoutError()
        return super().history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            limit=limit,
        )


def test_sync_task_submit_returns_summary_and_status_query_contract():
    client, _service, job_service = _build_app(provider=_StableProvider())

    resp = client.post(
        "/market/sync-task",
        json={
            "symbols": ["aapl", "msft"],
            "startDate": "2026-02-01",
            "endDate": "2026-02-05",
            "idempotencyKey": "idem-sync-1",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "market_data_sync"
    assert payload["data"]["status"] == "succeeded"
    assert payload["data"]["result"]["summary"]["totalSymbols"] == 2
    assert payload["data"]["result"]["summary"]["successCount"] == 2
    assert payload["data"]["result"]["summary"]["failureCount"] == 0

    job = job_service.get_job(user_id="u-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.status == "succeeded"
    assert job.executor_name is not None
    assert job.dispatch_id is not None

    status = client.get(f"/market/sync-task/{payload['data']['taskId']}")
    assert status.status_code == 200
    status_payload = status.json()
    assert status_payload["data"]["status"] == "succeeded"


def test_sync_task_failure_sets_error_code_and_retry_succeeds():
    client, _service, _job_service = _build_app(provider=_FlakyProvider())

    first = client.post(
        "/market/sync-task",
        json={
            "symbols": ["AAPL", "MSFT"],
            "startDate": "2026-02-01",
            "endDate": "2026-02-05",
            "idempotencyKey": "idem-sync-flaky",
        },
    )

    assert first.status_code == 200
    payload = first.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "failed"
    assert payload["data"]["error"]["code"] == "MARKET_DATA_SYNC_FAILED"
    assert payload["data"]["result"]["summary"]["failureCount"] == 1

    retry = client.post(f"/market/sync-task/{payload['data']['taskId']}/retry")
    assert retry.status_code == 200
    retry_payload = retry.json()
    assert retry_payload["success"] is True
    assert retry_payload["data"]["status"] == "succeeded"
    assert retry_payload["data"]["result"]["summary"]["failureCount"] == 0


def test_boundary_check_reports_missing_extra_and_mismatch_contract():
    client, _service, _job_service = _build_app(provider=_StableProvider())

    synced = client.post(
        "/market/sync-task",
        json={
            "symbols": ["AAPL"],
            "startDate": "2026-02-01",
            "endDate": "2026-02-05",
            "idempotencyKey": "idem-sync-only-aapl",
        },
    )
    assert synced.status_code == 200
    assert synced.json()["data"]["status"] == "succeeded"

    report = client.post(
        "/market/boundary/check",
        json={"symbols": ["AAPL", "MSFT"]},
    )
    assert report.status_code == 200
    payload = report.json()
    assert payload["success"] is True
    assert payload["data"]["consistent"] is False
    assert payload["data"]["missingIds"] == ["MSFT"]
    assert payload["data"]["extraIds"] == []
    assert payload["data"]["mismatchCount"] == 0
    assert payload["data"]["beforeCount"] == 2
    assert payload["data"]["afterCount"] == 1


def test_indicators_calculate_task_returns_structured_json_contract():
    client, _service, job_service = _build_app(provider=_StableProvider())

    resp = client.post(
        "/market/indicators/calculate-task",
        json={
            "symbol": "AAPL",
            "startDate": "2026-02-01",
            "endDate": "2026-02-05",
            "timeframe": "1Day",
            "indicators": [{"name": "sma", "period": 3}],
            "idempotencyKey": "idem-indicators-1",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "market_indicators_calculate"
    assert payload["data"]["status"] == "succeeded"

    result = payload["data"]["result"]
    assert result["symbol"] == "AAPL"
    assert result["indicators"][0]["name"] == "sma"
    assert result["indicators"][0]["period"] == 3
    assert result["indicators"][0]["value"] == 13.0

    job = job_service.get_job(user_id="u-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.status == "succeeded"

    status = client.get(f"/market/indicators/calculate-task/{payload['data']['taskId']}")
    assert status.status_code == 200
    status_payload = status.json()
    assert status_payload["data"]["status"] == "succeeded"

