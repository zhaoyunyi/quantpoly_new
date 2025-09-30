"""策略研究优化引擎（grid/bayesian）测试。"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from strategy_management.research import build_optimization_result, build_research_results_listing


def test_build_optimization_result_grid_should_include_trials_and_budget_usage():
    result = build_optimization_result(
        strategy_id="u-1-s-1",
        template="mean_reversion",
        metrics={"averagePnl": 12.5, "volatility": 0.1},
        objective={"metric": "averagePnl", "direction": "maximize"},
        parameter_space={
            "window": {"min": 10, "max": 20, "step": 5},
            "entryZ": {"min": 1.0, "max": 1.4, "step": 0.2},
        },
        constraints={"maxDrawdown": 0.2},
        method="grid",
        budget={"maxTrials": 3, "maxDurationSeconds": 60},
    )

    assert result["method"] == "grid"
    assert result["version"] == "v3"
    assert result["budget"]["maxTrials"] == 3
    assert 1 <= len(result["trials"]) <= 3
    assert result["budgetUsage"]["usedTrials"] == len(result["trials"])
    assert result["bestCandidate"]["trialId"]
    assert result["convergence"]["earlyStopReason"] in {
        "max_trials_reached",
        "max_duration_reached",
        "parameter_space_exhausted",
        "early_stop_score_reached",
    }


def test_build_optimization_result_bayesian_should_honor_early_stop_budget():
    result = build_optimization_result(
        strategy_id="u-1-s-2",
        template="mean_reversion",
        metrics={"averagePnl": 8.0},
        objective={"metric": "averagePnl", "direction": "maximize"},
        parameter_space={
            "window": {"min": 10, "max": 40, "step": 5},
        },
        constraints={},
        method="bayesian",
        budget={"maxTrials": 10, "earlyStopScore": 0.0},
    )

    assert result["method"] == "bayesian"
    assert len(result["trials"]) == 1
    assert result["convergence"]["earlyStopReason"] == "early_stop_score_reached"


def test_build_research_results_listing_should_filter_by_method_and_version():
    now = datetime.now(timezone.utc)

    grid_job = SimpleNamespace(
        id="job-grid",
        task_type="strategy_optimization_suggest",
        payload={"strategyId": "s-1", "method": "grid"},
        status="succeeded",
        created_at=now,
        updated_at=now,
        finished_at=now,
        result={
            "optimizationResult": {
                "version": "v3",
                "method": "grid",
            }
        },
        error_code=None,
        error_message=None,
    )
    bayes_job = SimpleNamespace(
        id="job-bayes",
        task_type="strategy_optimization_suggest",
        payload={"strategyId": "s-1", "method": "bayesian"},
        status="succeeded",
        created_at=now,
        updated_at=now,
        finished_at=now,
        result={
            "optimizationResult": {
                "version": "v3",
                "method": "bayesian",
            }
        },
        error_code=None,
        error_message=None,
    )

    listing = build_research_results_listing(
        jobs=[grid_job, bayes_job],
        strategy_id="s-1",
        status="succeeded",
        method="bayesian",
        version="v3",
        limit=20,
    )

    assert listing["total"] == 1
    assert len(listing["items"]) == 1
    assert listing["items"][0]["taskId"] == "job-bayes"
    assert listing["items"][0]["method"] == "bayesian"
