"""本地 Coolify 验证工作流资产测试。"""

from __future__ import annotations

from pathlib import Path


def test_github_workflow_should_run_coolify_local_stack_verification():
    workflow_path = Path(".github/workflows/verify-coolify-local-stack.yml")
    content = workflow_path.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in content
    assert "pull_request:" in content
    assert "apps/frontend_web/package-lock.json" in content
    assert "docker/frontend.prod.Dockerfile" in content
    assert "docker-compose.coolify.local.yml" in content
    assert "scripts/verify_coolify_local_stack.py" in content
    assert "npm ci" in content
    assert "npx playwright install --with-deps chromium" in content
    assert "actions/setup-node" in content
    assert "actions/setup-python" in content

