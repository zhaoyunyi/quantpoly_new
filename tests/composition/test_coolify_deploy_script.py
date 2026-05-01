"""Coolify 生产部署脚本测试。"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _load_script_module():
    script_path = Path("scripts/deploy_coolify_production.py")
    spec = importlib.util.spec_from_file_location("deploy_coolify_production", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_env_file_should_parse_local_secret_file_without_shell_source(tmp_path):
    module = _load_script_module()
    env_file = tmp_path / "ops_tokens.local.env"
    env_file.write_text(
        "\n".join(
            [
                "# 本地测试",
                "export COOLIFY_BASE_URL='https://coolify.quantpoly.com/'",
                'COOLIFY_API_TOKEN="token-with-special=chars"',
                "EXTRA_VALUE=raw-value",
            ]
        ),
        encoding="utf-8",
    )

    values = module.load_env_file(env_file)

    assert values == {
        "COOLIFY_BASE_URL": "https://coolify.quantpoly.com/",
        "COOLIFY_API_TOKEN": "token-with-special=chars",
        "EXTRA_VALUE": "raw-value",
    }


def test_build_config_should_use_quantpoly_production_defaults(tmp_path, monkeypatch):
    module = _load_script_module()
    env_file = tmp_path / "ops_tokens.local.env"
    env_file.write_text(
        "\n".join(
            [
                "COOLIFY_BASE_URL=https://coolify.quantpoly.com/",
                "COOLIFY_API_TOKEN=local-token",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("COOLIFY_BASE_URL", raising=False)
    monkeypatch.delenv("COOLIFY_API_TOKEN", raising=False)
    args = argparse.Namespace(
        env_file=env_file,
        base_url=None,
        api_token=None,
        application_uuid=module.DEFAULT_APPLICATION_UUID,
    )

    config = module.build_config(args)

    assert config.base_url == "https://coolify.quantpoly.com"
    assert config.api_token == "local-token"
    assert config.application_uuid == "wgsoo0gow8wkwow8kkg00kks"


def test_dry_run_output_should_not_need_network_or_expose_authorization_header():
    script = Path("scripts/deploy_coolify_production.py").read_text(encoding="utf-8")

    assert "--dry-run" in script
    assert "Authorization" in script
    assert '"api_token"' not in script
    assert 'method="GET"' in script
    assert 'method="HEAD"' not in script
