# Wave 0 用户系统后端聚合 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成 `update-user-system-backend-consolidation` 的首批落地：持久化会话、legacy token 兼容、统一鉴权入口与安全日志脱敏。

**Architecture:** 以 `libs/user_auth` 为聚合中心，先建立持久化仓储抽象与可替换实现，再统一 HTTP/WebSocket/CLI token 提取与鉴权语义。`platform_core` 负责脱敏策略，`user_preferences` 负责契约稳定与服务端 merge 语义。

**Tech Stack:** Python、FastAPI、Pydantic v2、pytest。

---

### Task 1: Legacy token 兼容提取器（先红后绿）

**Files:**
- Modify: `libs/user_auth/user_auth/token.py`
- Test: `libs/user_auth/tests/test_token_extraction.py`

**Step 1: Write the failing test**
- 新增以下失败用例：
  - `Authorization: Bearer token.signature` 返回 `token`
  - `Cookie: __Secure-better-auth.session_token=token.signature` 返回 `token`
  - `Cookie: better-auth.session_token=token.signature` 返回 `token`
  - 标准 `session_token` 仍可兼容

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/user_auth/tests/test_token_extraction.py`
- Expected: FAIL（legacy cookie 或签名移除行为缺失）

**Step 3: Write minimal implementation**
- 在 `extract_session_token` 中：
  - 增加 cookie 优先级：`session_token` > `__Secure-better-auth.session_token` > `better-auth.session_token`
  - 增加 `token.signature -> token` 归一化逻辑

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/user_auth/tests/test_token_extraction.py`
- Expected: PASS

---

### Task 2: 统一 get_current_user 失败日志脱敏

**Files:**
- Modify: `libs/user_auth/user_auth/deps.py`
- Modify: `libs/platform_core/platform_core/logging.py`
- Test: `libs/user_auth/tests/test_deps.py`
- Test: `libs/platform_core/tests/test_logging.py`

**Step 1: Write the failing test**
- `test_deps.py`：认证失败日志中不得出现原始 token/cookie/body 片段
- `test_logging.py`：Bearer/cookie/password 在复杂文本中均被掩码

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/user_auth/tests/test_deps.py libs/platform_core/tests/test_logging.py`
- Expected: FAIL

**Step 3: Write minimal implementation**
- `deps.py` 只记录掩码 token 与安全原因码
- 复用 `platform_core.logging.mask_sensitive`，避免重复规则

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/user_auth/tests/test_deps.py libs/platform_core/tests/test_logging.py`
- Expected: PASS

---

### Task 3: 持久化 SessionStore 抽象与 SQLite 实现

**Files:**
- Modify: `libs/user_auth/user_auth/session.py`
- Create: `libs/user_auth/user_auth/session_sqlite.py`
- Test: `libs/user_auth/tests/test_session.py`

**Step 1: Write the failing test**
- 增加仓储契约测试：
  - 重建 store 后仍可读会话（模拟重启）
  - 过期会话自动失效
  - revoke 后不可再用

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/user_auth/tests/test_session.py`
- Expected: FAIL

**Step 3: Write minimal implementation**
- 抽象 `SessionStore` 协议
- 新增 `SQLiteSessionStore`（`sqlite3` 原生实现，零额外依赖）

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/user_auth/tests/test_session.py`
- Expected: PASS

---

### Task 4: 持久化 UserRepository 抽象与 SQLite 实现

**Files:**
- Modify: `libs/user_auth/user_auth/repository.py`
- Create: `libs/user_auth/user_auth/repository_sqlite.py`
- Test: `libs/user_auth/tests/test_domain.py`
- Test: `libs/user_auth/tests/test_routes.py`

**Step 1: Write the failing test**
- 增加仓储契约测试：
  - `save/get_by_id/get_by_email/email_exists` 在重启后保持一致

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/user_auth/tests/test_domain.py libs/user_auth/tests/test_routes.py`
- Expected: FAIL

**Step 3: Write minimal implementation**
- 抽象 `UserRepository` 协议 + `InMemoryUserRepository`
- 新增 `SQLiteUserRepository`

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/user_auth/tests/test_domain.py libs/user_auth/tests/test_routes.py`
- Expected: PASS

---

### Task 5: 统一 HTTP/WebSocket/CLI 鉴权入口

**Files:**
- Modify: `libs/user_auth/user_auth/deps.py`
- Modify: `libs/monitoring_realtime/monitoring_realtime/app.py`
- Modify: `libs/user_auth/user_auth/cli.py`
- Test: `libs/monitoring_realtime/tests/test_ws_auth.py`
- Test: `libs/user_auth/tests/test_cli.py`

**Step 1: Write the failing test**
- WebSocket 与 HTTP 使用同一 token 提取顺序
- CLI 支持 `--token` 与 `Authorization` 等价语义

**Step 2: Run test to verify it fails**
- Run: `pytest -q libs/monitoring_realtime/tests/test_ws_auth.py libs/user_auth/tests/test_cli.py`
- Expected: FAIL

**Step 3: Write minimal implementation**
- 在 `user_auth` 暴露共享 token 提取与校验入口
- WebSocket/CLI 复用同一逻辑

**Step 4: Run test to verify it passes**
- Run: `pytest -q libs/monitoring_realtime/tests/test_ws_auth.py libs/user_auth/tests/test_cli.py`
- Expected: PASS

---

### Task 6: 全量回归与 OpenSpec 对齐

**Files:**
- Modify: `openspec/changes/update-user-system-backend-consolidation/tasks.md`（勾选已完成项）

**Step 1: Run targeted tests**
- Run: `pytest -q libs/user_auth/tests libs/monitoring_realtime/tests libs/platform_core/tests`
- Expected: PASS

**Step 2: Run full tests**
- Run: `pytest -q`
- Expected: PASS

**Step 3: Validate OpenSpec**
- Run: `openspec validate update-user-system-backend-consolidation --strict`
- Expected: PASS

