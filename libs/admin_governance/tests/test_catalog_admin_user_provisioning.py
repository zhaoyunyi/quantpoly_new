"""admin_governance 目录中管理员开通用户动作测试。"""

from __future__ import annotations


def test_catalog_contains_admin_create_user_action():
    from admin_governance.catalog import default_action_catalog

    catalog = default_action_catalog()

    assert "admin_create_user" in catalog
    policy = catalog["admin_create_user"]
    assert policy.min_role == "admin"
    assert policy.min_level == 2
