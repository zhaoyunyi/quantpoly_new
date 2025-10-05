"""平台鉴权判定测试。"""

from __future__ import annotations

from platform_core.authz import is_admin_actor, resolve_admin_decision


class _Actor:
    pass


def test_role_admin_has_highest_priority():
    actor = _Actor()
    actor.role = "admin"
    actor.is_admin = False
    actor.level = 1

    decision = resolve_admin_decision(actor)

    assert decision.is_admin is True
    assert decision.source == "role"
    assert is_admin_actor(actor) is True


def test_legacy_is_admin_true_is_rejected():
    actor = _Actor()
    actor.is_admin = True

    decision = resolve_admin_decision(actor)

    assert decision.is_admin is False
    assert decision.source == "none"


def test_level_based_admin_is_accepted_for_ops_context():
    actor = _Actor()
    actor.level = 10

    decision = resolve_admin_decision(actor)

    assert decision.is_admin is True
    assert decision.source == "level"


def test_non_admin_actor_is_rejected():
    actor = _Actor()
    actor.role = "user"
    actor.is_admin = False
    actor.level = 2

    decision = resolve_admin_decision(actor)

    assert decision.is_admin is False
    assert decision.source == "none"
    assert is_admin_actor(actor) is False
