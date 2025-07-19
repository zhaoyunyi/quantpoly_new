# Platform Core Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在新仓库落地 `platform_core` 作为后端基础库：统一配置、响应信封、camelCase 序列化、日志脱敏。

**Architecture:** 先做纯库（无 FastAPI 依赖），再做 FastAPI 适配层；对外提供 CLI 便于验证与脚本化。

**Tech Stack:** Python（建议 3.11+），Pydantic v2，pytest。

---

## Task 1: 建立 Python 项目骨架

**Files:**
- Create: `pyproject.toml`
- Create: `src/platform_core/__init__.py`
- Create: `src/platform_core/cli.py`
- Create: `tests/test_platform_core_smoke.py`

**Step 1: Write the failing test**

在 `tests/test_platform_core_smoke.py` 添加最小 smoke test（先红）：

```python
def test_platform_core_importable():
    import platform_core  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`

Expected: FAIL（`ModuleNotFoundError: No module named 'platform_core'`）

**Step 3: Write minimal implementation**

- 增加 `src/platform_core/__init__.py` 并让项目可安装（pyproject 配置）

**Step 4: Run test to verify it passes**

Run: `pytest -q`

Expected: PASS

**Step 5: Commit**

Run: `git add pyproject.toml src tests && git cnd -m "feat: scaffold platform_core library"`

---

## Task 2: 统一响应信封（library-first）

**Files:**
- Create: `src/platform_core/response_envelope.py`
- Test: `tests/test_response_envelope.py`

**Step 1: Write the failing test**

```python
from platform_core.response_envelope import success_response, error_response


def test_success_response_shape():
    res = success_response(data={"a": 1}, message="ok")
    assert res["success"] is True
    assert res["message"] == "ok"
    assert res["data"] == {"a": 1}


def test_error_response_shape():
    res = error_response(code="BAD", message="no")
    assert res["success"] is False
    assert res["error"]["code"] == "BAD"
    assert res["error"]["message"] == "no"
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`

Expected: FAIL（函数未实现）

**Step 3: Write minimal implementation**

- 实现 `success_response/error_response/paged_response`（纯 dict 输出，后续再做 pydantic model）

**Step 4: Run test to verify it passes**

Run: `pytest -q`

Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add response envelope helpers"`

---

## Task 3: camelCase 序列化工具

**Files:**
- Create: `src/platform_core/case.py`
- Test: `tests/test_case.py`

**Step 1: Write the failing test**

```python
from platform_core.case import to_camel


def test_to_camel_converts_snake_case():
    assert to_camel("created_at") == "createdAt"
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 实现 `to_camel`，并提供对 dict/list 的递归转换（仅用于输出层）

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add camelCase serializer"`

---

## Task 4: 日志脱敏工具

**Files:**
- Create: `src/platform_core/redaction.py`
- Test: `tests/test_redaction.py`

**Step 1: Write the failing test**

```python
from platform_core.redaction import redact_token


def test_redact_token_masks_middle():
    assert redact_token("abcdefghijklmnopqrstuvwxyz") == "abcdefgh…(redacted)"
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- `redact_token(token, prefix=8)`：只保留前缀，后续全部掩码

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add sensitive data redaction"`

---

## Task 5: CLI（满足 CLI Mandate）

**Files:**
- Modify: `src/platform_core/cli.py`
- Test: `tests/test_platform_core_cli.py`

**Step 1: Write the failing test**

用 `subprocess` 调用 CLI（stdin 输入 JSON），期待 stdout 输出 JSON。

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- 提供最小子命令：
  - `platform-core redact`：输入 token，输出脱敏 token
  - `platform-core camel`：输入 dict（JSON），输出 camelCase dict（JSON）

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

Run: `git add src tests && git cnd -m "feat: add platform-core cli"`

