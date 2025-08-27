"""risk_control 风控自动化与报告任务补齐测试（Wave3）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(*, current_user_id: str):
    from job_orchestration.repository import InMemoryJobRepository
    from job_orchestration.scheduler import InMemoryScheduler
    from job_orchestration.service import JobOrchestrationService
    from risk_control.api import create_router
    from risk_control.repository import InMemoryRiskRepository
    from risk_control.service import RiskControlService

    class _User:
        def __init__(self, user_id: str):
            self.id = user_id

    def _get_current_user():
        return _User(current_user_id)

    repo = InMemoryRiskRepository()
    service = RiskControlService(
        repository=repo,
        account_owner_acl=lambda user_id, account_id: account_id.startswith(user_id),
    )
    job_service = JobOrchestrationService(
        repository=InMemoryJobRepository(),
        scheduler=InMemoryScheduler(),
    )

    app = FastAPI()
    app.include_router(create_router(service=service, get_current_user=_get_current_user, job_service=job_service))
    return app, service, repo, job_service


def test_batch_risk_check_task_endpoint_returns_job_and_summary():
    app, service, _repo, job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max_drawdown",
        threshold=0.8,
    )

    resp = client.post(
        "/risk/batch/check-task",
        json={"accountIds": ["u-1-account"], "idempotencyKey": "idem-batch-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "risk_batch_check"
    assert payload["data"]["result"]["total"] == 1

    job = job_service.get_job(user_id="u-1", job_id=payload["data"]["taskId"])
    assert job is not None
    assert job.status == "succeeded"


def test_risk_report_generate_task_endpoint_returns_structured_summary():
    app, service, _repo, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max_drawdown",
        severity="high",
        message="drawdown high",
    )
    service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="margin_call",
        severity="critical",
        message="margin call",
    )

    resp = client.post(
        "/risk/reports/generate-task",
        json={"reportType": "daily", "idempotencyKey": "idem-report-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "risk_report_generate"
    assert payload["data"]["result"]["summary"]["totalAlerts"] == 2
    assert payload["data"]["result"]["summary"]["criticalAlerts"] == 1


def test_alert_notify_task_updates_alert_audit_fields_and_returns_result():
    app, service, _repo, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    alert = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max_drawdown",
        severity="high",
        message="drawdown high",
    )

    resp = client.post(
        "/risk/alerts/notify-task",
        json={"idempotencyKey": "idem-notify-1"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "risk_alert_notify"
    assert payload["data"]["result"]["total"] == 1
    assert payload["data"]["result"]["success"] == 1
    assert payload["data"]["result"]["auditId"]

    listed = client.get("/risk/alerts")
    assert listed.status_code == 200
    items = listed.json()["data"]
    item = next(row for row in items if row["id"] == alert.id)
    assert item["status"] in {"acknowledged", "resolved"}
    assert item["notificationStatus"] == "sent"
    assert item["notifiedBy"] == "u-1"
    assert item["notifiedAt"]


def test_continuous_monitor_task_and_status_query():
    app, service, _repo, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max_drawdown",
        threshold=0.9,
    )

    resp = client.post(
        "/risk/monitor/continuous-task",
        json={"accountIds": ["u-1-account"], "idempotencyKey": "idem-monitor-1"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "risk_continuous_monitor"
    assert payload["data"]["result"]["monitoredAccounts"] == 1

    status = client.get(f"/risk/monitor/continuous-task/{payload['data']['taskId']}")
    assert status.status_code == 200
    status_payload = status.json()
    assert status_payload["data"]["status"] == "succeeded"


def test_snapshot_batch_and_account_task_and_read_contract():
    app, service, _repo, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    service.create_rule(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max_drawdown",
        threshold=0.4,
    )

    batch = client.post(
        "/risk/snapshots/generate-all-task",
        json={"accountIds": ["u-1-account"], "idempotencyKey": "idem-snap-batch"},
    )
    assert batch.status_code == 200
    batch_payload = batch.json()
    assert batch_payload["data"]["taskType"] == "risk_snapshot_generate_all"
    assert batch_payload["data"]["result"]["totalAccounts"] == 1
    assert batch_payload["data"]["result"]["successCount"] == 1

    single = client.post(
        "/risk/accounts/u-1-account/snapshot-task",
        json={"idempotencyKey": "idem-snap-single"},
    )
    assert single.status_code == 200
    single_payload = single.json()
    assert single_payload["data"]["taskType"] == "risk_snapshot_generate_account"
    assert single_payload["data"]["result"]["accountId"] == "u-1-account"

    snapshot = client.get("/risk/accounts/u-1-account/snapshot")
    assert snapshot.status_code == 200
    snapshot_payload = snapshot.json()["data"]
    assert snapshot_payload["assessmentId"] == single_payload["data"]["result"]["assessmentId"]


def test_alert_cleanup_task_deletes_resolved_alerts_older_than_retention():
    app, service, repo, _job_service = _build_app(current_user_id="u-1")
    client = TestClient(app)

    old = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max_drawdown",
        severity="info",
        message="old",
    )
    old.resolve(actor_id="u-1")
    old.resolved_at = datetime.now(timezone.utc) - timedelta(days=10)
    repo.save_alert(old)

    recent = service.create_alert(
        user_id="u-1",
        account_id="u-1-account",
        rule_name="max_drawdown",
        severity="info",
        message="recent",
    )
    recent.resolve(actor_id="u-1")
    repo.save_alert(recent)

    resp = client.post(
        "/risk/alerts/cleanup-task",
        json={"retentionDays": 3, "idempotencyKey": "idem-alert-clean"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["taskType"] == "risk_alert_cleanup"
    assert payload["data"]["result"]["deleted"] == 1
    assert payload["data"]["result"]["auditId"]

    remaining = client.get("/risk/alerts")
    assert remaining.status_code == 200
    remaining_ids = {item["id"] for item in remaining.json()["data"]}
    assert recent.id in remaining_ids
    assert old.id not in remaining_ids

