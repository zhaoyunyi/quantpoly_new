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
- 前端运行时已切换为 `Vite + @tanstack/react-start/plugin/vite`
- 前端子项目说明：`apps/frontend_web/AGENTS.md`
- 关键运行命令：
  - `cd apps/frontend_web && npm run dev`
  - `cd apps/frontend_web && npm run build`
  - `cd apps/frontend_web && npm run start`（依赖最新一次 `npm run build` 产物）
- 关键运行时回归命令：
  - `cd apps/frontend_web && npm test`
  - `cd apps/frontend_web && npm run test:e2e -- tests/e2e/auth-dashboard.spec.ts`
  - `cd apps/frontend_web && npm run test:e2e -- tests/e2e/runtime-smoke.spec.ts`

## 4. 当前已知限制

- 前端构建已消除旧 Vinxi runtime 的 `node:fs/node:path externalized for browser compatibility` warning。
- 仍保留少量非阻断 warning，主要是：
  - client bundle 体积告警
  - TanStack Start SSR build 的 unused imports
  - `tanstack-router` 对 route file named exports 的 code-splitting 提示
- 这些 warning 当前作为已知事项记录，不代表运行时错误；如需进一步优化，应单独立项而不是混入基础设施迁移。
