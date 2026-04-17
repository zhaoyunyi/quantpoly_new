"""production docker 资产测试。"""

from __future__ import annotations

from pathlib import Path


def test_frontend_prod_dockerfile_should_use_node_22_or_newer():
    dockerfile_path = Path("docker/frontend.prod.Dockerfile")
    content = dockerfile_path.read_text(encoding="utf-8")

    assert "FROM node:22-alpine" in content
    assert "npm ci" in content


def test_local_coolify_override_should_publish_ports_for_browser_level_verification():
    compose_path = Path("docker-compose.coolify.local.yml")
    content = compose_path.read_text(encoding="utf-8")

    assert '15432:5432' in content
    assert '18000:8000' in content
    assert '13000:3000' in content
    assert 'VITE_BACKEND_ORIGIN: http://localhost:18000' in content
    assert 'BACKEND_CORS_ALLOWED_ORIGINS: http://localhost:13000' in content
    assert 'USER_AUTH_COOKIE_SECURE: "false"' in content
