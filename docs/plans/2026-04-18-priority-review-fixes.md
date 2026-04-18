# Priority Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 按 review 优先级修复权限边界、前后端契约、前端导航/鉴权链路、日志脱敏与行情目录性能问题，并用回归测试锁住。

**Architecture:** 先修后端高风险边界与契约问题，再修前端共享导航与鉴权链路，最后补市场数据性能优化。每个修复都先写失败测试，再做最小实现，最后跑对应子集验证与全量回归。

**Tech Stack:** FastAPI, pytest, React 19, TanStack Router, Vitest, TypeScript

---

### Task 1: 锁住作业编排系统级接口的管理员权限

**Files:**
- Modify: `libs/job_orchestration/tests/test_api_domain_task_parity.py`
- Modify: `libs/job_orchestration/job_orchestration/api.py`

**Step 1: 写失败测试**
- 为 `/jobs/runtime`
- 为 `/jobs/system-schedules/templates`
- 为 `/jobs/system-schedules/templates/recover`
- 断言普通用户返回 `403/ADMIN_REQUIRED`，管理员仍可访问。

**Step 2: 运行失败测试**
- Run: `PYTHONPATH=libs/job_orchestration:libs/platform_core ./.venv/bin/pytest libs/job_orchestration/tests/test_api_domain_task_parity.py -q`

**Step 3: 最小实现**
- 在 `job_orchestration.api` 引入统一管理员判定。
- 对上述系统级接口增加权限校验。

**Step 4: 重新运行测试**
- 同上命令，确认通过。

### Task 2: 修复主题偏好前后端契约漂移

**Files:**
- Modify: `libs/user_preferences/tests/test_api.py`
- Modify: `libs/user_preferences/tests/test_domain.py`
- Modify: `libs/user_preferences/user_preferences/domain.py`
- Modify: `libs/frontend_api_client/src/endpoints.ts`
- Modify: `apps/frontend_web/tests/pages/settings/theme-preferences.test.tsx`
- Modify: `apps/frontend_web/app/widgets/settings/ThemePreferencesForm.tsx`

**Step 1: 写失败测试**
- 后端：`theme.mode` 可以被接受并与 `darkMode` 兼容。
- 前端：主题表单发出的 patch 与后端契约一致。

**Step 2: 运行失败测试**
- Run: `PYTHONPATH=libs/user_preferences:libs/platform_core ./.venv/bin/pytest libs/user_preferences/tests/test_api.py libs/user_preferences/tests/test_domain.py -q`
- Run: `cd apps/frontend_web && npm test -- tests/pages/settings/theme-preferences.test.tsx`

**Step 3: 最小实现**
- 在 `user_preferences.domain` 中补充 `mode` 持久化语义，并兼容旧 `darkMode`。
- 将前端 `UserPreferences` 收紧为显式接口。
- 调整主题表单读写逻辑。

**Step 4: 重新运行测试**
- 运行上述命令，确认通过。

### Task 3: 修复密码重置审计日志泄漏原始邮箱

**Files:**
- Modify: `libs/user_auth/tests/test_routes.py`
- Modify: `libs/user_auth/user_auth/app.py`

**Step 1: 写失败测试**
- 断言密码重置请求日志不包含原始邮箱，只保留 hash/domain。

**Step 2: 运行失败测试**
- Run: `PYTHONPATH=libs/user_auth:libs/platform_core ./.venv/bin/pytest libs/user_auth/tests/test_routes.py -q`

**Step 3: 最小实现**
- 对 password reset 审计沿用 resend verification 的脱敏策略。

**Step 4: 重新运行测试**
- 同上命令，确认通过。

### Task 4: 修复前端共享导航与鉴权副作用

**Files:**
- Modify: `apps/frontend_web/tests/app/entry-wiring.test.tsx`
- Modify: `apps/frontend_web/tests/shell/app-shell.test.tsx`
- Modify: `apps/frontend_web/tests/widgets/search/command-palette.test.tsx`
- Modify: `apps/frontend_web/app/entry_wiring.tsx`
- Modify: `apps/frontend_web/app/widgets/search/CommandPalette.tsx`
- Modify: `apps/frontend_web/app/widgets/landing/CtaLink.tsx`
- Modify: `apps/frontend_web/app/widgets/landing/LandingContent.tsx`
- Modify: `apps/frontend_web/app/routes/auth/*.tsx`
- Modify: `apps/frontend_web/app/routes/settings/theme.tsx`
- Modify: `libs/ui_app_shell/src/AppShell.tsx`
- Modify: `libs/ui_app_shell/src/AuthGuard.tsx`
- Modify: `libs/ui_app_shell/src/PublicLayout.tsx`

**Step 1: 写失败测试**
- 断言 `ProtectedLayout` 在未认证时不会启动通知轮询。
- 断言导航点击不触发整页跳转，使用客户端导航。

**Step 2: 运行失败测试**
- Run: `cd apps/frontend_web && npm test -- tests/app/entry-wiring.test.tsx tests/shell/app-shell.test.tsx tests/widgets/search/command-palette.test.tsx`

**Step 3: 最小实现**
- 用 TanStack Router 的 `Link/useNavigate` 替换共享导航层的原生跳转。
- 将 `AuthGuard` 的跳转移入 effect。
- 让通知轮询只在已认证后启用。

**Step 4: 重新运行测试**
- 同上命令，确认通过。

### Task 5: 优化行情目录详情与搜索实现

**Files:**
- Modify: `libs/market_data/tests/test_catalog_detail_filter_parity.py`
- Modify: `libs/market_data/tests/test_api_catalog_detail_filter_parity.py`
- Modify: `libs/market_data/market_data/service.py`
- Modify: `libs/market_data/market_data/alpaca_transport.py`
- Modify: `libs/market_data/market_data/alpaca_provider.py`

**Step 1: 写失败测试**
- 断言 `get_catalog_asset_detail()` 优先走 provider 详情接口，不扫描整表。
- 断言 Alpaca 资产目录搜索复用缓存。

**Step 2: 运行失败测试**
- Run: `PYTHONPATH=libs/market_data:libs/platform_core:libs/job_orchestration ./.venv/bin/pytest libs/market_data/tests/test_catalog_detail_filter_parity.py libs/market_data/tests/test_api_catalog_detail_filter_parity.py -q`

**Step 3: 最小实现**
- 在 transport/provider 增加资产详情直连与目录缓存。
- 在 service 中优先调用 provider 详情接口。

**Step 4: 重新运行测试**
- 同上命令，确认通过。

### Task 6: 全量验证

**Files:**
- Modify: `.omc/state/ralph-state.json`

**Step 1: 运行后端子集**
- Run: `./.venv/bin/pytest -q`

**Step 2: 运行前端验证**
- Run: `cd apps/frontend_web && npm test`
- Run: `cd apps/frontend_web && npm run build`

**Step 3: 运行规格验证**
- Run: `scripts/openspecw.sh validate --specs --strict`

**Step 4: 更新 Ralph 状态**
- 记录最终 iteration、checkpoint 与验证结果。
