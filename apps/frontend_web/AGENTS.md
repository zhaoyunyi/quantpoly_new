# 前端应用（frontend_web）

## 1. 目标

本目录用于承载 QuantPoly 前端应用（Web）。

- 前端仅负责 UI 呈现、交互编排、调用后端 API。
- 用户认证、会话签发、权限判断等能力继续由后端负责。

## 2. 目录约定

- `app/`：TanStack Start 路由与页面源码
- `tests/`：前端测试目录（按需扩展）
- `vite.config.ts`：TanStack Start 官方 Vite 集成配置
- `testing/`：测试运行时与浏览器测试辅助工具
- `package.json`：前端依赖与脚本

## 3. 框架与命令

- 当前前端框架：`TanStack Start`（React）
- 当前运行时基线：`Vite + @tanstack/react-start/plugin/vite`
- 开发启动：`cd apps/frontend_web && npm run dev`
- 生产构建：`cd apps/frontend_web && npm run build`
- 本地预览：先执行 `cd apps/frontend_web && npm run build`，再执行 `cd apps/frontend_web && npm run start`
- 关键浏览器回归：
  - `cd apps/frontend_web && npm run test:e2e -- tests/e2e/auth-dashboard.spec.ts`
  - `cd apps/frontend_web && npm run test:e2e -- tests/e2e/runtime-smoke.spec.ts`

## 4. 设计系统与 Tokens

- 设计系统基座：`Base UI + Tailwind CSS v4`
- Design Tokens：`app/styles/app.css`（`@theme {}`）
- UI 规范入口：`spec/UISpec.md`

## 5. 边界说明

- 当前仅保留前端规范与 Design Tokens 基线，业务 UI 暂未实现。
- 现有后端入口 `apps/backend_app/` 与脚本命令保持不变。

## 6. 安全提示（开发阶段）

- `npm audit` 目前仍会提示上游依赖存在高危漏洞，需要单独治理后再考虑生产暴露。
- 在漏洞处理完成前，不建议将本前端构建产物用于生产环境对外提供服务。

## 7. 已知 Warning（迁移后）

- `npm run build` 已不再出现 `node:fs/node:path externalized for browser compatibility`。
- 当前保留的非阻断 warning：
  - client bundle `chunk size > 500 kB`：属于体积优化问题，不影响运行时正确性。
  - SSR build 中 `@tanstack/start-*` 的 unused imports：属于上游构建输出 warning，当前接受。
  - dev / Playwright 启动时的 `tanstack-router` route-file named export code-splitting warning：提示可进一步拆分页面导出，当前不阻断迁移。
