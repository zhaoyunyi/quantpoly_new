"""backend docker 开发编排资产测试。"""

from __future__ import annotations

from pathlib import Path


def test_compose_should_enable_hot_reload_and_workspace_mount():
    compose_path = Path("docker-compose.backend-dev.yml")
    content = compose_path.read_text(encoding="utf-8")

    assert "backend_dev" in content
    assert "./:/workspace" in content
    assert "--reload" in content
    assert "BACKEND_CORS_ALLOWED_ORIGINS" in content
    assert "http://localhost:3300" in content


def test_dockerfile_should_install_backend_runtime_dependencies():
    dockerfile_path = Path("docker/backend.dev.Dockerfile")
    content = dockerfile_path.read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in content
    assert "uvicorn[standard]" in content
    assert "sqlalchemy" in content
    assert "psycopg[binary]" in content

