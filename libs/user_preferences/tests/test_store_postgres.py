"""Preferences Postgres 存储测试。

依赖：
- 本地运行 `docker compose up -d postgres`
- 安装可选依赖：sqlalchemy + psycopg（仅该集成测试需要）
"""

from __future__ import annotations

import os

import pytest


sqlalchemy = pytest.importorskip("sqlalchemy")
create_engine = sqlalchemy.create_engine


@pytest.mark.integration
def test_postgres_store_roundtrip_and_migration():
    from user_preferences.store import PostgresPreferencesStore
    from user_preferences.domain import Preferences, ThemePreferences, CURRENT_VERSION

    dsn = os.getenv(
        "POSTGRES_DSN",
        "postgresql+psycopg://quantpoly:quantpoly@localhost:54329/quantpoly_test",
    )

    engine = create_engine(dsn)
    store = PostgresPreferencesStore(engine=engine)
    store.ensure_schema()

    # 先写入旧版本
    old = Preferences(
        version=0,
        theme=ThemePreferences(primary_color="#000000", dark_mode=False),
        advanced={"betaFeatures": True},
    )
    store.set("u-1", old)

    # 读取应自动迁移并写回
    migrated = store.get_or_create("u-1")
    assert migrated.version == CURRENT_VERSION

    persisted = store.get("u-1")
    assert persisted is not None
    assert persisted.version == CURRENT_VERSION
