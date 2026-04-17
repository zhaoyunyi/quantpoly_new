# 文档与代码一致性审计与收敛记录（2026-04-18）

## 1. 审计范围

本次审计基于以下事实入口与实现层进行交叉核对：

- 根级与目录级说明：`README.md`、`docs/README.md`、各子目录 `AGENTS.md`
- 当前事实文档与运行手册：`docs/migration/`、`docs/runbooks/`
- OpenSpec 当前规格：`openspec/specs/`
- 实际代码与验证命令：`apps/`、`libs/`、`tests/`

## 2. 审计结论

本次审计最初发现两类问题：

1. 纯文档漂移：说明文档仍保留旧结论，已经与当前代码事实不一致。这类已直接修正。
2. 合理设计但实现未收敛：规格与目标方向合理，但代码、依赖或测试基线尚未闭环。这类不回退规格，而是记录为待收敛冲突。

截至本记录收尾时：

- 纯文档漂移已修正
- 前端构建、测试与 npm 锁文件基线已收敛
- 本文保留为“审计过程 + 收敛结果”记录，便于后续追踪

## 3. 已直接修正的文档漂移

### 3.1 根 README 完全失真

- 原 `README.md` 实际是一份 `git cnd` 本地 alias 说明，和当前项目无关。
- 已改为 QuantPoly 仓库总览，并补入前端当前审计结论入口。

### 3.2 文档入口误称“历史计划稿已移除”

- `docs/README.md` 原文称“历史计划稿/盘点稿已移除”，但仓库仍保留 `docs/plans/`。
- 已改为：`docs/plans/` 仍保留，但不作为当前实现事实依据。

### 3.3 前端目录说明停留在“只有基线、没有业务 UI”

- `apps/frontend_web/AGENTS.md` 原文写明“业务 UI 暂未实现”。
- 实际代码已存在 Landing、Auth、Dashboard、Monitor、Strategies、Backtests、Trading、Settings 等路由与 widget。
- 已修正文档，明确当前页面覆盖与当前阻断项分离描述。

### 3.4 OpenSpec 项目约定仍要求 `git cnd`

- `openspec/project.md` 的 Git Workflow 仍写“必须使用 `git cnd` 提交”。
- 仓库当前明确使用 `jj`，且根 `AGENTS.md` 已声明。
- 已修正为 `jj` 工作流说明，并补充仓库已包含前端与部署资产。

## 4. 初始冲突点与收敛结果

### 4.1 前端运行时迁移目标合理，但构建基线曾未闭环

**相关文档 / 规格**

- `apps/frontend_web/AGENTS.md`
- `docs/frontend/AGENTS.md`
- `openspec/specs/frontend-foundation/spec.md`
- `docs/runbooks/fullstack-coolify-deployment-runbook.md`

**承诺**

- 前端运行时已切到 `Vite + @tanstack/react-start/plugin/vite`
- `npm run build` 可作为当前构建基线
- 全栈部署手册可直接用于前端镜像构建与部署

**当前证据**

- `2026-04-18` 执行 `cd apps/frontend_web && npm run build`，命令退出码为 `1`
- 报错为 `Missing "./plugin/vite" specifier in "@tanstack/react-start" package`
- 报错源头来自 `apps/frontend_web/vite.config.ts` 中：
  - `import { tanstackStart } from '@tanstack/react-start/plugin/vite'`
- 前端镜像构建同样依赖该命令：
  - `docker/frontend.prod.Dockerfile` 中执行 `RUN cd apps/frontend_web && npm run build`
- 锁文件状态也未收敛：
  - `apps/frontend_web/package.json` 声明 `@tanstack/react-start=1.167.41`、`@tanstack/react-router=1.168.22`、`vite=^7.1.12`
  - `apps/frontend_web/pnpm-lock.yaml` 仍混有 `@tanstack/react-start@1.117.2`、`vite@6.4.2`、`vinxi@0.5.3`

**初始判定**

- 这是合理的迁移方向，不应通过回退规格来掩盖问题。
- 当前问题属于依赖族与锁文件未完全收敛，导致“文档已宣告迁移完成，但实现并未形成稳定构建基线”。

**收敛结果**

- 已移除 `apps/frontend_web/pnpm-lock.yaml`
- 已补齐并重写 `apps/frontend_web/package-lock.json`
- 主工作区 `cd apps/frontend_web && npm run build` 已通过
- 干净目录 `npm ci && npm run build` 已通过

### 4.2 前端自动化测试门禁方向合理，但测试基线曾不成立

**相关文档 / 规格**

- `docs/frontend/AGENTS.md`
- `openspec/specs/frontend-testing-harness/spec.md`
- `apps/frontend_web/AGENTS.md`

**承诺**

- `npm test` / E2E 可作为关键回归门禁
- Vitest + Testing Library 覆盖关键用户旅程

**当前证据**

- `2026-04-18` 执行 `cd apps/frontend_web && npm test`，结果为：
  - `12` 个失败文件
  - `38` 个失败测试
- 主要失败来源：
  - `libs/ui_design_system/src/ThemeProvider.tsx` 直接依赖 `window.matchMedia`
  - `apps/frontend_web/tests/setup.ts` 仅引入 `@testing-library/jest-dom/vitest`，未提供 `matchMedia` mock
  - 多个页面测试最终落到统一错误边界，错误文案为 `window.matchMedia is not a function`
  - `apps/frontend_web/tests/pages/settings/theme-preferences.test.tsx` 直接渲染 `ThemePreferencesForm`，但组件内部调用 `useTheme`，测试未包裹 `ThemeProvider`
- 仓库内还保留一组已明显落后于当前前端基线的 Python 测试：
  - `tests/frontend/test_tanstack_start_scaffold.py`
  - 该测试仍断言旧版 `@tanstack/react-start` 版本和 `app/client.tsx` Vinxi client handler
  - 实测执行 `./.venv/bin/pytest tests/frontend/test_tanstack_start_scaffold.py -q` 结果为 `2 failed, 1 passed`

**初始判定**

- 规格“需要自动化回归门禁”是合理的。
- 当前问题不是规格错误，而是测试运行环境、测试封装与旧迁移护栏测试尚未同步完成。

**收敛结果**

- 已将 `tests/frontend/test_tanstack_start_scaffold.py` 改为当前 npm + Vite 基线护栏
- 已为 `ThemeProvider` 增加缺失 `matchMedia` 时的稳健降级
- 已修正 `ThemePreferencesForm` 测试，使其按真实使用方式包裹 `ThemeProvider`
- `cd apps/frontend_web && npm test` 已通过
- `./.venv/bin/pytest tests/frontend -q` 已通过

### 4.3 全栈 Coolify 部署资产已存在，但当时不应被描述为已验证可用路径

**相关文档 / 规格**

- `deploy/AGENTS.md`
- `docs/runbooks/fullstack-coolify-deployment-runbook.md`
- `deploy/coolify/docker-compose.fullstack.yml`

**承诺**

- 全栈 Coolify 部署手册可作为当前部署事实入口
- 前端、后端、Postgres 三服务可按当前模板直接部署验证

**当前证据**

- 前端服务镜像构建依赖 `docker/frontend.prod.Dockerfile`
- 该 Dockerfile 在构建阶段执行 `npm run build`
- 当前本地构建已被 4.1 中的运行时问题阻断，因此前端镜像链路未通过当前仓库状态验证

**初始判定**

- 部署模板与运行手册本身是合理设计，应保留。
- 但它们不能继续被描述为“当前已验证事实”，只能表述为“目标部署资产已存在，待前端构建基线收敛后恢复验证”。

**收敛结果**

- 前端 npm 构建链路已恢复，可再次作为部署前置检查
- `docker build -f docker/frontend.prod.Dockerfile ...` 已通过
- `docker build -f docker/backend.prod.Dockerfile ...` 已通过
- 本地 `docker compose -p quantpoly_local_verify -f docker-compose.coolify.yml up -d --build` 已通过
- 新增 `docker-compose.coolify.local.yml` 用于本地浏览器级部署验证
- 新增 `scripts/verify_coolify_local_stack.py` 作为一键验证入口
- 本地 Compose 栈内 `postgres`、`backend`、`frontend` 均达到 `healthy`
- 栈内验证已通过：
  - `backend /health`
  - `frontend /`
  - 后端冒烟脚本
  - `WS /ws/monitor` 实连心跳
- 本地浏览器级验证已通过：
  - `http://localhost:13000/auth/login` 登录成功跳转 `/dashboard`
  - 浏览器内已拿到 `session_token` cookie
  - `sessionCookieSecure=false`、`SameSite=Lax` 与本地 override 预期一致
- 本地 Compose 栈上的完整 Playwright E2E 已通过（`19 passed`）
- 一键脚本实跑已通过，输出包含 health / HTTP 检查 / E2E / cleanup 结果
- 运行手册与部署目录说明已同步更新为当前事实

## 5. 当前后续建议

按优先级建议如下：

1. 如果继续优化前端基础设施，优先处理 `npm run build` 中仍保留的非阻断 warning。
2. 如需进一步提高部署可信度，可补一次带端口映射的本地浏览器级验证，确认前端登录后对后端 API 与 Cookie 会话的实际交互。
3. 后续如再次切换包管理器或运行时基线，应同步更新锁文件、测试护栏与目录说明，避免重回“迁移中间态”。
