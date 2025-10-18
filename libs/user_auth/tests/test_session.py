"""Session 管理测试 — Red 阶段。

BDD Scenarios:
- 创建会话返回 opaque token
- 通过 token 查询会话获取 user_id
- 撤销会话后 token 失效
- 过期会话不可用
"""
from datetime import datetime, timezone
from pathlib import Path

from user_auth.session import Session, SessionStore


def _sqlite_store(db_path: Path):
    from user_auth.session_sqlite import SQLiteSessionStore

    return SQLiteSessionStore(db_path=str(db_path))


class TestSession:
    """Test会话模型。"""

    def test_create_session_has_token(self):
        session = Session.create(user_id="user-1")
        assert session.token is not None
        assert len(session.token) >= 32

    def test_create_session_has_expiry(self):
        session = Session.create(user_id="user-1")
        assert session.expires_at > datetime.now(timezone.utc)

    def test_session_is_not_expired(self):
        session = Session.create(user_id="user-1")
        assert session.is_expired is False

    def test_expired_session(self):
        session = Session.create(user_id="user-1", ttl_seconds=0)
        assert session.is_expired is True


class TestSessionStore:
    """Test会话存储。"""

    def test_save_and_get(self):
        store = SessionStore()
        session = Session.create(user_id="user-1")
        store.save(session)
        found = store.get_by_token(session.token)
        assert found is not None
        assert found.user_id == "user-1"

    def test_get_nonexistent_returns_none(self):
        store = SessionStore()
        assert store.get_by_token("nonexistent") is None

    def test_revoke_session(self):
        store = SessionStore()
        session = Session.create(user_id="user-1")
        store.save(session)
        store.revoke(session.token)
        assert store.get_by_token(session.token) is None

    def test_get_expired_returns_none(self):
        store = SessionStore()
        session = Session.create(user_id="user-1", ttl_seconds=0)
        store.save(session)
        assert store.get_by_token(session.token) is None


class TestSQLiteSessionStore:
    """Test持久化会话存储。"""

    def test_save_and_get_across_restarts(self, tmp_path: Path):
        db_path = tmp_path / "sessions.db"

        store1 = _sqlite_store(db_path)
        session = Session.create(user_id="persist-user")
        store1.save(session)

        store2 = _sqlite_store(db_path)
        found = store2.get_by_token(session.token)

        assert found is not None
        assert found.user_id == "persist-user"

    def test_revoke_persists_across_restarts(self, tmp_path: Path):
        db_path = tmp_path / "sessions.db"

        store1 = _sqlite_store(db_path)
        session = Session.create(user_id="persist-user")
        store1.save(session)

        store2 = _sqlite_store(db_path)
        store2.revoke(session.token)

        store3 = _sqlite_store(db_path)
        assert store3.get_by_token(session.token) is None

    def test_expired_session_returns_none(self, tmp_path: Path):
        db_path = tmp_path / "sessions.db"
        store = _sqlite_store(db_path)
        session = Session.create(user_id="persist-user", ttl_seconds=0)
        store.save(session)
        assert store.get_by_token(session.token) is None
