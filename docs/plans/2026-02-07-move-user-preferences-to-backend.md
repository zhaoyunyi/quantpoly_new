# User Preferences Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将用户偏好设置（defaults/version/migration/validation/permissions）完全聚合到后端；前端仅做展示与提交。

**Architecture:** `user_preferences` 作为独立库：
- 默认值生成器 + 版本迁移器
- 深度合并策略
- 权限过滤（例如 Level 1 隐藏 advanced）
再提供 FastAPI 路由与 CLI。

**Tech Stack:** Python（FastAPI/Pydantic v2），pytest。

---

## Task 1: 默认值与版本迁移（library-first）

**Files:**
- Create: `src/user_preferences/defaults.py`
- Create: `src/user_preferences/migrations.py`
- Test: `tests/test_user_preferences_defaults.py`

**Step 1: Write the failing test**

```python
from user_preferences.defaults import build_default_preferences


def test_default_preferences_has_version_and_sync_enabled():
    prefs = build_default_preferences(user_level=1)
    assert prefs["version"]
    assert prefs["syncEnabled"] in [True, False]
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 实现 `build_default_preferences(user_level)`，返回包含 `version` 与基本字段

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add user preferences defaults"`

---

## Task 2: 深度合并 + 字段白名单校验

**Files:**
- Create: `src/user_preferences/merge.py`
- Create: `src/user_preferences/validation.py`
- Test: `tests/test_user_preferences_merge.py`

**Step 1: Write the failing test**

覆盖：patch 只更新嵌套字段，不丢失其余字段。

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- `deep_merge(base, patch)`
- `validate_patch(patch)`：拒绝未知顶层 key

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add preferences deep merge and validation"`

---

## Task 3: advanced 权限过滤

**Files:**
- Create: `src/user_preferences/permissions.py`
- Test: `tests/test_user_preferences_permissions.py`

**Step 1: Write the failing test**

覆盖：Level 1 读取时不包含 advanced；Level 1 patch advanced 返回 Forbidden。

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- `filter_preferences_for_user(prefs, user_level)`
- `ensure_can_patch(patch, user_level)`

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: enforce preferences permissions"`

---

## Task 4: FastAPI 路由（GET/PATCH/reset/export/import）

**Files:**
- Create: `src/user_preferences/fastapi/routes.py`
- Test: `tests/test_user_preferences_fastapi.py`

**Step 1: Write the failing test**

用 TestClient 覆盖：
- GET 返回默认值
- PATCH 深度合并
- reset 恢复默认
- export/import 往返一致

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 实现路由（路径按 spec：`/users/me/preferences` 等）

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add user preferences api"`

