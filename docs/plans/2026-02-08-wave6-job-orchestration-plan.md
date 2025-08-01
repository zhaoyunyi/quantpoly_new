# Wave 6 任务编排上下文迁移 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 落地 `add-job-orchestration-context-migration`：统一任务模型、状态机、调度抽象、幂等约束与 Celery 兼容适配。

**Architecture:** 构建 `job_orchestration` 独立库（Job 聚合 + Repository/Scheduler/Dispatcher 接口 + in-memory 实现），以注入式适配器实现 Celery 兼容入口，首批接入 backtest/market-data 任务类型。

**Tech Stack:** Python、pytest。

---

### Task 1: 领域与状态机红测

**Files:**
- Create: `libs/job_orchestration/tests/test_domain.py`

**Step 1: Write failing tests**
- 状态机：queued/running/succeeded/failed/cancelled
- 显式 `user_id` 所有权校验
- 幂等键冲突检测

**Step 2: Run red tests**
- Run: `pytest -q libs/job_orchestration/tests/test_domain.py`

**Step 3: Minimal implementation**
- `domain.py` / `repository.py` / `service.py`
- `scheduler.py` / `dispatcher.py` in-memory 抽象

**Step 4: Run green tests**
- Run: `pytest -q libs/job_orchestration/tests/test_domain.py`

---

### Task 2: 适配与 CLI 红测

**Files:**
- Create: `libs/job_orchestration/tests/test_cli.py`
- Create: `libs/job_orchestration/tests/test_adapter.py`
- Create: `libs/job_orchestration/job_orchestration/cli.py`
- Create: `libs/job_orchestration/job_orchestration/celery_adapter.py`

**Step 1: Write failing tests**
- CLI 提交/取消/重试/查询 JSON 输出
- Celery 适配器契约（可替换 dispatcher）
- interval/cron 调度注册与启停

**Step 2: Run red tests**
- Run: `pytest -q libs/job_orchestration/tests/test_cli.py libs/job_orchestration/tests/test_adapter.py`

**Step 3: Minimal implementation**
- CLI 命令：submit/cancel/retry/status
- 适配器：`CeleryJobAdapter`（stub contract）

**Step 4: Run green tests**
- Run: `pytest -q libs/job_orchestration/tests`

---

### Task 3: 验证与 OpenSpec 同步

**Files:**
- Modify: `conftest.py`
- Modify: `openspec/changes/add-job-orchestration-context-migration/tasks.md`

**Step 1: Add lib path**
- 在根 `conftest.py` 注入 `job_orchestration`

**Step 2: Full verification**
- Run: `pytest -q`
- Run: `openspec validate add-job-orchestration-context-migration --strict`
- Run: `openspec validate --changes --strict`

