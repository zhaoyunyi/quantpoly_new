# User Auth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在后端实现自管用户系统（注册/登录/登出/会话查询），彻底淘汰 better-auth，并提供单一 `get_current_user`。

**Architecture:** `user_auth` 作为独立 bounded context。使用数据库持久化 opaque session token：浏览器用 httpOnly Cookie；CLI/服务端用 Bearer。同一 token 体系覆盖 HTTP 与 WebSocket。

**Tech Stack:** Python（FastAPI）、SQLModel/SQLAlchemy、Pydantic v2、pytest。

---

## Task 1: 定义领域模型与存储结构（Library-first）

**Files:**
- Create: `src/user_auth/models.py`
- Create: `src/user_auth/password.py`
- Create: `src/user_auth/session.py`
- Test: `tests/test_user_auth_password.py`

**Step 1: Write the failing test**

```python
from user_auth.password import hash_password, verify_password


def test_password_hash_and_verify_roundtrip():
    hashed = hash_password("S0m3-Str0ng-Pa55")
    assert verify_password("S0m3-Str0ng-Pa55", hashed) is True
    assert verify_password("wrong", hashed) is False
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 使用成熟算法（如 bcrypt/argon2）进行哈希

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add user_auth password hashing"`

---

## Task 2: 用户注册与弱口令拒绝

**Files:**
- Create: `src/user_auth/registration.py`
- Test: `tests/test_user_auth_registration.py`

**Step 1: Write the failing test**

覆盖：弱口令被拒绝、正常口令通过。

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 增加密码强度校验（最小长度 + 常见弱口令字典）

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: enforce password policy"`

---

## Task 3: 会话 token 签发、查询、撤销

**Files:**
- Create: `src/user_auth/tokens.py`
- Create: `src/user_auth/auth_service.py`
- Test: `tests/test_user_auth_sessions.py`

**Step 1: Write the failing test**

覆盖：登录签发 token、token 可验证、登出后 token 失效。

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- opaque token：随机高熵字符串 + 数据库持久化（hash 存储优先）

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add session token lifecycle"`

---

## Task 4: FastAPI 适配层与单一 get_current_user

**Files:**
- Create: `src/user_auth/fastapi/dependencies.py`
- Create: `src/user_auth/fastapi/routes.py`
- Test: `tests/test_user_auth_fastapi.py`

**Step 1: Write the failing test**

使用 TestClient 覆盖：
- 注册
- 登录返回 cookie/bearer
- `GET /users/me` 在有效 token 下返回用户
- 登出后 401

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 实现路由：`POST /auth/register`、`POST /auth/login`、`POST /auth/logout`、`GET /users/me`
- 依赖：从 Cookie（优先）或 Authorization Bearer 取 token

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add user-auth fastapi routes"`

---

## Task 5: CLI（满足 CLI Mandate）

**Files:**
- Create: `src/user_auth/cli.py`
- Test: `tests/test_user_auth_cli.py`

**Step 1: Write the failing test**

CLI 覆盖：create-user、login、verify-token、logout（stdout 为 JSON）。

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 通过环境变量或配置指定 API base url
- 输出结构化 JSON

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add user-auth cli"`

