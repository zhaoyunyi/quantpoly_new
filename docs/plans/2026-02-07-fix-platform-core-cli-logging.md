# Platform Core CLI/Logging Bugfix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 `platform_core` 在参数化日志与 CLI 配置加载上的缺陷（脱敏不应异常/泄漏；CLI 默认应读取 `.env`；`mask` 支持空字符串参数），在不改变现有功能语义的前提下提升鲁棒性与可测试性。

**Architecture:** 保持现有 API/CLI 行为不变，仅在实现层修复：
- `SensitiveFilter` 以最终格式化后的 message 进行脱敏，并清理 `record.args` 避免二次格式化。
- CLI 仅在用户显式提供 `--env-file` 时才覆盖 `_env_file`，否则走 `Settings.model_config` 的默认 `.env` 加载。
- `mask` 子命令把空字符串视为有效输入（不走 stdin）。

**Tech Stack:** Python 3.11+，pytest，pydantic-settings。

---

## Task 1: 修复 SensitiveFilter 参数化日志的异常与泄漏风险

**Files:**
- Modify: `libs/platform_core/tests/test_logging.py`
- Modify: `libs/platform_core/platform_core/logging.py`

**Step 1: Write the failing test**

在 `libs/platform_core/tests/test_logging.py` 增加用例：当使用参数化日志（`msg="token=%s"` + `args=(token,)`）时，过滤器不应造成格式化异常，且最终 message 必须完成脱敏。

**Step 2: Run test to verify it fails**

Run: `pytest -q libs/platform_core/tests/test_logging.py -k parameterized`

Expected: FAIL（当前实现会把 `record.msg` 改成无占位符的字符串，但 `record.args` 仍存在，导致后续 `getMessage()` 触发 `TypeError`，或保留敏感值）。

**Step 3: Write minimal implementation**

在 `libs/platform_core/platform_core/logging.py`：
- 仅当 `record.msg` 为 `str` 时处理（保持现有边界）。
- 先调用 `record.getMessage()` 得到最终字符串，再执行 `mask_sensitive()`。
- 将 `record.msg` 替换为脱敏后的最终字符串，并将 `record.args` 清空（`()`），避免后续 formatter 再次格式化。
- 兜底：若 `getMessage()` 发生格式化异常，也应清空 `record.args` 并尽量对 `record.msg` 做脱敏，保证 filter 不抛异常。

**Step 4: Run test to verify it passes**

Run: `pytest -q libs/platform_core/tests/test_logging.py -k parameterized`

Expected: PASS

---

## Task 2: 修复 CLI 默认忽略 .env 导致 config/validate 不可靠

**Files:**
- Modify: `libs/platform_core/tests/test_cli.py`
- Modify: `libs/platform_core/platform_core/cli.py`

**Step 1: Write the failing tests**

在 `libs/platform_core/tests/test_cli.py` 增加 2 个用例（直接调用 `_cmd_config/_cmd_validate`，避免子进程与 cwd 差异）：
- 当工作目录存在 `.env` 且未传 `--env-file` 时，`config` 应读取 `.env` 中的 `ENVIRONMENT/SECRET_KEY`。
- 当 `.env` 中 `ENVIRONMENT=production` 且 `SECRET_KEY` 为空时，`validate` 必须失败并返回 `CONFIG_VALIDATION_ERROR`。

**Step 2: Run tests to verify they fail**

Run: `pytest -q libs/platform_core/tests/test_cli.py -k dotenv_default`

Expected: FAIL（当前实现显式传 `_env_file=None` 导致禁用 `.env`）。

**Step 3: Write minimal implementation**

在 `libs/platform_core/platform_core/cli.py`：
- 仅当 `args.env_file is not None` 时才调用 `Settings(_env_file=args.env_file)`。
- 否则使用 `Settings()`，让 pydantic-settings 按 `Settings.model_config` 默认读取 `.env`。

**Step 4: Run tests to verify they pass**

Run: `pytest -q libs/platform_core/tests/test_cli.py -k dotenv_default`

Expected: PASS

---

## Task 3: 修复 mask 子命令对空字符串参数的误判

**Files:**
- Modify: `libs/platform_core/tests/test_cli.py`
- Modify: `libs/platform_core/platform_core/cli.py`

**Step 1: Write the failing test**

在 `libs/platform_core/tests/test_cli.py` 增加用例：当 `args.text == ""`（显式传入空字符串）时，`_cmd_mask` 必须以空字符串为输入，而不是读取 `stdin`。

**Step 2: Run test to verify it fails**

Run: `pytest -q libs/platform_core/tests/test_cli.py -k mask_empty_string`

Expected: FAIL（当前 `if args.text:` 会把空字符串当成 False，从而走 stdin 分支）。

**Step 3: Write minimal implementation**

在 `libs/platform_core/platform_core/cli.py`：
- 将判断从 `if args.text:` 改为 `if args.text is not None:`。

**Step 4: Run test to verify it passes**

Run: `pytest -q libs/platform_core/tests/test_cli.py -k mask_empty_string`

Expected: PASS

---

## Task 4: 回归验证

**Files:**
- (no code changes expected)

**Step 1: Run platform_core tests**

Run: `pytest -q libs/platform_core/tests`

Expected: PASS

**Step 2: Run repo tests (if configured)**

Run: `pytest -q`

Expected: PASS（若 `libs/user_auth/tests` 被收集，也应不出现 ImportError）。

