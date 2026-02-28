from __future__ import annotations

import json
from pathlib import Path


def test_frontend_web_uses_tanstack_start_scaffold() -> None:
    package_json_path = Path("apps/frontend_web/package.json")
    assert package_json_path.exists(), "缺少前端 package.json，尚未完成 TanStack Start 初始化"

    package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
    scripts = package_data.get("scripts", {})
    assert "dev" in scripts
    assert "build" in scripts

    dependencies = package_data.get("dependencies", {})
    dev_dependencies = package_data.get("devDependencies", {})
    all_dependencies = set(dependencies) | set(dev_dependencies)

    assert "@tanstack/react-router" in all_dependencies
    assert any(pkg.startswith("@tanstack/") for pkg in all_dependencies)


def test_frontend_web_pins_tanstack_start_versions() -> None:
    package_json_path = Path("apps/frontend_web/package.json")
    package_data = json.loads(package_json_path.read_text(encoding="utf-8"))

    dependencies = package_data.get("dependencies", {})
    assert dependencies.get("@tanstack/react-start") == "1.117.2"
    assert dependencies.get("@tanstack/react-router") == "1.117.1"
    assert dependencies.get("vinxi") == "0.5.3"

    overrides = package_data.get("overrides", {})
    assert overrides.get("@tanstack/router-generator") == "1.117.1"
    assert overrides.get("@tanstack/react-start-client") == "1.117.1"
    assert overrides.get("@tanstack/react-start-server") == "1.117.1"
    assert overrides.get("@tanstack/react-start-config") == "1.117.2"
    assert overrides.get("@tanstack/router-plugin") == "1.117.2"
