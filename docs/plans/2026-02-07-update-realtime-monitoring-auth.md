# Realtime Monitoring Auth Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 `/ws/monitor` 的鉴权从旧 better-auth 迁移为新 `user-auth` session token（cookie 或 bearer）。

**Architecture:** WebSocket 握手复用 `user-auth` 的 token 解析逻辑；HTTP 与 WS 共享同一个 `CurrentUser`。

**Tech Stack:** Python（FastAPI）、pytest。

---

## Task 1: 提取可复用的 token 提取器

**Files:**
- Modify: `src/user_auth/fastapi/dependencies.py`
- Test: `tests/test_user_auth_token_extraction.py`

**Step 1: Write the failing test**

覆盖：
- 从 Cookie 取 token
- 从 Authorization Bearer 取 token
- 不支持 query token（默认）

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- `extract_session_token(headers, cookies)`

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "refactor: extract session token parser"`

---

## Task 2: WS endpoint 使用同一鉴权

**Files:**
- Modify: `src/monitoring_realtime/ws.py`（或实际 WS 模块路径）
- Test: `tests/test_monitor_ws_auth.py`

**Step 1: Write the failing test**

用 WebSocketTestSession 覆盖：
- 无 token：连接被拒绝（4401）
- 有 token：握手成功

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 握手时调用 `get_current_user_websocket`（复用 user-auth）

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "fix: align monitor ws auth with user-auth"`

