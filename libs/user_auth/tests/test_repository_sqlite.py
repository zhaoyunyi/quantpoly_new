"""SQLite UserRepository 持久化测试。"""

from __future__ import annotations

from pathlib import Path

from user_auth.domain import User


def _sqlite_repo(db_path: Path):
    from user_auth.repository_sqlite import SQLiteUserRepository

    return SQLiteUserRepository(db_path=str(db_path))


class TestSQLiteUserRepository:
    def test_save_and_get_by_id_across_restarts(self, tmp_path: Path):
        db_path = tmp_path / "users.db"

        repo1 = _sqlite_repo(db_path)
        user = User.register(email="persist@example.com", password="StrongPass123!")
        repo1.save(user)

        repo2 = _sqlite_repo(db_path)
        found = repo2.get_by_id(user.id)

        assert found is not None
        assert found.id == user.id
        assert found.email == "persist@example.com"

    def test_get_by_email_and_email_exists(self, tmp_path: Path):
        db_path = tmp_path / "users.db"
        repo = _sqlite_repo(db_path)

        user = User.register(email="persist2@example.com", password="StrongPass123!")
        repo.save(user)

        found = repo.get_by_email("persist2@example.com")
        assert found is not None
        assert found.id == user.id
        assert repo.email_exists("persist2@example.com") is True
        assert repo.email_exists("missing@example.com") is False

