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


def test_frontend_web_uses_single_npm_lockfile_baseline() -> None:
    pnpm_lock = Path("apps/frontend_web/pnpm-lock.yaml")
    assert not pnpm_lock.exists(), "前端当前命令与文档基线使用 npm，不应同时保留 pnpm-lock.yaml"


def test_frontend_web_package_lock_stays_in_sync_with_declared_dependencies() -> None:
    package_json_path = Path("apps/frontend_web/package.json")
    package_lock_path = Path("apps/frontend_web/package-lock.json")

    package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
    lock_data = json.loads(package_lock_path.read_text(encoding="utf-8"))

    dependencies = package_data.get("dependencies", {})
    root_package = lock_data.get("packages", {}).get("", {})
    root_dependencies = root_package.get("dependencies", {})
    locked_packages = lock_data.get("packages", {})

    assert root_dependencies.get("@tanstack/react-start") == dependencies.get(
        "@tanstack/react-start"
    )
    assert root_dependencies.get("@tanstack/react-router") == dependencies.get(
        "@tanstack/react-router"
    )
    assert root_dependencies.get("lucide-react") == dependencies.get("lucide-react")
    assert "node_modules/lucide-react" in locked_packages


def test_frontend_web_uses_vite_runtime_config_instead_of_vinxi_client_entry() -> None:
    vite_config = Path("apps/frontend_web/vite.config.ts")
    client_entry = Path("apps/frontend_web/app/client.tsx")

    assert vite_config.exists(), "缺少 vite.config.ts，当前前端运行时基线应为 TanStack Start + Vite"
    assert not client_entry.exists(), "当前前端已不应继续保留旧 Vinxi client entry"
