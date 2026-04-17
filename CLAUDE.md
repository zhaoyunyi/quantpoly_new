# CLAUDE.md

本文件是 Claude Code / AI 编码助手在当前仓库的精简入口。公共背景与重复索引已抽到：

- `docs/guides/ai-collaboration.md`
- `docs/guides/ai-context-index.md`
- `docs/README.md`

## 必读顺序

1. `README.md`
2. `docs/guides/ai-collaboration.md`
3. `docs/guides/ai-context-index.md`
4. `openspec/AGENTS.md`（涉及计划 / 提案 / 规格 / 变更时）
5. 当前工作目录下的 `CLAUDE.md` 或 `AGENTS.md`
6. 实际代码与测试

## 协作约定

- 当前事实优先看 `README.md`、`docs/README.md`、`docs/migration/2026-02-13-backend-current-state.md`、`openspec/specs/`
- 开发中变更优先看 `openspec/changes/`
- 落地开发、浏览器测试、UI 与前端架构约束优先看 `spec/`
- 本仓库本地版本控制使用 `jj`
- 执行 OpenSpec CLI 时优先使用 `scripts/openspecw.sh`
- `docs/plans/` 默认是历史计划或工作草稿，不等于当前产品事实

## 目录入口

- `apps/backend_app/AGENTS.md`
- `apps/frontend_web/AGENTS.md`
- `deploy/AGENTS.md`
- `docs/frontend/AGENTS.md`
- `libs/frontend_api_client/AGENTS.md`
- `libs/ui_app_shell/AGENTS.md`
- `libs/ui_design_system/AGENTS.md`

## 重要直达索引

- 协作入口：`docs/guides/ai-collaboration.md`
- 上下文地图：`docs/guides/ai-context-index.md`
- OpenSpec：`openspec/AGENTS.md`
- 规范：`spec/ProgramSpec.md`、`spec/DDDSpec.md`、`spec/BDD_TestSpec.md`、`spec/BrowserTestStrategy.md`、`spec/UISpec.md`
- 后端组合入口：`apps/backend_app/AGENTS.md`
- 前端规范入口：`docs/frontend/AGENTS.md`、`apps/frontend_web/AGENTS.md`
- 部署入口：`deploy/AGENTS.md`
- 后端运行与门禁：`docs/runbooks/backend-operations-runbook.md`、`docs/gates/backend-gate-handbook.md`
- Skill 约定、多 Agent 约束与 `jj` 工作流：`AGENTS.md`
