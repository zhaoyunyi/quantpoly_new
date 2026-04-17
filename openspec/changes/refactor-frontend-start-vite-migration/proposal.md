# Change: 将前端运行时从旧版 Vinxi 链路迁移到新版 TanStack Start + Vite

## Why

`apps/frontend_web` 当前仍运行在旧版 TanStack Start + Vinxi 组合上，并依赖一组历史 overrides 才能维持可构建状态。该组合已经产生 `node:fs/node:path externalized for browser compatibility` 等构建 warning，说明当前运行时链路与上游推荐基线存在偏移，后续升级与排障成本会持续上升。

## What Changes

- 将 `apps/frontend_web` 的运行时基线从旧版 Vinxi 链路迁移到基于 TanStack Start 官方 Vite 集成的方案
- 对齐 `@tanstack/react-start`、`@tanstack/react-router` 及相关配套包的版本族，清理历史遗留 overrides
- 保持现有路由、认证接线、Landing、AppShell 与测试行为不变，只替换底层构建/运行时集成方式
- 为迁移前后的构建 warning 建立对比基线，避免将“warning 换了个名字”误判为问题消失
- 重新校验构建 warning：
  - 迁移后必须消除来自旧 Start runtime 的 `node:fs/node:path externalized for browser compatibility`
  - 若仍存在第三方 warning（例如 Base UI 的 `'use client'`），必须明确记录归因与后续处置
- 更新前端运行文档，说明迁移后的运行时基线与剩余已知 warning

## Impact

- Affected specs: `frontend-foundation`
- Affected code:
  - `apps/frontend_web/package.json`
  - `apps/frontend_web/package-lock.json`
  - `apps/frontend_web/app.config.ts`
  - `apps/frontend_web/app/client.tsx`
  - `apps/frontend_web/app/ssr.tsx`
  - `apps/frontend_web/vitest.config.ts`
  - `apps/frontend_web/playwright.config.ts`
  - `apps/frontend_web/AGENTS.md`
  - `docs/frontend/AGENTS.md`
  - 可能新增 `apps/frontend_web/vite.config.ts`
  - 可能更新其他前端运行文档与相关测试配置
