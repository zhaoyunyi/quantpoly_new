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

## 3. 运行基线与命令

- 当前前端框架：`TanStack Start`（React）
- 当前运行时基线：`Vite + @tanstack/react-start/plugin/vite`
- 当前包管理基线：`npm + package-lock.json`
- 开发启动：`cd apps/frontend_web && npm run dev`
- 生产构建：`cd apps/frontend_web && npm run build`
- 本地预览：先执行 `cd apps/frontend_web && npm run build`，再执行 `cd apps/frontend_web && npm run start`
- 关键浏览器回归：
  - `cd apps/frontend_web && npm run test:e2e -- tests/e2e/auth-dashboard.spec.ts`
  - `cd apps/frontend_web && npm run test:e2e -- tests/e2e/runtime-smoke.spec.ts`
- 本地 Compose 栈联调版 E2E：
  - `cd apps/frontend_web && PLAYWRIGHT_BACKEND_PORT=18000 npx playwright test --config playwright.compose.config.ts`
- 本地一键全栈验证：
  - `./.venv/bin/python scripts/verify_coolify_local_stack.py`

截至 `2026-04-18` 的当前验证状态：

- `npm run build` 已通过
- `npm test` 已通过
- 干净环境 `npm ci && npm run build` 已通过
- 本地 Compose 栈上的完整 Playwright E2E 已通过
- 一键脚本 `scripts/verify_coolify_local_stack.py` 已可执行完整“Compose + 健康检查 + Playwright + 清理”链路
- 审计与收敛记录见：`docs/migration/2026-04-18-doc-code-consistency-audit.md`

## 4. 设计系统与 Tokens

- 设计系统基座：`Base UI + Tailwind CSS v4`
- Design Tokens：`app/styles/app.css`（`@theme {}`）
- UI 规范入口：`spec/UISpec.md`

## 5. 边界说明

- 当前已落位的页面范围包括：
  - Landing
  - Auth（login/register/forgot-password/reset-password/verify-email/resend-verification）
  - Dashboard / Monitor
  - Strategies / Backtests / Trading / Settings
- 前端基础库继续保持“UI/ACL/App Shell”边界，不承载用户认证、会话签发与权限判定主逻辑。
- 现有后端入口 `apps/backend_app/` 与脚本命令保持不变。

## 6. 安全提示（开发阶段）

- `npm audit` 目前仍会提示上游依赖存在高危漏洞，需要单独治理后再考虑生产暴露。
- 在漏洞处理完成前，不建议将本前端构建产物用于生产环境对外提供服务。

## 7. 当前已知事项

- `npm run build` 当前仍会保留非阻断 warning：
  - client bundle `chunk size > 500 kB`
  - TanStack Start SSR build 的 unused imports warning
- 这些 warning 当前不影响构建成功；如需继续优化，应单独立项处理。
- `docs/migration/2026-04-18-doc-code-consistency-audit.md` 记录了本轮前端基线收敛过程。
