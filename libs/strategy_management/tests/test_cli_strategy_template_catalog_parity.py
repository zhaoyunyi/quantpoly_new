"""strategy_management 模板目录能力对齐 CLI 测试。"""

from __future__ import annotations

import argparse
import json

import pytest

from strategy_management import cli
from strategy_management.repository import InMemoryStrategyRepository
from strategy_management.service import StrategyService


@pytest.fixture(autouse=True)
def _reset_cli_state(monkeypatch):
    repo = InMemoryStrategyRepository()
    service = StrategyService(repository=repo, count_active_backtests=lambda _user_id, _strategy_id: 0)
    monkeypatch.setattr(cli, "_repo", repo)
    monkeypatch.setattr(cli, "_service", service)


def _run(handler, *, capsys, **kwargs):
    handler(argparse.Namespace(**kwargs))
    out = capsys.readouterr().out
    return json.loads(out)


def test_cli_template_list_covers_core_templates(capsys):
    payload = _run(cli._cmd_template_list, capsys=capsys, user_id="u-1")

    assert payload["success"] is True
    template_ids = {item["templateId"] for item in payload["data"]}
    assert {
        "moving_average",
        "bollinger_bands",
        "rsi",
        "macd",
        "mean_reversion",
        "momentum",
    }.issubset(template_ids)


def test_cli_create_from_template_uses_catalog_schema(capsys):
    payload = _run(
        cli._cmd_create_from_template,
        capsys=capsys,
        user_id="u-1",
        name="rsi-strategy",
        template_id="rsi",
        parameters='{"period":14,"oversold":30.0,"overbought":70.0}',
    )

    assert payload["success"] is True
    assert payload["data"]["template"] == "rsi"


def test_cli_create_from_template_invalid_parameter_returns_stable_error(capsys):
    payload = _run(
        cli._cmd_create_from_template,
        capsys=capsys,
        user_id="u-1",
        name="macd-invalid",
        template_id="macd",
        parameters='{"fast":30,"slow":10,"signal":9}',
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "STRATEGY_INVALID_PARAMETERS"
    assert "fast" in payload["error"]["message"].lower()
