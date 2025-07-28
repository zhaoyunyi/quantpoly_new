"""user-auth CLI 测试。"""

from __future__ import annotations

import argparse
import json

import pytest

from user_auth import cli
from user_auth.repository import UserRepository
from user_auth.session import SessionStore


@pytest.fixture(autouse=True)
def _reset_cli_state(monkeypatch):
    monkeypatch.setattr(cli, "_repo", UserRepository())
    monkeypatch.setattr(cli, "_sessions", SessionStore())


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_register_login_verify_logout_flow(capsys):
    register = _run(
        cli._cmd_register,
        capsys=capsys,
        email="cli@example.com",
        password="StrongPass123!",
    )
    assert register["success"] is True

    verify_email = _run(
        cli._cmd_verify_email,
        capsys=capsys,
        email="cli@example.com",
    )
    assert verify_email["success"] is True

    login = _run(
        cli._cmd_login,
        capsys=capsys,
        email="cli@example.com",
        password="StrongPass123!",
    )
    assert login["success"] is True
    token = login["data"]["token"]

    verify = _run(cli._cmd_verify, capsys=capsys, token=token)
    assert verify["success"] is True
    assert verify["data"]["email"] == "cli@example.com"

    logout = _run(cli._cmd_logout, capsys=capsys, token=token)
    assert logout["success"] is True

    verify_after_logout = _run(cli._cmd_verify, capsys=capsys, token=token)
    assert verify_after_logout["success"] is False
    assert verify_after_logout["error"]["code"] == "INVALID_TOKEN"


def test_cli_verify_and_logout_accept_legacy_token_signature(capsys):
    _run(
        cli._cmd_register,
        capsys=capsys,
        email="legacy-cli@example.com",
        password="StrongPass123!",
    )
    _run(
        cli._cmd_verify_email,
        capsys=capsys,
        email="legacy-cli@example.com",
    )
    login = _run(
        cli._cmd_login,
        capsys=capsys,
        email="legacy-cli@example.com",
        password="StrongPass123!",
    )
    token = login["data"]["token"]
    legacy_token = f"{token}.signature"

    verify = _run(cli._cmd_verify, capsys=capsys, token=legacy_token)
    assert verify["success"] is True
    assert verify["data"]["email"] == "legacy-cli@example.com"

    logout = _run(cli._cmd_logout, capsys=capsys, token=legacy_token)
    assert logout["success"] is True

    verify_after_logout = _run(cli._cmd_verify, capsys=capsys, token=token)
    assert verify_after_logout["success"] is False


def test_cli_register_rejects_weak_password(capsys):
    result = _run(
        cli._cmd_register,
        capsys=capsys,
        email="weak@example.com",
        password="password",
    )
    assert result["success"] is False
    assert result["error"]["code"] == "WEAK_PASSWORD"


def test_cli_register_duplicate_email(capsys):
    _run(
        cli._cmd_register,
        capsys=capsys,
        email="dup@example.com",
        password="StrongPass123!",
    )
    result = _run(
        cli._cmd_register,
        capsys=capsys,
        email="dup@example.com",
        password="StrongPass123!",
    )
    assert result["success"] is False
    assert result["error"]["code"] == "DUPLICATE_EMAIL"


def test_cli_login_rejects_unverified_email(capsys):
    _run(
        cli._cmd_register,
        capsys=capsys,
        email="unverified-cli@example.com",
        password="StrongPass123!",
    )

    login = _run(
        cli._cmd_login,
        capsys=capsys,
        email="unverified-cli@example.com",
        password="StrongPass123!",
    )

    assert login["success"] is False
    assert login["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_cli_verify_invalid_token_has_unified_error_code(capsys):
    result = _run(cli._cmd_verify, capsys=capsys, token="invalid-token")
    assert result["success"] is False
    assert result["error"]["code"] == "INVALID_TOKEN"
