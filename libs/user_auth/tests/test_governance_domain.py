"""user_auth 用户治理领域测试。"""

from __future__ import annotations

import pytest


def test_user_profile_status_level_and_password_rules():
    from user_auth.domain import PasswordTooWeakError, User

    user = User.register(email="govern@example.com", password="StrongPass123!")
    user.verify_email()

    user.update_profile(display_name="Alice")
    assert user.display_name == "Alice"

    user.set_level(2)
    assert user.level == 2

    with pytest.raises(ValueError):
        user.set_level(3)

    user.disable()
    assert user.is_active is False
    user.enable()
    assert user.is_active is True

    with pytest.raises(ValueError):
        user.change_password(current_password="WrongPass123!", new_password="NewStrong123!")

    user.change_password(current_password="StrongPass123!", new_password="NewStrong123!")
    assert user.authenticate("StrongPass123!") is False
    assert user.authenticate("NewStrong123!") is True

    with pytest.raises(PasswordTooWeakError):
        user.change_password(current_password="NewStrong123!", new_password="weak")


def test_repository_list_and_session_revoke_by_user():
    from user_auth.domain import User
    from user_auth.repository import UserRepository
    from user_auth.session import Session, SessionStore

    repo = UserRepository()
    u1 = User.register(email="u1@example.com", password="StrongPass123!")
    u2 = User.register(email="u2@example.com", password="StrongPass123!")
    u3 = User.register(email="u3@example.com", password="StrongPass123!")
    u2.disable()

    repo.save(u1)
    repo.save(u2)
    repo.save(u3)

    page = repo.list_users(status="active", page=1, page_size=2)
    assert page["total"] == 2
    assert len(page["items"]) == 2

    updated = repo.update_user_level(user_id=u1.id, level=2)
    assert updated is not None
    assert updated.level == 2

    sessions = SessionStore()
    s1 = Session.create(user_id=u1.id)
    s2 = Session.create(user_id=u1.id)
    s3 = Session.create(user_id=u2.id)
    sessions.save(s1)
    sessions.save(s2)
    sessions.save(s3)

    revoked = sessions.revoke_by_user(user_id=u1.id)
    assert revoked == 2
    assert sessions.get_by_token(s1.token) is None
    assert sessions.get_by_token(s2.token) is None
    assert sessions.get_by_token(s3.token) is not None
