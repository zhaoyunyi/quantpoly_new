# Backend User Ownership Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在所有业务 bounded context 中统一资源所有权（ownership）规则：任何资源读写必须绑定 `userId` 并按 `current_user.id` 校验/过滤。

**Architecture:** 以 library-first 的方式提供 `ownership` 校验工具与 FastAPI 依赖/辅助函数，业务路由只调用统一入口。

**Tech Stack:** Python（FastAPI）、pytest。

---

## Task 1: ownership 工具函数（library-first）

**Files:**
- Create: `src/platform_core/ownership.py`
- Test: `tests/test_ownership.py`

**Step 1: Write the failing test**

```python
from platform_core.ownership import ensure_owner


def test_ensure_owner_raises_when_not_owner():
    try:
        ensure_owner(resource_user_id="u2", current_user_id="u1")
        assert False, "should raise"
    except PermissionError:
        assert True
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- `ensure_owner(resource_user_id, current_user_id)`：不匹配则 raise `PermissionError`

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add ownership helpers"`

---

## Task 2: FastAPI 层统一 403 映射

**Files:**
- Create: `src/platform_core/fastapi/errors.py`
- Test: `tests/test_fastapi_ownership_error.py`

**Step 1: Write the failing test**

构建一个最小 FastAPI app，调用 `ensure_owner` 触发 `PermissionError`，期待返回 403。

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 增加 exception handler：`PermissionError` -> HTTP 403

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: map ownership violations to 403"`

---

## Task 3: 在一个业务模块上做示范性落地

**Files:**
- Modify: `src/<some_module>/...`（选择第一个迁移的业务模块，例如 strategies 或 backtests）
- Test: `tests/test_<module>_ownership.py`

**Step 1: Write the failing test**

覆盖：
- A 用户不能读取 B 用户资源（403）
- 列表接口只返回本人资源

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- repo/service 方法显式接收 `user_id`
- 路由层传入 `current_user.id`

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "refactor: enforce user ownership in <module>"`

