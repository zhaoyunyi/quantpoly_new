# 前端建设文档入口（docs/frontend）

## 1. 核心规范

- `spec/UISpec.md`
- `spec/FrontendArchitectureSpec.md`
- `spec/DesignTokensSpec.md`
- `spec/BrowserTestStrategy.md`

## 2. 设计与实现原则

- 遵循 `spec/ProgramSpec.md`：Library-First、CLI Mandate、Test-First
- 遵循 `spec/DDDSpec.md`：限界上下文与通用语言一致
- 浏览器测试选型与边界遵循 `spec/BrowserTestStrategy.md`
- 前端仅作为后端能力的 UI 与交互层，不承载用户系统主逻辑

## 3. 当前实现状态

- 前端应用框架已落位为 `TanStack Start`（目录：`apps/frontend_web/`）
- 前端当前运行时基线为 `Vite + @tanstack/react-start/plugin/vite`
- 前端当前包管理基线为 `npm + package-lock.json`
- 前端子项目说明：`apps/frontend_web/AGENTS.md`
- 当前已实现的页面范围包括 Landing、Auth、Dashboard、Monitor、Strategies、Backtests、Trading、Settings
- 关键运行命令：
  - `cd apps/frontend_web && npm run dev`
  - `cd apps/frontend_web && npm run build`
  - `cd apps/frontend_web && npm run start`（依赖最新一次 `npm run build` 产物）
- 关键运行时回归命令：
  - `cd apps/frontend_web && npm test`
  - `cd apps/frontend_web && npm run test:e2e -- tests/e2e/auth-dashboard.spec.ts`
  - `cd apps/frontend_web && npm run test:e2e -- tests/e2e/runtime-smoke.spec.ts`

## 4. 当前已知限制

- 截至 `2026-04-18`，前端构建与测试基线已恢复：
  - `npm test` 通过
  - `npm run build` 通过
  - 干净环境 `npm ci && npm run build` 通过
- 当前保留的已知事项主要是构建 warning，而非阻断错误：
  - client bundle 体积告警
  - TanStack Start SSR build 的 unused imports warning
- 本轮收敛记录见：`docs/migration/2026-04-18-doc-code-consistency-audit.md`
