"""user_auth 用户治理 CLI 测试。"""

from __future__ import annotations

import argparse
import json

from user_auth import cli
from user_auth.repository import UserRepository
from user_auth.session import SessionStore


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    return json.loads(capsys.readouterr().out)


def test_cli_update_me_and_change_password(capsys, monkeypatch):
    monkeypatch.setattr(cli, "_repo", UserRepository())
    monkeypatch.setattr(cli, "_sessions", SessionStore())

    _run(cli._cmd_register, capsys=capsys, email="cli-govern@example.com", password="StrongPass123!")
    _run(cli._cmd_verify_email, capsys=capsys, email="cli-govern@example.com")
    login = _run(cli._cmd_login, capsys=capsys, email="cli-govern@example.com", password="StrongPass123!")
    token = login["data"]["token"]

    updated = _run(cli._cmd_update_me, capsys=capsys, token=token, display_name="Alice", email=None)
    assert updated["success"] is True
    assert updated["data"]["displayName"] == "Alice"

    changed = _run(
        cli._cmd_change_password,
        capsys=capsys,
        token=token,
        current_password="StrongPass123!",
        new_password="NewStrongPass123!",
    )
    assert changed["success"] is True

    verify_old = _run(cli._cmd_verify, capsys=capsys, token=token)
    assert verify_old["success"] is False
    assert verify_old["error"]["code"] == "INVALID_TOKEN"


def test_cli_admin_user_management_requires_admin(capsys, monkeypatch):
    repo = UserRepository()
    sessions = SessionStore()
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_sessions", sessions)

    _run(cli._cmd_register, capsys=capsys, email="normal-cli@example.com", password="StrongPass123!")
    _run(cli._cmd_verify_email, capsys=capsys, email="normal-cli@example.com")
    normal_login = _run(cli._cmd_login, capsys=capsys, email="normal-cli@example.com", password="StrongPass123!")
    normal_token = normal_login["data"]["token"]

    deny = _run(cli._cmd_admin_list_users, capsys=capsys, token=normal_token, status=None, page=1, page_size=20)
    assert deny["success"] is False
    assert deny["error"]["code"] == "ADMIN_REQUIRED"

    _run(cli._cmd_register, capsys=capsys, email="admin-cli@example.com", password="StrongPass123!")
    _run(cli._cmd_verify_email, capsys=capsys, email="admin-cli@example.com")
    admin_user = repo.get_by_email("admin-cli@example.com")
    assert admin_user is not None
    admin_user.role = "admin"
    admin_user.level = 2
    repo.save(admin_user)
    admin_login = _run(cli._cmd_login, capsys=capsys, email="admin-cli@example.com", password="StrongPass123!")
    admin_token = admin_login["data"]["token"]

    listed = _run(cli._cmd_admin_list_users, capsys=capsys, token=admin_token, status=None, page=1, page_size=20)
    assert listed["success"] is True
    assert listed["data"]["total"] >= 2


def test_cli_self_and_admin_delete_user_flow(capsys, monkeypatch):
    repo = UserRepository()
    sessions = SessionStore()
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_sessions", sessions)

    _run(cli._cmd_register, capsys=capsys, email="self-cli-delete@example.com", password="StrongPass123!")
    _run(cli._cmd_verify_email, capsys=capsys, email="self-cli-delete@example.com")
    self_login = _run(
        cli._cmd_login,
        capsys=capsys,
        email="self-cli-delete@example.com",
        password="StrongPass123!",
    )
    self_token = self_login["data"]["token"]

    deleted_self = _run(cli._cmd_delete_me, capsys=capsys, token=self_token)
    assert deleted_self["success"] is True

    verify_after_self_delete = _run(cli._cmd_verify, capsys=capsys, token=self_token)
    assert verify_after_self_delete["success"] is False
    assert verify_after_self_delete["error"]["code"] == "INVALID_TOKEN"

    _run(cli._cmd_register, capsys=capsys, email="admin-cli-delete@example.com", password="StrongPass123!")
    _run(cli._cmd_verify_email, capsys=capsys, email="admin-cli-delete@example.com")
    admin_user = repo.get_by_email("admin-cli-delete@example.com")
    assert admin_user is not None
    admin_user.role = "admin"
    admin_user.level = 2
    repo.save(admin_user)
    admin_login = _run(
        cli._cmd_login,
        capsys=capsys,
        email="admin-cli-delete@example.com",
        password="StrongPass123!",
    )
    admin_token = admin_login["data"]["token"]

    _run(cli._cmd_register, capsys=capsys, email="target-cli-delete@example.com", password="StrongPass123!")
    _run(cli._cmd_verify_email, capsys=capsys, email="target-cli-delete@example.com")
    target = repo.get_by_email("target-cli-delete@example.com")
    assert target is not None

    got = _run(cli._cmd_admin_get_user, capsys=capsys, token=admin_token, user_id=target.id)
    assert got["success"] is True
    assert got["data"]["email"] == "target-cli-delete@example.com"

    deleted_target = _run(cli._cmd_admin_delete_user, capsys=capsys, token=admin_token, user_id=target.id)
    assert deleted_target["success"] is True

    got_after_delete = _run(cli._cmd_admin_get_user, capsys=capsys, token=admin_token, user_id=target.id)
    assert got_after_delete["success"] is False
    assert got_after_delete["error"]["code"] == "USER_NOT_FOUND"
