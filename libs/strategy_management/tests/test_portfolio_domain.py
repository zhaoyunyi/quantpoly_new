"""strategy_management 组合聚合领域测试。"""

from __future__ import annotations

import pytest

from strategy_management.portfolio import (
    InvalidPortfolioConstraintsError,
    InvalidPortfolioTransitionError,
    InvalidPortfolioWeightsError,
    Portfolio,
)


def test_portfolio_should_create_with_default_constraints_and_version():
    portfolio = Portfolio.create(user_id="u-1", name="core")

    assert portfolio.user_id == "u-1"
    assert portfolio.name == "core"
    assert portfolio.status == "draft"
    assert portfolio.version == 1
    assert portfolio.constraints["maxTotalWeight"] == 1.0
    assert portfolio.constraints["maxSingleWeight"] == 1.0


def test_portfolio_should_add_members_and_update_version():
    portfolio = Portfolio.create(user_id="u-1", name="core")

    portfolio.add_member(strategy_id="s-1", weight=0.6)
    portfolio.add_member(strategy_id="s-2", weight=0.4)

    assert len(portfolio.members) == 2
    assert abs(portfolio.total_weight - 1.0) < 1e-9
    assert portfolio.version == 3


def test_portfolio_should_reject_invalid_weights():
    portfolio = Portfolio.create(
        user_id="u-1",
        name="risk",
        constraints={"maxTotalWeight": 1.0, "maxSingleWeight": 0.6},
    )

    with pytest.raises(InvalidPortfolioWeightsError):
        portfolio.add_member(strategy_id="s-1", weight=0.7)

    portfolio.add_member(strategy_id="s-1", weight=0.6)
    with pytest.raises(InvalidPortfolioWeightsError):
        portfolio.add_member(strategy_id="s-2", weight=0.5)


def test_portfolio_should_reject_invalid_constraints():
    with pytest.raises(InvalidPortfolioConstraintsError):
        Portfolio.create(
            user_id="u-1",
            name="invalid",
            constraints={"maxTotalWeight": 0, "maxSingleWeight": 0.5},
        )


def test_portfolio_should_support_status_transition_and_guard_invalid_transition():
    portfolio = Portfolio.create(user_id="u-1", name="lifecycle")

    portfolio.activate()
    assert portfolio.status == "active"

    portfolio.archive()
    assert portfolio.status == "archived"

    with pytest.raises(InvalidPortfolioTransitionError):
        portfolio.activate()
