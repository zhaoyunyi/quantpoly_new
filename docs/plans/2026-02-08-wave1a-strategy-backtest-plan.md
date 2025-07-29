# Wave 1-A 策略与回测上下文迁移 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 落地 `add-strategy-backtest-migration` 的库级基础能力：`strategy_management` 与 `backtest_runner`，满足 Library-First + CLI Mandate + Test-First。

**Architecture:** 先构建两个独立库（纯领域 + in-memory 仓储 + CLI），再通过显式接口解耦（策略删除前通过回测查询接口做占用检查）。本阶段先完成最小可用路径，不接入 FastAPI 路由。

**Tech Stack:** Python、Pydantic v2、pytest。

---

### Task 1: strategy_management 库骨架与红测

**Files:**
- Create: `libs/strategy_management/pyproject.toml`
- Create: `libs/strategy_management/strategy_management/__init__.py`
- Create: `libs/strategy_management/tests/test_domain.py`

**Step 1: Write failing tests**
- 策略必须绑定 `user_id`
- 越权读取返回 `None`
- 删除策略时若存在 `pending/running` 回测，抛出 `StrategyInUseError`

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/strategy_management/tests/test_domain.py`
- Expected: FAIL

**Step 3: Minimal implementation**
- 实现 `Strategy` 聚合、`InMemoryStrategyRepository`、`StrategyService`

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/strategy_management/tests/test_domain.py`
- Expected: PASS

---

### Task 2: strategy_management CLI

**Files:**
- Create: `libs/strategy_management/strategy_management/cli.py`
- Create: `libs/strategy_management/tests/test_cli.py`

**Step 1: Write failing tests**
- `create` 输出策略 JSON
- `list` 仅输出指定用户策略
- `delete` 在占用时输出错误码 `STRATEGY_IN_USE`

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/strategy_management/tests/test_cli.py`
- Expected: FAIL

**Step 3: Minimal implementation**
- CLI 子命令：`create/list/delete`

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/strategy_management/tests/test_cli.py`
- Expected: PASS

---

### Task 3: backtest_runner 库骨架与状态机红测

**Files:**
- Create: `libs/backtest_runner/pyproject.toml`
- Create: `libs/backtest_runner/backtest_runner/__init__.py`
- Create: `libs/backtest_runner/tests/test_domain.py`

**Step 1: Write failing tests**
- 状态机：`pending -> running -> completed|failed|cancelled`
- 越权读取任务返回 `None`
- 非法状态迁移抛 `InvalidBacktestTransitionError`

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/backtest_runner/tests/test_domain.py`
- Expected: FAIL

**Step 3: Minimal implementation**
- 实现 `BacktestTask` 聚合、`InMemoryBacktestRepository`、`BacktestService`

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/backtest_runner/tests/test_domain.py`
- Expected: PASS

---

### Task 4: backtest_runner CLI

**Files:**
- Create: `libs/backtest_runner/backtest_runner/cli.py`
- Create: `libs/backtest_runner/tests/test_cli.py`

**Step 1: Write failing tests**
- `create` 返回 `taskId/status`
- `status` 可查询任务
- `transition` 对非法迁移返回 `INVALID_TRANSITION`

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/backtest_runner/tests/test_cli.py`
- Expected: FAIL

**Step 3: Minimal implementation**
- CLI 子命令：`create/status/transition`

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/backtest_runner/tests/test_cli.py`
- Expected: PASS

---

### Task 5: 仓库集成与规范同步

**Files:**
- Modify: `conftest.py`
- Modify: `openspec/changes/add-strategy-backtest-migration/tasks.md`

**Step 1: Make tests discoverable**
- 在根 `conftest.py` 注入新库路径

**Step 2: Run focused tests**
- Run: `pytest -q libs/strategy_management/tests libs/backtest_runner/tests`
- Expected: PASS

**Step 3: Run full verification**
- Run: `pytest -q`
- Run: `openspec validate add-strategy-backtest-migration --strict`
- Expected: PASS

