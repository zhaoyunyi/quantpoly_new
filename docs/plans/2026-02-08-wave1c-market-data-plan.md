# Wave 1-C 市场数据上下文迁移 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 落地 `add-market-data-context-migration` 的最小可用能力：`market_data` 库（统一接口 + Alpaca Provider 适配 + 缓存限流）与 API/CLI。

**Architecture:** 先建领域模型与 Provider 抽象，再实现 `MarketDataService`（显式 `user_id` + 缓存 + 限流 + 错误映射），最后提供 FastAPI Router 与 CLI，并用端到端测试验证错误语义与缓存命中元数据。

**Tech Stack:** Python、FastAPI、Pydantic v2、pytest。

---

### Task 1: 领域与 Provider 红测

**Files:**
- Create: `libs/market_data/tests/test_domain.py`

**Step 1: Write failing tests**
- Provider 超时映射为可识别错误码（重试后失败）
- 同 symbol 重复 quote 命中缓存，返回 `cacheHit`
- 高频调用触发限流错误码

**Step 2: Run red tests**
- Run: `pytest -q libs/market_data/tests/test_domain.py`
- Expected: FAIL

**Step 3: Minimal implementation**
- `domain.py`：Asset/Quote/Candle 与错误模型
- `provider.py` + `alpaca_provider.py`：统一接口 + 超时重试/错误映射
- `cache.py` / `rate_limit.py`
- `service.py`

**Step 4: Run green tests**
- Run: `pytest -q libs/market_data/tests/test_domain.py`

---

### Task 2: API 红测与实现

**Files:**
- Create: `libs/market_data/tests/test_api.py`
- Create: `libs/market_data/market_data/api.py`

**Step 1: Write failing tests**
- `GET /market/quote/{symbol}` 二次请求返回 `metadata.cacheHit=true`
- Provider 超时返回标准错误 envelope 与错误码
- 触发限流返回标准错误 envelope 与错误码

**Step 2: Run red tests**
- Run: `pytest -q libs/market_data/tests/test_api.py`

**Step 3: Minimal implementation**
- 路由：`search/quote/history`
- 统一 `platform_core.response.success_response/error_response`
- 错误映射：`UPSTREAM_TIMEOUT`、`RATE_LIMIT_EXCEEDED`

**Step 4: Run green tests**
- Run: `pytest -q libs/market_data/tests/test_api.py`

---

### Task 3: CLI 红测与实现

**Files:**
- Create: `libs/market_data/tests/test_cli.py`
- Create: `libs/market_data/market_data/cli.py`

**Step 1: Write failing tests**
- `search --user-id --keyword` 输出搜索结果 JSON
- `quote --user-id --symbol` 输出行情及 `cacheHit`
- `history --user-id --symbol --start-date --end-date` 输出 K 线列表

**Step 2: Run red tests**
- Run: `pytest -q libs/market_data/tests/test_cli.py`

**Step 3: Minimal implementation**
- CLI 子命令：`search` / `quote` / `history`

**Step 4: Run green tests**
- Run: `pytest -q libs/market_data/tests/test_cli.py`

---

### Task 4: 集成验证与 OpenSpec 同步

**Files:**
- Modify: `conftest.py`
- Modify: `openspec/changes/add-market-data-context-migration/tasks.md`

**Step 1: Add lib path**
- 在根 `conftest.py` 注入 `market_data`

**Step 2: Focused tests**
- Run: `pytest -q libs/market_data/tests`

**Step 3: Full verification**
- Run: `pytest -q`
- Run: `openspec validate add-market-data-context-migration --strict`
- Run: `openspec validate --changes --strict`

