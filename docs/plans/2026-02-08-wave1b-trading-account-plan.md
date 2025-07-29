# Wave 1-B 交易账户上下文迁移 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 落地 `add-trading-account-context-migration` 的最小可用能力：`trading_account` 库（账户/持仓/交易/流水）、CLI、API 与所有权校验。

**Architecture:** 先建纯领域模型 + in-memory 仓储 + service（所有对外方法显式 `user_id`），再提供 FastAPI router（403 越权）与 CLI（账户查询、持仓分析、交易统计）。

**Tech Stack:** Python、FastAPI、Pydantic v2、pytest。

---

### Task 1: 领域与仓储红测

**Files:**
- Create: `libs/trading_account/tests/test_domain.py`

**Step 1: Write failing tests**
- 账户创建并按用户隔离查询
- 持仓分析按用户隔离
- 交易统计按用户隔离
- 仓储/service 公共方法显式需要 `user_id`

**Step 2: Run red tests**
- Run: `pytest -q libs/trading_account/tests/test_domain.py`
- Expected: FAIL

**Step 3: Minimal implementation**
- `domain.py`：`TradingAccount/Position/TradeRecord/CashFlow`
- `repository.py`：`InMemoryTradingAccountRepository`
- `service.py`：`TradingAccountService`

**Step 4: Run tests to green**
- Run: `pytest -q libs/trading_account/tests/test_domain.py`

---

### Task 2: API 越权红测与实现

**Files:**
- Create: `libs/trading_account/tests/test_api.py`
- Create: `libs/trading_account/trading_account/api.py`

**Step 1: Write failing tests**
- `GET /trading/accounts` 仅返回当前用户
- `GET /trading/accounts/{id}/positions` 越权返回 403
- `GET /trading/accounts/{id}/trade-stats` 越权返回 403

**Step 2: Run red tests**
- Run: `pytest -q libs/trading_account/tests/test_api.py`

**Step 3: Minimal implementation**
- `create_router(store, get_current_user)`
- 用 `platform_core.response.success_response`
- 对外字段 camelCase

**Step 4: Run tests to green**
- Run: `pytest -q libs/trading_account/tests/test_api.py`

---

### Task 3: CLI 红测与实现

**Files:**
- Create: `libs/trading_account/tests/test_cli.py`
- Create: `libs/trading_account/trading_account/cli.py`

**Step 1: Write failing tests**
- `account-list --user-id` 输出该用户账户
- `position-summary --user-id --account-id` 输出分析
- `trade-stats --user-id --account-id` 输出统计

**Step 2: Run red tests**
- Run: `pytest -q libs/trading_account/tests/test_cli.py`

**Step 3: Minimal implementation**
- CLI 子命令：`account-list`、`position-summary`、`trade-stats`

**Step 4: Run tests to green**
- Run: `pytest -q libs/trading_account/tests/test_cli.py`

---

### Task 4: 验证与 OpenSpec 同步

**Files:**
- Modify: `conftest.py`
- Modify: `openspec/changes/add-trading-account-context-migration/tasks.md`

**Step 1: Add path injection**
- 在根 `conftest.py` 注入 `trading_account`

**Step 2: Run focused tests**
- Run: `pytest -q libs/trading_account/tests`

**Step 3: Full verification**
- Run: `pytest -q`
- Run: `openspec validate add-trading-account-context-migration --strict`

