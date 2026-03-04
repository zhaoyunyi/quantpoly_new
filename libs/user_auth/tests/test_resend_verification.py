"""重发邮箱验证端点测试（TDD Red）。"""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from user_auth.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_resend_verification_returns_anti_enumeration_success(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "exists@example.com", "password": "StrongPass123!"},
    )

    existing = client.post(
        "/auth/verify-email/resend",
        json={"email": "exists@example.com"},
    )
    missing = client.post(
        "/auth/verify-email/resend",
        json={"email": "missing@example.com"},
    )

    assert existing.status_code == 200
    assert missing.status_code == 200
    assert existing.json()["success"] is True
    assert missing.json()["success"] is True
    assert existing.json()["message"] == missing.json()["message"]
    assert "data" not in existing.json()
    assert "data" not in missing.json()


def test_resend_verification_returns_success_for_verified_user(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "verified@example.com", "password": "StrongPass123!"},
    )
    client.post(
        "/auth/verify-email",
        json={"email": "verified@example.com"},
    )

    resp = client.post(
        "/auth/verify-email/resend",
        json={"email": "verified@example.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_resend_verification_emits_audit_log_without_raw_email(client: TestClient, caplog) -> None:
    email = "audit@example.com"
    client.post(
        "/auth/register",
        json={"email": email, "password": "StrongPass123!"},
    )

    with caplog.at_level(logging.INFO, logger="user_auth.email_verification"):
        resp = client.post(
            "/auth/verify-email/resend",
            json={"email": email},
        )

    assert resp.status_code == 200
    assert "email_verification_resend_event=" in caplog.text
    assert email not in caplog.text

