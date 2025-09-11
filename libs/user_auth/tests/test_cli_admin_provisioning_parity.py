"""user_auth 管理员创建用户 CLI 对齐测试。"""

from __future__ import annotations

import argparse
import json

from user_auth import cli
from user_auth.repository import UserRepository
from user_auth.session import SessionStore


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def _setup(monkeypatch):
    repo = UserRepository()
    sessions = SessionStore()
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_sessions", sessions)
    return repo


def test_cli_admin_create_user_success(capsys, monkeypatch):
    repo = _setup(monkeypatch)

    _run(cli._cmd_register, capsys=capsys, email="admin-cli-provision@example.com", password="StrongPass123!")
    _run(cli._cmd_verify_email, capsys=capsys, email="admin-cli-provision@example.com")
    admin = repo.get_by_email("admin-cli-provision@example.com")
    assert admin is not None
    admin.set_role("admin")
    admin.set_level(2)
    repo.save(admin)

    login = _run(
        cli._cmd_login,
        capsys=capsys,
        email="admin-cli-provision@example.com",
        password="StrongPass123!",
    )
    token = login["data"]["token"]

    created = _run(
        cli._cmd_admin_create_user,
        capsys=capsys,
        token=token,
        email="seeded-cli@example.com",
        password="SeededCliPass123!",
        display_name="Seeded CLI",
        role="user",
        level=1,
        is_active=False,
        email_verified=True,
    )

    assert created["success"] is True
    assert created["data"]["email"] == "seeded-cli@example.com"
    assert created["data"]["displayName"] == "Seeded CLI"
    assert created["data"]["isActive"] is False


def test_cli_non_admin_create_user_denied(capsys, monkeypatch):
    _setup(monkeypatch)

    _run(cli._cmd_register, capsys=capsys, email="normal-cli-provision@example.com", password="StrongPass123!")
    _run(cli._cmd_verify_email, capsys=capsys, email="normal-cli-provision@example.com")
    login = _run(
        cli._cmd_login,
        capsys=capsys,
        email="normal-cli-provision@example.com",
        password="StrongPass123!",
    )

    denied = _run(
        cli._cmd_admin_create_user,
        capsys=capsys,
        token=login["data"]["token"],
        email="denied-cli@example.com",
        password="DeniedCliPass123!",
        display_name="Denied CLI",
        role=None,
        level=None,
        is_active=True,
        email_verified=False,
    )

    assert denied["success"] is False
    assert denied["error"]["code"] == "ADMIN_REQUIRED"
