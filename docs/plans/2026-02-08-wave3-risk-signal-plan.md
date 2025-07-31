# Wave 3 风控与信号执行迁移 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 落地 `add-risk-signal-context-migration` 的最小可用能力：`risk_control` 与 `signal_execution` 两个独立库，完成所有权隔离、维护接口限制与 ACL 解耦。

**Architecture:** 先分别构建库级领域模型/仓储/服务（显式 `user_id`），再提供 API + CLI，最后通过注入式 ACL（`account_owner_acl`、`strategy_owner_acl`）与 `trading_account`、`strategy_management` 解耦。

**Tech Stack:** Python、FastAPI、Pydantic v2、pytest。

---

### Task 1: risk_control 红测与实现

**Files:**
- Create: `libs/risk_control/tests/test_domain.py`
- Create: `libs/risk_control/tests/test_api.py`
- Create: `libs/risk_control/tests/test_cli.py`

**Step 1: Write failing tests**
- 批量确认包含他人告警时返回 403 语义且不更新任何记录
- 统计接口指定他人账户时拒绝访问
- 仓储与服务公共方法显式接收 `user_id`

**Step 2: Run red tests**
- Run: `pytest -q libs/risk_control/tests`

**Step 3: Minimal implementation**
- `domain.py`/`repository.py`/`service.py`
- `api.py`/`cli.py`
- ACL 注入：`account_owner_acl(user_id, account_id)`

**Step 4: Run green tests**
- Run: `pytest -q libs/risk_control/tests`

---

### Task 2: signal_execution 红测与实现

**Files:**
- Create: `libs/signal_execution/tests/test_domain.py`
- Create: `libs/signal_execution/tests/test_api.py`
- Create: `libs/signal_execution/tests/test_cli.py`

**Step 1: Write failing tests**
- 越权 `signal_id` 执行/取消被拒绝且状态不变
- 普通用户调用全局清理接口返回 403
- 执行趋势统计仅按当前用户范围聚合

**Step 2: Run red tests**
- Run: `pytest -q libs/signal_execution/tests`

**Step 3: Minimal implementation**
- `domain.py`/`repository.py`/`service.py`
- `api.py`/`cli.py`
- ACL 注入：`strategy_owner_acl`、`account_owner_acl`

**Step 4: Run green tests**
- Run: `pytest -q libs/signal_execution/tests`

---

### Task 3: 集成验证与 OpenSpec 同步

**Files:**
- Modify: `conftest.py`
- Modify: `openspec/changes/add-risk-signal-context-migration/tasks.md`

**Step 1: Add lib paths**
- 在根 `conftest.py` 注入 `risk_control`、`signal_execution`

**Step 2: Focused tests**
- Run: `pytest -q libs/risk_control/tests libs/signal_execution/tests`

**Step 3: Full verification**
- Run: `pytest -q`
- Run: `openspec validate add-risk-signal-context-migration --strict`
- Run: `openspec validate --changes --strict`

