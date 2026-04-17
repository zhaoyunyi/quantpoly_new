# Frontend Start Vite Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 `apps/frontend_web` 从旧版 Vinxi 运行链迁移到基于 TanStack Start 官方 Vite 集成的运行时基线，同时保持现有页面行为、测试入口与构建门禁稳定。

**Architecture:** 本次变更只触达前端基础设施层，不改业务页面结构与视觉风格。迁移以 TDD 驱动：先增加运行时配置回归测试，再替换脚本、依赖、client/server entry 和配置文件；最后用 BDD 页面测试与 Playwright E2E 回归来证明行为不变，并记录迁移前后 warning 差异。

**Tech Stack:** Jujutsu (`jj`), TanStack Start, Vite, React 19, Tailwind CSS v4, Vitest, Testing Library, Playwright

---

### Task 1: 建立迁移护栏测试与 warning 基线

**Files:**
- Create: `apps/frontend_web/tests/app/runtime-toolchain.test.ts`
- Modify: `apps/frontend_web/package.json`
- Modify: `apps/frontend_web/app/client.tsx`
- Modify: `apps/frontend_web/app/ssr.tsx`
- Modify: `docs/plans/2026-04-18-frontend-start-vite-migration.md`

**Step 1: 写失败测试，锁定运行时迁移目标**

在 `apps/frontend_web/tests/app/runtime-toolchain.test.ts` 中添加以下断言：

- `package.json` 的 `dev/build/start` 脚本不再包含 `vinxi`
- `dependencies` 不再直接依赖 `vinxi`
- `overrides` 不再保留旧 `@tanstack/start-client-core` / `@tanstack/start-server-core` / `@tanstack/react-start-plugin` / `@tanstack/server-functions-plugin`
- `app/client.tsx` 与 `app/ssr.tsx` 不再引用 `vinxi/types/*`

**Step 2: 运行测试，确认当前为红灯**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm test -- tests/app/runtime-toolchain.test.ts
```

Expected:
- FAIL，失败原因应明确指向当前脚本/依赖/入口仍绑定 Vinxi

**Step 3: 记录当前 build warning 基线**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm run build | tee /tmp/quantpoly-start-build-before.log
```

Expected:
- build 成功
- 输出包含当前已知 `node:fs/node:path externalized for browser compatibility`
- 若存在 `'use client' was ignored`，一并记录

**Step 4: 用文档记下 warning 分类**

将 `/tmp/quantpoly-start-build-before.log` 的 warning 手工归类为：

- Start runtime warning
- 第三方库 warning

记录到本计划末尾的执行备注区域。

**Step 5: 形成独立变更**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration
jj describe -m "test(frontend): lock runtime migration guardrails"
jj new
```

### Task 2: 迁移运行时脚本、依赖与入口

**Files:**
- Modify: `apps/frontend_web/package.json`
- Modify: `apps/frontend_web/package-lock.json`
- Modify: `apps/frontend_web/app.config.ts`
- Modify: `apps/frontend_web/app/client.tsx`
- Modify: `apps/frontend_web/app/ssr.tsx`
- Create or Modify: `apps/frontend_web/vite.config.ts`
- Test: `apps/frontend_web/tests/app/runtime-toolchain.test.ts`

**Step 1: 仅实现让运行时护栏测试通过所需的最小变更**

实现内容限于：

- 将 `dev/build/start` 脚本替换为新版 TanStack Start + Vite 推荐链路
- 移除 `vinxi` 直接依赖与过时 overrides
- 按目标版本族调整 `@tanstack/react-start` / `@tanstack/react-router`
- 根据新版入口要求更新 `app/client.tsx` / `app/ssr.tsx`
- 必要时新增 `vite.config.ts`

**Step 2: 刷新锁文件**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm install
```

Expected:
- `package-lock.json` 刷新成功
- 无未解析依赖错误

**Step 3: 运行护栏测试，确认转绿**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm test -- tests/app/runtime-toolchain.test.ts
```

Expected:
- PASS

**Step 4: 提交该运行时迁移骨架**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration
jj describe -m "refactor(frontend): migrate start runtime to vite"
jj new
```

### Task 3: 修复并验证测试基建与 BDD 页面行为

**Files:**
- Modify: `apps/frontend_web/vitest.config.ts`
- Modify: `apps/frontend_web/playwright.config.ts`
- Modify: `apps/frontend_web/tests/app/entry-wiring.test.tsx`
- Modify: `apps/frontend_web/tests/pages/landing/landing.test.tsx`
- Modify: `apps/frontend_web/tests/pages/auth/login.test.tsx`
- Modify: `apps/frontend_web/tests/pages/dashboard/dashboard.test.tsx`
- Create or Modify: `apps/frontend_web/tests/e2e/runtime-smoke.spec.ts`

**Step 1: 先写/补失败测试，锁定用户行为不回退**

BDD 级测试至少覆盖：

- landing 可正常渲染 CTA 与健康状态
- 登录成功后仍可进入 dashboard
- 受保护路由仍通过 AuthGuard 重定向

E2E 至少覆盖：

- `/` 打开成功
- `/auth/login` 登录成功进入 `/dashboard`

如现有用例已覆盖相同行为，应优先复用并最小修改，不新增重复场景。

**Step 2: 运行相关测试，确认在迁移后暴露真实失败**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm test -- tests/app/entry-wiring.test.tsx tests/pages/landing/landing.test.tsx tests/pages/auth/login.test.tsx tests/pages/dashboard/dashboard.test.tsx
```

Expected:
- 若迁移破坏测试入口、模块解析或路由挂载，此处应红灯

**Step 3: 最小修复测试基建**

只修与新 runtime 链路相关的问题：

- alias / fs allow / jsx 配置
- Playwright 启动命令与端口
- 入口挂载方式变化导致的测试初始化差异

**Step 4: 运行 BDD 测试转绿**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm test -- tests/app/entry-wiring.test.tsx tests/pages/landing/landing.test.tsx tests/pages/auth/login.test.tsx tests/pages/dashboard/dashboard.test.tsx
```

Expected:
- PASS

**Step 5: 运行关键 E2E**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm run test:e2e -- tests/e2e/auth-dashboard.spec.ts
```

Expected:
- PASS

**Step 6: 提交测试基建修复**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration
jj describe -m "test(frontend): restore bdd and e2e runtime regression coverage"
jj new
```

### Task 4: 完整验证 warning 收口与文档更新

**Files:**
- Modify: `apps/frontend_web/AGENTS.md`
- Modify: `docs/frontend/AGENTS.md`
- Modify: `openspec/changes/refactor-frontend-start-vite-migration/tasks.md`
- Optional: `docs/plans/2026-04-18-frontend-start-vite-migration.md`

**Step 1: 运行完整前端单测**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm test
```

Expected:
- PASS

**Step 2: 运行生产构建并保存迁移后日志**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm run build | tee /tmp/quantpoly-start-build-after.log
```

Expected:
- PASS
- 不再出现 `node:fs` / `node:path externalized for browser compatibility`

**Step 3: 对比 warning**

对比：

- `/tmp/quantpoly-start-build-before.log`
- `/tmp/quantpoly-start-build-after.log`

结论必须写入文档：

- 哪些 warning 已消失
- 哪些 warning 仍保留
- 每条剩余 warning 是接受现状还是另起提案处理

**Step 4: 更新前端运行文档**

将迁移后的运行时基线与已知限制写入：

- `apps/frontend_web/AGENTS.md`
- `docs/frontend/AGENTS.md`

**Step 5: 最终提交**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration
jj describe -m "docs(frontend): document vite runtime baseline and warning audit"
jj new
```

### Task 5: 最终验收

**Files:**
- No code changes expected

**Step 1: 运行最终验收命令**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration/apps/frontend_web
npm test
npm run test:e2e -- tests/e2e/auth-dashboard.spec.ts
npm run build
```

Expected:
- 全部 PASS

**Step 2: 更新 OpenSpec 任务勾选**

将以下文件中的任务更新为完成：

- `openspec/changes/refactor-frontend-start-vite-migration/tasks.md`

**Step 3: 记录 jj 状态**

Run:

```bash
cd /Users/zhaoyunyi/developer/quantpoly-jj-vite-migration
jj status
jj log -r 'master | @' --no-graph -T 'change_id.short() ++ \" \" ++ description.first_line() ++ \"\\n\"'
```

Expected:
- 工作区状态清晰
- 当前 change 描述明确

## 执行备注

- 当前远端 `jj git fetch` 因仓库访问权限失败，本次实现基线为本地 `master`：`wyqlouzn`
- 若后续可恢复远端读取权限，实施前应再做一次 `jj git fetch` 复核基线
