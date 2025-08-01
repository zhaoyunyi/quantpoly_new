# Wave 5 数据拓扑边界迁移 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 落地 `add-data-topology-boundary-migration`：明确模型归属边界、跨库访问策略、迁移模板与一致性校验能力。

**Architecture:** 构建独立库 `data_topology_boundary`，包含边界目录（catalog）、跨库策略（ACL/AC Layer 规则）、迁移脚本模板与 dry-run、对账与补偿策略；对外统一 CLI。

**Tech Stack:** Python、pytest。

---

### Task 1: 领域与边界红测

**Files:**
- Create: `libs/data_topology_boundary/tests/test_domain.py`

**Step 1: Write failing tests**
- 模型归属校验（user/business DB）
- 非法跨库依赖检测
- 迁移 dry-run 与回滚演练

**Step 2: Run red tests**
- Run: `pytest -q libs/data_topology_boundary/tests/test_domain.py`

**Step 3: Minimal implementation**
- `catalog.py`、`policy.py`、`migration.py`、`reconciliation.py`

**Step 4: Run green tests**
- Run: `pytest -q libs/data_topology_boundary/tests/test_domain.py`

---

### Task 2: CLI 红测与实现

**Files:**
- Create: `libs/data_topology_boundary/tests/test_cli.py`
- Create: `libs/data_topology_boundary/data_topology_boundary/cli.py`

**Step 1: Write failing tests**
- `check-model` 校验模型归属
- `scan-cross-db` 检测非法边
- `migration-dry-run` 输出迁移/回滚计划

**Step 2: Run red tests**
- Run: `pytest -q libs/data_topology_boundary/tests/test_cli.py`

**Step 3: Minimal implementation**
- CLI 命令：`check-model` / `scan-cross-db` / `migration-dry-run` / `reconcile`

**Step 4: Run green tests**
- Run: `pytest -q libs/data_topology_boundary/tests/test_cli.py`

---

### Task 3: 验证与 OpenSpec 同步

**Files:**
- Modify: `conftest.py`
- Modify: `openspec/changes/add-data-topology-boundary-migration/tasks.md`

**Step 1: Add lib path**
- 在根 `conftest.py` 注入 `data_topology_boundary`

**Step 2: Focused tests**
- Run: `pytest -q libs/data_topology_boundary/tests`

**Step 3: Full verification**
- Run: `pytest -q`
- Run: `openspec validate add-data-topology-boundary-migration --strict`
- Run: `openspec validate --changes --strict`

