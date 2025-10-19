"""策略模板与生命周期测试。"""

from __future__ import annotations

import pytest

from strategy_management.domain import InvalidStrategyTransitionError
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import InvalidStrategyParametersError, StrategyService


def _service() -> StrategyService:
    return StrategyService(repository=InMemoryStrategyRepository(), count_active_backtests=lambda user_id, strategy_id: 0)


def test_list_templates_contains_required_defaults():
    service = _service()

    templates = service.list_templates()

    assert len(templates) >= 1
    mean_rev = next(item for item in templates if item["templateId"] == "mean_reversion")
    assert "requiredParameters" in mean_rev


def test_create_from_template_and_activate_lifecycle():
    service = _service()

    created = service.create_strategy_from_template(
        user_id="u-1",
        name="mr-1",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )
    assert created.status == "draft"

    activated = service.activate_strategy(user_id="u-1", strategy_id=created.id)
    assert activated.status == "active"

    deactivated = service.deactivate_strategy(user_id="u-1", strategy_id=created.id)
    assert deactivated.status == "inactive"


def test_invalid_template_parameters_are_rejected():
    service = _service()

    with pytest.raises(InvalidStrategyParametersError):
        service.create_strategy_from_template(
            user_id="u-1",
            name="mr-invalid",
            template_id="mean_reversion",
            parameters={"window": 1, "entryZ": 1.5, "exitZ": 0.5},
        )


def test_archived_strategy_cannot_activate_again():
    service = _service()
    created = service.create_strategy_from_template(
        user_id="u-1",
        name="mr-archived",
        template_id="mean_reversion",
        parameters={"window": 20, "entryZ": 1.5, "exitZ": 0.5},
    )
    service.archive_strategy(user_id="u-1", strategy_id=created.id)

    with pytest.raises(InvalidStrategyTransitionError):
        service.activate_strategy(user_id="u-1", strategy_id=created.id)
