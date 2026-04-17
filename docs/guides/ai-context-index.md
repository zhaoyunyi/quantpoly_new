# AI 上下文索引

本文按“当前事实优先、操作手册次之、历史材料最后”的原则，为 AI 助手提供按领域查找上下文的入口。

## 1. 当前事实入口

优先用于判断“系统现在是什么样”：

- `README.md`
- `docs/README.md`
- `docs/migration/2026-02-13-backend-current-state.md`
- `openspec/specs/`
- `openspec/project.md`

## 2. 按领域查找

### 后端组合入口与运行

- `apps/backend_app/AGENTS.md`
- `apps/backend_app/`
- `apps/backend_app/cli.py`
- `scripts/run_backend_server.py`
- `scripts/smoke_backend_composition.py`
- `docs/runbooks/backend-operations-runbook.md`

### 前端应用与页面

- `apps/frontend_web/AGENTS.md`
- `apps/frontend_web/app/`
- `apps/frontend_web/tests/`
- `apps/frontend_web/playwright.config.ts`

### 前端基础库

- `libs/frontend_api_client/AGENTS.md`
- `libs/ui_app_shell/AGENTS.md`
- `libs/ui_design_system/AGENTS.md`

### 开发规范与测试策略

- `spec/ProgramSpec.md`
- `spec/DDDSpec.md`
- `spec/BDD_TestSpec.md`
- `spec/BrowserTestStrategy.md`
- `spec/UISpec.md`
- `spec/FrontendArchitectureSpec.md`
- `spec/DesignTokensSpec.md`

### 门禁、运行手册与部署

- `deploy/AGENTS.md`
- `docs/gates/backend-gate-handbook.md`
- `docs/gates/examples/capability_gate_input.json`
- `docs/runbooks/backend-operations-runbook.md`
- `docs/runbooks/fullstack-coolify-deployment-runbook.md`
- `deploy/`

### OpenSpec 与变更流程

- `openspec/AGENTS.md`
- `openspec/specs/`
- `openspec/changes/`

## 3. 文档类型判断

- 看当前实现事实：优先 `README.md`、`docs/README.md`、`docs/migration/`、`openspec/specs/`
- 看落地实现与测试约束：优先 `spec/`
- 看操作步骤、runbook、门禁与样例：优先 `docs/runbooks/`、`docs/gates/`
- 看正在开发中的方案与变更：优先 `openspec/changes/`
- 看历史计划草稿：看 `docs/plans/`

## 4. 目录协作入口

- 根目录：`AGENTS.md`、`CLAUDE.md`
- OpenSpec：`openspec/AGENTS.md`
- 后端组合入口：`apps/backend_app/AGENTS.md`、`apps/backend_app/CLAUDE.md`
- 前端：`apps/frontend_web/AGENTS.md`
- 前端文档：`docs/frontend/AGENTS.md`
- 前端基础库：`libs/frontend_api_client/AGENTS.md`、`libs/ui_app_shell/AGENTS.md`、`libs/ui_design_system/AGENTS.md`
- 部署：`deploy/AGENTS.md`、`deploy/CLAUDE.md`

完整文档治理入口见 `docs/README.md`。
